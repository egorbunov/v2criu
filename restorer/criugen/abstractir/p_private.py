"""
Initialization of private process resource concepts; by private we mean not sharable resources:
internal process state, vm info, page map
"""

from resource_concepts import ProcessInternalsConcept, FSPropsConcept
from model import crdata
from pstree import ProcessTreeConcept
import resource_handles


def init_internal_state_resources(process_tree, application):
    """
    :type process_tree: ProcessTreeConcept
    :type application: crdata.Application
    """
    raw_processes = application.processes

    for p in raw_processes:
        process_concept = process_tree.proc_by_pid(p.pid)

        page_map = ProcessInternalsConcept(p.page_map)
        vm_info = ProcessInternalsConcept(p.vm_info)
        fs_props = FSPropsConcept(p.fs)
        process_core = ProcessInternalsConcept(p.core)
        thread_cores = [ProcessInternalsConcept(t_core) for t_core in p.thread_cores]
        sigacts = ProcessInternalsConcept(p.sigact)

        process_concept.add_resource(page_map, resource_handles.NO_HANDLE)
        process_concept.add_resource(vm_info, resource_handles.NO_HANDLE)
        process_concept.add_resource(fs_props, resource_handles.NO_HANDLE)
        process_concept.add_resource(sigacts, resource_handles.NO_HANDLE)
        process_concept.add_resource(process_core, resource_handles.NO_HANDLE)
        for thread_core in thread_cores:
            process_concept.add_resource(thread_core, resource_handles.NO_HANDLE)
