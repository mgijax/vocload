# Name: DAG.py
# Purpose: classes representing a directed acyclic graph

class Edge:
    """
    #  Object representing a directed edge between two nodes
    """

    def __init__(self, parent, child, etype = None):
        """
        #  Requires:
        #    parent: Node object
        #    child: Node object
        #    etype: string (denoting type of edge) or None
        #  Effects:
        #    Constructor
        #  Modifies:
        #    self.parent, self.child, self.etype
        #  Returns:
        #  Exceptions:
        """
        
       	self.parent = parent
       	self.child = child
       	self.etype = etype

class DAG:
    """
    #  Object representing a directed acyclic graph - keeps track of edges
    #  between nodes, independent of node representation.
    #  Assumes: nodes have a label and an id as attributes
    """

    def __init__(self):
        """
        #  Requires:
        #  Effects:
        #    Constructor
        #  Modifies:
        #    self.nodes: list of nodes
        #    self.outEdges: dictionary of Edge objects keyed by node id
        #    self.inEdges: dictionary of Edge objects keyed by node id
        #    self.nodeByName: dictionary of nodes keyed by node label
        #    self.nodeById: dictionary of nodes keyed by node id
        #  Returns:
        #  Exceptions:
        """
        
       	self.nodes = []
       	self.outEdges = {}
        self.inEdges = {}
       	self.nodeByName = {}
        self.nodeById = {}
        
    def getRoot(self):
        """
        #  Requires:
        #  Effects:
        #    Returns the root node of the graph
        #  Modifies:
        #  Returns:
        #    self.nodes[0]: a node
        #  Exceptions:
        """
        
       	return self.nodes[0]

    def addNode(self, node):
        """
        #  Requires:
        #    node: a Node object
        #  Effects:
        #    Adds a node to the graph
        #  Modifies:
        #    self.nodes, self.nodeByName, self.nodeById
        #  Returns:
        #  Exceptions:
        """

        id = node.getId()
        name = node.getLabel()
       	if self.nodeById.has_key(id):
       		return
        self.nodes.append(node)
       	self.nodeByName[name] = node
        self.nodeById[id] = node

    def addEdge(self, parent, child, eType = None):
        """
        #  Requires:
        #    parent: Node object
        #    child: Node object
        #    etype: string (edge type) or None
        #  Effects:
        #    Adds a directed edge to the graph
        #  Modifies:
        #    self.outEdges, self.inEdges
        #  Returns:
        #  Exceptions:
        """
        
        parentId = parent.getId()
        childId = child.getId()

        ##### added 3/29/01 - don't recreate edges! #####
        proposedEdge = (parent, child, eType)
        try:
           for inEdge in self.inEdges[childId]:
              currentEdge = (inEdge.parent, inEdge.child, inEdge.etype)
              if proposedEdge == currentEdge:
                return
        except KeyError:
           pass
        ##### end new block #####
       	edge = Edge(parent, child, eType)
        if self.outEdges.has_key(parentId):
            self.outEdges[parentId].append(edge)
        else:
            self.outEdges[parentId] = [edge]
        if self.inEdges.has_key(childId):
            self.inEdges[childId].append(edge)
        else:
            self.inEdges[childId] = [edge]

    def getParentsOf(self, node):
        """
        #  Requires:
        #    node: Node object
        #  Effects:
        #    Returns the parents of a node, along with the edge types
        #  Modifies:
        #  Returns:
        #    parents: list of tuples
        #  Exceptions:
        """

        id = node.getId()
        parents = []
        if self.inEdges.has_key(id):
            edges = self.inEdges[id]
            for edge in edges:
                parents.append(edge.parent, edge.etype)
        return parents

    def getChildrenOf(self, node):
        """
        #  Requires:
        #    node: Node object
        #  Effects:
        #    Returns the children of a node, along with the edge types
        #  Modifies:
        #  Returns:
        #    children: list of tuples
        #  Exceptions:
        """

        id = node.getId()
        children = []
        if self.outEdges.has_key(id):
            edges = self.outEdges[id]
            for edge in edges:
                children.append(edge.child, edge.etype)
        return children

    def getPathsTo(self, end, start=None, path=[]):
        """
        #  Requires:
        #    end: target node
        #    start: tuple of starting node and edge type
        #    path: list of tuples containing nodes and edge types
        #    along a path
        #  Effects:
        #    Recursive function that finds all paths in an
        #    acyclic graph between two nodes - uses backtracking.
        #  Modifies:
        #  Returns:
        #    paths: list of paths; each path is a list of tuples
        #    containing a Node object and an edge type
        #  Exceptions:
        """

        if start == None:
            start = (self.getRoot(), None)
        path = path + [start]
        node = start[0]
        if node.getId() == end.getId():
            return [path]
        id = node.getId()
        if not self.outEdges.has_key(id):
            return []
        paths = []
        for edge in self.outEdges[id]:
            newStart = (edge.child, edge.etype)
            if newStart not in path:
                newpaths = self.getPathsTo(end, newStart, path)
                for newpath in newpaths:
                    paths.append(newpath)
        return paths
	
    def getNodesReachableFrom(self, node, etype=None):
        """
        #  Requires:
        #    node: Node object
        #    etype: string (edge type)
        #  Effects:
        #    Depth-first search to find all descendents of a node
        #  Modifies:
        #  Returns:
        #    reachableNodes: list of tuples containing nodes and edge types
        #  Exceptions:
        """

        id = node.getId()
        
        # use etype to get children
        if etype == None:
            children = self.getChildrenOf(node)
        else:
            children = []
            for edge in self.outEdges[id]:
                if edge.etype == etype:
                    children.append(edge.child, edge.etype)

        reachableNodes = children[:]
        # dfs to retrieve all descendents
        for child in children:
            node = child[0]
            id = node.getId()
            if self.outEdges.has_key(id):
                reachableNodes = reachableNodes \
                                 + self.getNodesReachableFrom(node, etype)

        return reachableNodes

    def findNode(self, id):
        """
        #  Requires:
        #    id: string (node id)
        #  Effects:
        #    Returns node from dictionary keyed by id
        #  Modifies:
        #  Returns:
        #    Node object
        #  Exceptions:
        """

        if self.nodeById.has_key(id):
            return self.nodeById[id]
        else:
            return None

    def getTransitiveClosure(self):
        """
        #  Requires:
        #  Effects:
        #    Finds all descendents of every node in the graph
        #  Modifies:
        #  Returns:
        #    closure: dictionary (keys are nodes, values are lists of
        #    tuples containing nodes and edge types)
        #  Exceptions:
        """

        closure = {}
        for node in self.nodes:
            descendents = self.getNodesReachableFrom(node)
            closure[node] = descendents
        
        return closure
