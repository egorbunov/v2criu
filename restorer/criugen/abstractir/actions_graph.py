""" Action graph building and other stuff
"""

from pstree import ProcessTreeConcept
from process_concept import ProcessConcept
from actions import *
from pyutils.graph import Graph
import actions_gen
from actions_index import ActionsIndex


def build_actions_graph(process_tree):
    """ Performs analysis of given process concepts tree and builds up
    a graph of actions, which represents restoration process in terms
    of abstract actions

    :param process_tree: process tree concept, which contains all processes
           which are filled with resources concepts
    :type process_tree: ProcessTreeConcept
    :return: actions graph
    """

    action_index, action_graph = _init_actions_graph_and_index(process_tree)
    _build_precedence_edges(process_tree, action_index, action_graph)

    del action_index

    return action_graph


def _init_actions_graph_and_index(process_tree):
    """ Creates actions index and action graph without edges (only with
    vertices)
    :type process_tree: ProcessTreeConcept
    :return: pair: graph and actions index
    :rtype: tuple[ActionsIndex, Graph]
    """

    actions_generator = actions_gen.gen_actions_vertices(process_tree)
    action_index = ActionsIndex()
    action_graph = Graph()

    for action in actions_generator:
        action_index.add_action(action)
        action_graph.add_vertex(action)

    return action_index, action_graph


def _add_precedence_edges_from_to(actions_from, actions_to, actions_graph):
    """ for each `v in actions_from` for each `u in actions_to` add edge
    (v, u) to the actions graph

    :param actions_from: actions, from which edges will go
    :param actions_to: actions, to which edges will go
    :param actions_graph: graph of actions, where to add edges
    :type actions_graph: Graph
    """

    for v in actions_from:
        for u in actions_to:
            actions_graph.add_edge(v, u)


def _build_precedence_edges(process_tree, actions_index, actions_graph):
    """
    :type process_tree: ProcessTreeConcept
    :type actions_index: ActionsIndex
    :type actions_graph: Graph
    """

    _add_after_fork_edges(actions_index, actions_graph)
    _add_after_resource_creation_edges(process_tree, actions_index, actions_graph)


def _add_after_fork_edges(actions_index, actions_graph):
    """ All actions involving a process must be performed AFTER
    that process is forked

    Complexity: (Process-cnt) * (Max-actions-per-process)
    """

    for fa in actions_index.fork_actions:
        process = fa.child  # fa is an action, which creates process fa.child

        # actions, which are somehow involve process during their execution
        actions = actions_index.actions_involving_process(process)
        _add_precedence_edges_from_to([fa], actions, actions_graph)


def _add_after_resource_creation_edges(process_tree, actions_index, actions_graph):
    """ Each (resource, handle) pair inside each process has corresponding action `cr_r`,
    which is responsible for creation of that pair inside a process; But also there
    are actions, which rely on that (resource, handle) is already created; So this
    function builds edges from action `cr_r` to these actions

    Complexity: (Process-cnt) * (Tmp-resource-cnt) * (Max-handle-cnt) * (Max-actions-per-process)

    """

    for process in process_tree.processes:
        _add_after_resource_creation_edges_one_proc(process, actions_index, actions_graph)


def _add_after_resource_creation_edges_one_proc(process, actions_index, actions_graph):
    """ Does the thing described in `_add_after_resource_creation_edges` doc comment,
    but for only one process
    """
    for r, h in process.iter_resource_handle_pairs():
        obtain_act = actions_index.process_obtain_resource_action(process, r, h)
        acts_with_resource = actions_index.process_actions_with_resource(process, r, h)
        _add_precedence_edges_from_to([obtain_act], acts_with_resource, actions_graph)


def _add_before_remove_resource_edges(process_tree, actions_index, actions_graph):
    """ If remove resource action takes place in actions vertices then
    we need to put all other actions with resource before it in the final
    execution scenario;
    This function adds such precedence for temporary resources, which must
    have corresponding remove action

    Complexity: (Process-cnt) * (Tmp-resource-cnt) * (Max-handle-cnt) * (Max-actions-per-process)

    """
    for p in process_tree.processes:
        _add_before_remove_resource_edges_one_proc(p, actions_index, actions_graph)


def _add_before_remove_resource_edges_one_proc(process, actions_index, actions_graph):
    """ Same as `_add_before_remove_resource_edges_one_proc` but for single process
    :type process: ProcessConcept
    """
    for r, h in process.iter_resource_handle_pairs():
        acts_with_resource = actions_index.process_actions_with_resource(process, r, h)
        remove_act = next(a for a in acts_with_resource if isinstance(a, RemoveResourceAction))

        # adding precedence edges FROM all acts except remove act TO remove act!
        _add_precedence_edges_from_to((a for a in acts_with_resource if a != remove_act),
                                      [remove_act],
                                      actions_graph)


def _add_inherited_resource_cr_before_fork_edges(actions_index, actions_graph):
    """ Some resources are inherited from parent process during fork and shared
    that way. So we have to make sure, that parent creates resource, which is
    shared via inheritance with it's children, before forking these children!
    (here our inheritance closure works for us so we can check only children,
    but not the whole subtree)

    Important: if inherited resource is temporary, then the REMOVE action for this resource
    must be performed AFTER fork of children, which share that resource

    Complexity: (Create-acts-cnt) * (Process-cnt)

    :type actions_graph: Graph
    :type actions_index: ActionsIndex
    """

    for cr_act in actions_index.create_actions:
        resource = cr_act.resource

        if resource.is_sharable or not resource.is_inherited:
            # not interested in sharable or private resources
            continue

        creator = cr_act.process
        assert len(cr_act.handles) == 1  # we do not support multi handle non-sharable resource for now
        handle = cr_act.handles[0]

        # only those fork actions, which fork children, who really share the inheritable
        # resource
        fork_acts_which_share = (
            fa for fa in actions_index.fork_actions
            if fa.parent == creator and fa.child.has_resource_at_handle(resource, handle)
        )

        _add_precedence_edges_from_to([cr_act], fork_acts_which_share, actions_graph)

        if not creator.is_tmp_resource(resource, handle):
            continue

        # resource is temporary, there must be reomve action
        remove_act = actions_index.resource_remove_action(creator, resource, handle)

        # temporary resource must be deleted only after forking children, which share that resource
        # via inheritance =)
        _add_precedence_edges_from_to(fork_acts_which_share, [remove_act], actions_graph)


def _add_cr_dependency_before_cr_resource_edges(actions_index, actions_graph):
    """ We have notion of dependency resource: resource, which needed for creation of another
    resource. So we have to make sure, for correct restoration action sequence, that before
    creation of dependant resource the action of creation (initialization) of dependency resource
    is already performed. So this method generates such precedence edges.

    Also each temporary dependency should not be deleted before creation of dependant resource

    Complexity: (Create-act-cnt) * (Max-resource-dependency-cnt) * (Max-per-process-act-cnt + Max-handle-cnt)

    :type actions_index: ActionsIndex
    :type actions_graph: Graph
    """

    for cr_act in actions_index.create_actions:
        process = cr_act.process
        resource = cr_act.resource
        dependencies = resource.dependencies

        for dependency in dependencies:
            dep_cr_act, handles = _find_proper_dependency_creation_act(dependency, process, actions_index)
            _add_precedence_edges_from_to([dep_cr_act], [cr_act], actions_graph)

            # if dependency at handles is temporary, then we should ensure, that
            # remove action for that dependency is performed after dependant resource
            # creation

            # TODO: maybe we could make a little bit more complex
            # TODO: processing in ActionIndex and treat such create action (cr_act)
            # TODO: as an action, which also involves resource (dependency, handle) for
            # TODO: each handle. And then this edges would be added during execution
            # TODO: of `_add_before_remove_resource_edges_one_proc`. But for now it is
            # TODO: easier to put it here

            # getting remove actions for this dependency resource
            dep_remove_acts = \
                (actions_index.resource_remove_action(process, dependency, handle) for handle in handles
                 if process.is_tmp_resource(dependency, handle))

            # ensure, that create resource action should be executed before
            # all these remove dependency actions
            _add_precedence_edges_from_to([cr_act], dep_remove_acts, actions_graph)


def _find_proper_dependency_creation_act(dep_resource, process, actions_index):
    """ This function returns right action, which is responsible for
    initialization of resource `dep_resource` in `process`. Here we try to find
    such action, which translates process from state `r \notin process` to `r \in process`.
    This can be either `CreateAction(process, r, _)` or
    `ShareAction(NOT process, process, r , _, _)`


    :param dep_resource: resource, which "initialization" action we want to find
    :return: action and handles, at which dependency is created or shared; in case
    act is share action, returned handles list is size one
    :rtype: tuple[object, object]
    """
    #  TODO: maybe move this function to ActionIndex as a method

    process_acts = actions_index.actions_involving_process(process)
    for act in process_acts:
        if isinstance(act, ShareResourceAction):
            if act.resource == dep_resource \
                    and act.process_from != process \
                    and act.process_to == process:
                return act, [act.handle_to]
        if isinstance(act, CreateResourceAction):
            if act.resource == dep_resource \
                    and act.process == process:
                return act, act.handles
    raise RuntimeError("No proper dependency create action found for dependency: [{}]"
                       .format(dep_resource))


def _add_can_exist_together_restriction_edges(process_tree, actions_index, actions_graph):
    """ Tries to build such precedence edges on actions that at each point
    in time during restoration process, there would be now two conflicting
    resources within one process. Conflicting resources are those resource,
    which cannot exist together at the same time (see consistency.py for some
    more OS-specific details)

    There are a few main ideas behind the algorithm:

    1) If two resources (r, h) and (r', h') have a conflict, then either (r, h) is
       temporary or (r', h') is temporary

    2) If two resources (r, h) and (r', h') have a conflict and (r, h) is shared during
       fork (i.e. inherited from parent), then all actions with (r, h) must be performed
       before all actions with (r', h')

    These points lead two very important properties of the restoration process satisfiability:

    The restoration (using current approach) is not possible if:

    a. Two inherited resources have a conflict
    b. Temporary resource has a conflict with non-temporary (final) inherited resource

    The real question is: can this cases really happen? If so, then in the final actions
    graph there would be cycles (there is a proof of this statement somewhere in the
    universe and probably in my masters thesis).

    :type process_tree: ProcessTreeConcept
    :type actions_index: ActionsIndex
    :type actions_graph: Graph
    """


def _add_can_exist_together_restriction_edges_one_process(process, actions_index, actions_graph):
    """
    :type process: ProcessConcept
    :type actions_index: ActionsIndex
    :type actions_graph: Graph
    """
    pass
