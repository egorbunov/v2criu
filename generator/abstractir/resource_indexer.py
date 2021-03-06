from process_concept import ProcessConcept
from resource_concepts import ResourceConcept
from resource_listener import ProcessResourceListener


class ResourcesIndexer(ProcessResourceListener):
    """ Indexes all resources and stores information
    about which process holds which resource
    """

    def __init__(self):
        self._resource_holders_map = {}  # type: dict[ResourceConcept, set[ProcessConcept]]
        # that is a map from pairs of (resource, handle) to processes list
        self._resource_handle_holders_map = {}  # type: dict[(ResourceConcept, object), set[ProcessConcept]]

    def on_proc_add_resource(self, process, r, h):
        self._resource_holders_map.setdefault(r, set()).add(process)
        if process in self._resource_handle_holders_map.setdefault((r, h), set()):
            print("Warning: adding duplicate (resource, handle) pair for the process")
        self._resource_handle_holders_map.setdefault((r, h), set()).add(process)

    @property
    def all_resources(self):
        """
        :rtype: list[ResourceConcept] 
        """
        return self._resource_holders_map.keys()

    @property
    def all_resources_handles(self):
        """ Returns all pairs (resource, handle), which
        are added to the indexer
        :rtype: list[(ResourceConcept, object)]
        """
        return self._resource_handle_holders_map.keys()

    def get_resource_holders(self, resource):
        """ Processes, which hold specified resource
        :rtype: set[ProcessConcept]
        """
        return self._resource_holders_map.get(resource, [])

    def get_resource_handle_holders(self, resource, handle):
        """ Processes, which hold specified resource pointing
        to it with specified handle
        :rtype: set[ProcessConcept]
        """
        return self._resource_handle_holders_map.get((resource, handle))

    def get_possible_resource_handles(self, resource):
        """ Returns a set of all handles, which point to the resource
        in some processes
        """
        return set(h for (r, h) in self._resource_handle_holders_map if r == resource)
