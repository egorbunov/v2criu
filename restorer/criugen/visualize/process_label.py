from abstractir.process_concept import ProcessConcept
from abstractir.resource_concepts import *


def get_proc_label(process, to_skip_resource_types=(), no_tmp=False):
    """ Returns cool table lable for the process; Lable contains
    all the resources contain within this process

    :type process: ProcessConcept
    :param to_skip_resource_types: list of process resource may
           be huge, so this parameter lets you to filter out
           some of the process resources not to include in label
    """

    all_resource_pairs = list((r, h) for r, h in process.iter_all_resource_handle_pairs()
                              if not isinstance(r, to_skip_resource_types))

    # sorting by priority
    all_resource_pairs.sort(key=lambda rh: _get_resource_types_attrs()[type(rh[0])][1])

    label_list = ['<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2" CELLPADDING="4">',
                  '<TR><TD COLSPAN="2" CELLPADDING="10" BGCOLOR="{}"><B>{}</B></TD></TR>'.format('#ff8282',
                                                                                     process.minimalistic_repr)]

    for r, h in all_resource_pairs:
        color = _get_resource_types_attrs()[type(r)][0]
        is_tmp = process.is_tmp_resource(r, h)
        if is_tmp and no_tmp:
            continue
        if h is not None:
            label_list.append('<TR><TD COLSPAN="{}" BGCOLOR="{}">{} <I>at</I> {}</TD>{}</TR>'
                              .format(1 if is_tmp else 2,
                                      color, r.minimalistic_repr, h,
                                      '<TD BGCOLOR="{}">tmp</TD>'.format(color) if is_tmp else ''))
        else:
            label_list.append('<TR><TD COLSPAN="{}" BGCOLOR="{}">{}</TD>{}</TR>'
                              .format(1 if is_tmp else 2,
                                      color, r.minimalistic_repr,
                                      '<TD BGCOLOR="{}">tmp</TD>'.format(color) if is_tmp else ''))
    label_list.append("</TABLE>>")
    return ''.join(label_list)


def _get_resource_types_attrs():
    """ Resource types attributes dict
    """
    return {
        ProcessGroupConcept: ("#f7dfdc", 0),
        ProcessSessionConcept: ("#f7eedc", 1),
        RegularFileConcept: ("#eff7dc", 2),
        PipeConcept: ("#dcf7e0", 3),
        SharedMemConcept: ("#dcf7ee", 4),
        ProcessInternalsConcept: ("#dcecf7", 5),
        VMAConcept: ("#e0dcf7", 6),
    }
