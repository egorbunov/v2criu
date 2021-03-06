import util
from process_concept import ProcessConcept
from pyutils.graph import DirectedGraph, GraphInterface
from resource_indexer import ResourcesIndexer


class ProcessTreeConcept(GraphInterface):
    """
    Process tree built from processes list
    """

    def __init__(self, processes):
        """ Builds process tree
        :param processes: list of objects with `pid` and `ppid` properties
        :param root: process tree root; if not specified, process with zero
               parent pid is treated as a root
        :type processes: list[ProcessConcept]
        """
        super(ProcessTreeConcept, self).__init__()
        self._processes = sorted(processes, key=lambda p: p.pid)

        roots = util.find_processes_roots(processes)
        if len(roots) != 1:
            raise RuntimeError("Processes do not form a tree!")

        self._root = roots[0]
        self._proc_map = {p.pid: p for p in processes}
        self._proc_graph = self._construct_process_graph()
        self._proc_depths_map = self._calc_process_depths()

        # creating resource indexer to store resources index
        self._resource_indexer = ResourcesIndexer()
        for p in self._processes:
            for r in p.iter_all_resources():
                for h in p.iter_all_handles(r):
                    self._resource_indexer.on_proc_add_resource(p, r, h)

        for p in self._processes:
            p.add_resource_listener(self._resource_indexer)

    @property
    def edges_iter(self):
        return ((parent, child) for parent in self.vertices_iter for child in self.vertex_neighbours(parent))

    @property
    def vertices_iter(self):
        return iter(self.processes)

    def vertex_neighbours(self, vertex):
        return self.proc_children(vertex)

    @property
    def resource_indexer(self):
        """
        Return resource indexer object, which indexes all resource in all
        processes from process tree
        :rtype: ResourcesIndexer
        """
        return self._resource_indexer

    @property
    def processes(self):
        """ Processes, sorted by pid
        :rtype: list[ProcessConcept] 
        """
        return self._processes

    @property
    def sorted_processes(self):
        """ Same as processes, but implicitly `sorted` =)        
        """
        return self._processes

    @property
    def root_process(self):
        """
        :return: process tree root
        :rtype: ProcessConcept
        """
        return self._root

    def proc_children(self, proc):
        """
        :param proc: process instance
        :return: list of children processes for given process
        :rtype: list[ProcessConcept]
        """
        return self._proc_graph.vertex_neighbours(proc)

    def proc_parent(self, proc):
        """
        :param proc: instance of `crdata.Process`
        :return: process parent or None if given process is the root process
        :rtype: ProcessConcept
        """
        if proc == self.root_process:
            return None
        return self._proc_map[proc.ppid]

    def proc_by_pid(self, pid):
        """
        :param pid: process id
        :return: process structure instance
        :rtype: ProcessConcept
        """
        return self._proc_map[pid]

    def process_depth(self, process):
        return self._proc_depths_map[process]

    def lca(self, proc_a, proc_b):
        """ simplest lca implementation; do not need something
        super efficient for now
        """

        # proc_a is lower in the tree
        if self.process_depth(proc_b) > self.process_depth(proc_a):
            proc_a, proc_b = proc_b, proc_a

        while self.process_depth(proc_a) != self.process_depth(proc_b):
            proc_a = self.proc_parent(proc_a)

        while proc_a != proc_b:
            proc_a = self.proc_parent(proc_a)
            proc_b = self.proc_parent(proc_b)

        return proc_a

    def _calc_process_depths(self):
        # calculating process depths
        process_depths_map = {}  # type: dict[ProcessConcept, int]

        def calc_node_depth(p):
            if p == self._root:
                process_depths_map[p] = 0
            else:
                process_depths_map[p] = process_depths_map[self.proc_parent(p)] + 1

        self._proc_graph.dfs_from(v_from=self._root, pre_visit=calc_node_depth)
        return process_depths_map

    def _construct_process_graph(self):
        process_graph = DirectedGraph()

        for p in self.processes:
            process_graph.add_vertex(p)

        for p in self._processes:
            if p == self._root:
                continue
            parent = self.proc_parent(p)
            process_graph.add_edge(parent, p)

        return process_graph


def process_tree_copy(tree, resource_types_to_skip=()):
    """ Makes a copy or process tree with ability to skip certain resources types:
    as a result tree is returned with processes, which contain only those resources,
    which types are not listed in 'resource_types_to_skip' parameter.

    WARNING: be careful with resource_types_to_skip parameter, because this procedure
             performs no logical consistency checks on resulting process tree, so skipped resources
             traces are not cleared from the resulting tree

    :type tree: ProcessTreeConcept
    :param resource_types_to_skip: tuple of resource concept types
    :return: new process tree
    :rtype: ProcessTreeConcept
    """

    new_processes = []
    cur_processes = tree.processes

    for p in cur_processes:
        new_p = ProcessConcept(p.pid, p.ppid)

        for r, h in p.iter_all_resource_handle_pairs():
            if isinstance(r, resource_types_to_skip):
                continue

            if p.is_tmp_resource(r, h):
                new_p.add_tmp_resource(r, h)
            else:
                new_p.add_final_resource(r, h)

        new_processes.append(new_p)

    return ProcessTreeConcept(new_processes)
