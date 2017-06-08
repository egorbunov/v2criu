#! /usr/bin/env python2
from __future__ import print_function

import argparse
import json
import sys

from abstractir.resource_concepts import *
from model import loader
from model.crdata import Application

PROGRAM_NAME = "criugen.py"


def main(args):
    cmd_parser, child_parsers_dict = build_parsers()

    cmd_args = cmd_parser.parse_args(args[0:1])

    if cmd_args.command not in child_parsers_dict.keys():
        exit_error("Unknown command: {}".format(cmd_args.command), print_help_parser=cmd_parser)

    # parsing specific for command arguments
    cmd_parser, processor_callback = child_parsers_dict[cmd_args.command]
    args = cmd_parser.parse_args(args[1:])

    # each command has obligatory argument
    dump_dir = args.dump_dir
    is_json_img = args.json_img

    # loading application, which is needed by every command
    if is_json_img:
        application = loader.load_from_jsons(dump_dir)
    else:
        application = loader.load_from_imgs(dump_dir)

    # invoking command-special processor
    processor_callback(application, args, cmd_parser)


def build_parsers():
    generate_program_command = "program"
    generate_actions_command = "actions-ir"
    generate_graph_command = "actions-graph"
    pstree_graph_command = "pstree"

    command_parser = argparse.ArgumentParser(description='', formatter_class=argparse.RawTextHelpFormatter)
    command_parser.add_argument('command', default=generate_program_command,
                                help="Command to execute, possible values are: \n"
                                     "    * program (default) -- generate final restorer program\n"
                                     "    * actions-ir -- generate list of abstract intermediate actions\n"
                                     "    * actions-graph -- render IR actions graph\n"
                                     "    * pstree -- render process tree graph\n"
                                     "\n"
                                     "You can see help for each of any command:\n"
                                     "    ./criugen.py <command> -h")

    # common parser
    root_parser = argparse.ArgumentParser(description='Process tree restoration program generator',
                                          add_help=False)
    root_parser.add_argument('-d', '--dump_dir', help="Path to process dump images directory",
                             required=True)
    root_parser.add_argument('--json_img', help="If set, then program parses process dump as json files",
                             default=False, action='store_true')

    # program command parser
    gen_program_cmd_parse = argparse.ArgumentParser(prog="{} {}".format(PROGRAM_NAME, generate_program_command),
                                                    description='Generates final program for restorer-interpreter',
                                                    parents=[root_parser])
    gen_program_cmd_parse.add_argument('-o', '--output_file', help="Output json file with commands, "
                                                                   "if not specified program will be "
                                                                   "printed to stdout")

    # actions program command parser (for now it is the same as program command parser)
    actions_cmd_parser = argparse.ArgumentParser(prog="{} {}".format(PROGRAM_NAME, generate_actions_command),
                                                 description='Generates intermediate program representation '
                                                             '-- list of abstract actions',
                                                 parents=[root_parser])
    actions_cmd_parser.add_argument('-o', '--output_file', help="Output json file with actions, "
                                                                "if not specified actions are printed to stdout")

    # common visualization parser
    common_vis_parser = argparse.ArgumentParser(add_help=False)
    common_vis_parser.add_argument('-o', '--output_file', help="Output graph drawing file path; if not specified,\n"
                                                               "graph will be saved in the current dir and showed\n"
                                                               "immediately (like when --show option is specified)"
                                   ,
                                   default=None)
    common_vis_parser.add_argument('--show', help="Show graph immediately",
                                   default=False, action='store_true')
    common_vis_parser.add_argument('--type', help="Output type of the graph render. Possible types are:\n"
                                                  "    * pdf (default)\n"
                                                  "    * svg\n"
                                                  "    * png\n"
                                                  "    * gv",
                                   default='pdf')
    common_vis_parser.add_argument('--layout', help="Set graphviz ordering layout. Possible values are:\n"
                                                    "    * LR -- from left to right\n"
                                                    "    * TB -- from top to bottom (default)",
                                   default='TB')
    common_vis_parser.add_argument('--skip', metavar='TO_SKIP', type=str, nargs='+', default=(),
                                   help="List of resources name, which should NOT BE rendered\n"
                                        "to the graph image; that helps sometimes to make graph visualization\n"
                                        "much more clearer for your particular need to look at some\n"
                                        "specific resources; Possible values are:\n"
                                        "    * vmas -- skip actions with Virtual Memory Areas\n"
                                        "    * regfiles -- ... with Regular Files\n"
                                        "    * pipes -- ... with Pipes\n"
                                        "    * groups -- ... with Groups\n"
                                        "    * sessions -- ... with Sessions\n"
                                        "    * private -- ... with all private (non-shared at all) resources\n"
                                        "    * shmem -- ... with Shared Memory\n"
                                   )
    common_vis_parser.add_argument('--keep', metavar='TO_KEEP_RESOURCE', type=str, nargs='+',
                                   default=get_all_resources_type_names(),
                                   help="List of resource names, which should BE rendered\n"
                                        "to the graph image; see '--skip' option for the list of\n"
                                        "possible resources to skip/keep. This list is intersected\n"
                                        "with '--skip' list to form the final resource list to be shown.\n"
                                        "If not specified all resources are kept."
                                   )

    # visualization command parser
    graph_command_parser = argparse.ArgumentParser(prog="{} {}".format(PROGRAM_NAME, generate_graph_command),
                                                   description='Actions graph visualization command',
                                                   parents=[root_parser, common_vis_parser],
                                                   formatter_class=argparse.RawTextHelpFormatter)
    graph_command_parser.add_argument('--cluster', help="If set, then actions are clustered by executing process",
                                      default=False, action='store_true')
    graph_command_parser.add_argument('--sorted', help="If set, then actual actions list is drawn, as it would\n"
                                                       "be executed by abstract process-restore machine =)",
                                      default=False, action='store_true')
    graph_command_parser.add_argument('--show_cycle',
                                      help="If set, then in case --sorted option specified and graph is not\n"
                                           "acyclic, cycle is shown as drawing\n",
                                      default=False, action='store_true')

    # process tree visualization parser
    pstreevis_command_parser = argparse.ArgumentParser(prog="{} {}".format(PROGRAM_NAME, pstree_graph_command),
                                                       description='Process tree visualization command',
                                                       parents=[root_parser, common_vis_parser],
                                                       formatter_class=argparse.RawTextHelpFormatter)
    pstreevis_command_parser.add_argument('--notmp', help="If set, then no temporary resource will be shown\n"
                                                          "on the process tree graph",
                                          default=False, action='store_true')

    return command_parser, {generate_program_command: (gen_program_cmd_parse, generate_final_commands),
                            generate_actions_command: (actions_cmd_parser, generate_intermediate_actions),
                            generate_graph_command: (graph_command_parser, generate_actions_graph),
                            pstree_graph_command: (pstreevis_command_parser, generate_pstree_graph)}


def get_all_resources_type_dict():
    return {
        'vmas': VMAConcept,
        'pipes': PipeConcept,
        'sessions': ProcessSessionConcept,
        'groups': ProcessGroupConcept,
        'regfiles': RegularFileConcept,
        'shmem': SharedMemConcept,
        'private': ProcessInternalsConcept
    }


def get_all_resources_type_names():
    return tuple(get_all_resources_type_dict().keys())


def get_resources_types_to_skip(skipped_type_names, keep_type_names):
    from itertools import chain

    all_type_names = set(get_all_resources_type_names())

    for t in chain(skipped_type_names, keep_type_names):
        if t not in all_type_names:
            raise RuntimeError("Unknown resource type: {}".format(t))

    name_to_type = get_all_resources_type_dict()
    skip = set(skipped_type_names)
    keep = set(keep_type_names)

    return tuple(name_to_type[n] for n in (all_type_names - (keep - skip)))


def exit_error(message, print_help_parser=None):
    print("ERROR: {}".format(message))
    print("")
    if print_help_parser is not None:
        print(print_help_parser.format_help())
    exit(1)


def generate_final_commands(application, args, parser):
    """
    :type application: Application
    """

    from generator import gen
    program = gen.generate_program(application)

    json_out_file = args.output_file
    if json_out_file is None:
        print(json.dumps(program, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        with open(json_out_file, 'w') as f:
            json.dump(program, f, indent=4, sort_keys=True)

    raise RuntimeError("This feature is coming soon ;)")


def generate_intermediate_actions(application, args, parser):
    """
    :type application: Application
    """
    from abstractir import actions_program
    acts = actions_program.generate_actions_list(application)

    json_out_file = args.output_file
    if json_out_file is None:
        print(acts)
    else:
        with open(json_out_file, 'w') as f:
            f.write(str(acts))

    raise RuntimeError("This feature is coming soon ;)")


def generate_actions_graph(application, args, parser):
    """
    :type application: Application
    """
    from abstractir.concept import build_concept_process_tree
    from abstractir.actgraph_build import build_actions_graph
    from abstractir.actgraph_sort import sort_actions_graph
    from pyutils.graph import GraphIsNotAcyclic
    import visualize.core as viz

    process_tree = build_concept_process_tree(application)

    resource_types_to_skip = get_resources_types_to_skip(args.skip, args.keep)

    if args.type not in ['svg', 'pdf', 'png', 'gv']:
        exit_error("unknown output image type: {}".format(args.type), parser)

    graph = build_actions_graph(process_tree, tuple(resource_types_to_skip))

    if not args.sorted:
        # just drawing graph
        viz.render_actions_graph(graph, args.output_file, output_type=args.type, view=args.show,
                                 layout=args.layout, do_cluster=args.cluster)
    else:
        # trying to sort the graph and draw list of actions
        try:
            sorted_actions = sort_actions_graph(graph)
            viz.render_actions_list(sorted_actions, args.output_file,
                                    type=args.type, view=args.show,
                                    layout=args.layout)

        except GraphIsNotAcyclic as e:
            print("ERROR: actions graph is not acyclic: {}".format(e.cycle), file=sys.stderr)

            if not args.show_cycle:
                pass

            # drawing cycle, if we got one =)
            viz.render_actions_cycle(e.cycle, args.output_file,
                                     type=args.type, view=args.show)


def generate_pstree_graph(application, args, parser):
    from abstractir.concept import build_concept_process_tree
    import visualize.core as viz

    resource_types_to_skip = get_resources_types_to_skip(args.skip, args.keep)

    process_tree = build_concept_process_tree(application)
    viz.render_pstree(process_tree, args.output_file, output_type=args.type, view=args.show,
                      layout=args.layout, to_skip_resource_types=resource_types_to_skip, no_tmp=args.notmp)


if __name__ == "__main__":
    main(sys.argv[1:])