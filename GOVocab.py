# Name: GOVocab.py
# Purpose: GO vocabulary class

import os, string, regsub, regex
import DAG, Vocab, GONode

# Globals
##########

# regular expression for GO id in ontology files
GO_re = regex.compile( ' ; \(GO:[0-9]+\)' )

# regular expression for synonyms in ontology files
syn_re = regex.compile('synonym:\([^;<%\n]+\)')

# regular expression for parent terms listed on same line in ontology files
parent_re = regex.compile('\( [<%] \)\([^;<%\n]+\)')

# regular expression for the GO id in definitions file
id_re = regex.compile( 'goid: \(GO:[0-9]+\)' )

# regular expression for the definition in definitions file
def_re = regex.compile( 'definition: \(.+\)' )


class Stack:
    """
    #  Object representing a stack
    """

    def __init__(self):
        """
        #  Requires:
        #  Effects:
        #    constructor
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #  Exceptions:
        """
        
        self.stack = []

    def push(self, obj):
        """
        #  Requires:
        #    obj: any object
        #  Effects:
        #    Appends obj to self.stack
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #  Exceptions:
        """
        
        self.stack.append(obj)

    def pop(self):
        """
        #  Requires:
        #  Effects:
        #    If self.stack is not empty, returns the last element of the
        #    list.  Slices last element off of self.stack.
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #    rval: any object
        #  Exceptions:
        #    STACKEMPTY
        """
        
        if self.isEmpty():
            raise "STACKEMPTY"
        rval = self.stack[-1]
        self.stack = self.stack[:-1]
        return rval

    def peek(self):
        """
        #  Requires:
        #  Effects:
        #    If self.stack is not empty, returns the last element of the
        #    list.
        #  Modifies:
        #  Returns:
        #    rval: any object
        #  Exceptions:
        #    STACKEMPTY
        """
        
        if self.isEmpty():
            raise "STACKEMPTY"
        rval = self.stack[-1]
        return rval

    def isEmpty(self):
        """
        #  Requires:
        #  Effects:
        #    Tests for len of self.stack; if empty, returns true.
        #  Modifies:
        #  Returns:
        #    boolean
        #  Exceptions:
        """
        
        return len(self.stack) == 0


class GOVocab(Vocab.Vocab):
    """
    #  Object representing the Gene Ontology vocabulary
    """

    # mapping of ontology names to corresponding data file names
    files = {'molecular_function': 'function.ontology.txt',
             'biological_process': 'process.ontology.txt',
             'cellular_component': 'component.ontology.txt'}    

    definitions = { }		# cache of definition files loaded so far...
				#	filename -> result of self.getDefs()

    def getDefs(self, inFile):
	"""
        #      Private
        #
	#  Requires:
	#    inFile: file handle (GO definitions file)
	#  Effects:
	#    Creates a dictionary of definitions keyed by GO id
	#  Modifies:
	#  Returns:
	#    defs: dictionary
	#  Exceptions:
	"""

        text = inFile.read()
        text = regsub.gsub('\n', ' ', text)
        text = regsub.gsub('definition_reference:', \
                           '\ndefinition_reference:', text)
        defs = {}
        while 1:
            index = id_re.search(text)
            if index == -1:
                break
            goid = id_re.group(1)
            text = text[index:]
            index = def_re.search(text)
            if index == -1:
                print "Couldn't find definition for %s" % goid
                break
            definition = string.strip(def_re.group(1))
            if len(definition):
                defs[goid] = definition
            text = text[index:]

        return defs
        
    def parseGOline(self, line):
	"""
        #      Private
        #
	#  Requires:
	#    line: string
	#  Effects:
	#    Parses line to determine indentation level, finds the term,
	#    GO id, relationship to parent, and synonyms (if any)
	#  Modifies:
	#  Returns:
	#    level: integer - depth in tree
	#    goid: string
	#    name: string (GO term)
	#    edgeType: string
	#    syns: list of strings
	#  Exceptions:
	"""
	
        if len(line) == 0 or line[0] == "!":
            return

	# get tree depth and relationship
	level = 0
	edgeType = ''
	while level < len(line):
            if line[level] != ' ':
                edgeType = line[level]
                break
            level = level + 1
	else:
            return
	
	# get id and term
	index = GO_re.search( line )
	if index == -1:
            return
	goid = GO_re.group(1)

        secondaryGOIDs = self.getSecondaryGOIDs ( line, goid, index )

	name = string.strip( line[level+1 : index])

	# get synonyms
	syns = []
	while 1:
            index = syn_re.search(line)
            if index == -1:
                break
            syn = string.strip(syn_re.group(1))
            syns.append(syn)
            start = index + 1
            line = line[start:]
		
	return (level, goid, name, edgeType, syns, secondaryGOIDs)
    
    def getSecondaryGOIDs ( self, inLine, goid, index ):
        """
        # Parses line for any secondary goids
        #      Private
        #  Requires:
        #  Effects:
        #  Modifies:
        #  Returns:
        #  Exceptions:
        """
        # the number 3 is used below to move pointer past the " ; " 
        # which precedes the GO ID (e.g., " ; GO:123456")
        #                                     ^ pointer moved to here
        searchSectionStart = 3 + index + len ( goid )
        searchSection = self.findSectionEnd ( inLine[ searchSectionStart : ] )

        # Finally, split the section by the "," to get each ID
        # start at position 1 rather than 0 to bypass leading ","
        # (e.g., ", GO:123456)
        if  len ( searchSection[1:] ) > 0:
           return string.split ( searchSection[1:], "," )
        else:
           return []
        
        
    def findSectionEnd ( self, inLine ):
       """
       # find the end of the section to search (denoted by %, ;, <)
       # Parses line for any secondary goids
       #      Private
       #  Requires:
       #  Effects:
       #  Modifies:
       #  Returns:
       #  Exceptions:
       """
       #remove newline character
       inLine = inLine[:-1]
       if len ( inLine ) > 0:
          i = 0
          while ( i < len ( inLine ) ):
             if inLine[i] in [ '%', ';', '<' ]:
                break
             i = i + 1
          inLine = inLine[0:i]
       return inLine
	
    def parseGOfile(self, ifd):
	"""
        #      Private
        #
	#  Requires:
	#    ifd: file handle
	#  Effects:
	#    Instantiates a DAG object and populates it with nodes and
	#    edges derived from the flat file parse
	#  Modifies:
	#  Returns:
	#    GO: DAG object
	#  Exceptions:
	#    INDENTERROR
	"""

	GO = DAG.DAG()

	nodeStack = Stack()

	firstNode = 1
	lastLevel = -1

	line = ifd.readline()
	while line:
            # tcw 20010820 - Strip out any backslashes in the 
            # ontology files (Stanford currently puts these slashes 
            # in the file to escape characters commas and other 
            # special characters
            line = regsub.gsub ( "\\\\", "",line )
            xxx = self.parseGOline(line)
            if not xxx:
                line = ifd.readline()
                continue
            (level,goid,name,edgeType, syns, secondaryGOIDs) = xxx
            ##### added 3/29/01 - don't recreate nodes! #####

            if GO.nodeById.has_key(goid):
               node = GO.nodeById[goid]
            else:
               node = GONode.GONode(goid, name)
               node.addSynonyms(syns)
               node.setSecondaryGOIDs(secondaryGOIDs)
               GO.addNode(node)

            ##### end new block #####

            if firstNode:
                firstNode = 0
            elif level > lastLevel:
                if level > (lastLevel+1):
                    raise "INDENTERROR", line
                GO.addEdge(nodeStack.peek(), node, edgeType)
            else:
                diff = lastLevel - level
                for i in range(diff+1):
                    nodeStack.pop()
                GO.addEdge(nodeStack.peek(), node, edgeType)
            lastLevel = level
            nodeStack.push(node)

            line = ifd.readline()

	return GO

    def addParents(self, graph, line, childNode):
        """
        #      Private
        #
	#  Requires:
	#    graph: DAG object
        #    line: string
        #    childNode: GONode object
	#  Effects:
	#    Finds all alternate parents on a line of the GO flat file
        #    and adds them to the graph
	#  Modifies:
	#  Returns:
	#  Exceptions:
        """

	parents = []
	for member in graph.getParentsOf(childNode):
            node = member[0]
            parents.append(node.getLabel())
	
	index = parent_re.search(line)
	if index == -1:
            return
	edgeType = string.strip(parent_re.group(1))
	parent = string.strip(parent_re.group(2))
	if parent not in parents:
            try:
                parentNode = graph.nodeByName[parent]
                graph.addEdge(parentNode, childNode, edgeType)
            except KeyError:
                pass
	start = index + 1
	self.addParents(graph, line[start:], childNode)

    def parentSweep(self, graph, ifile):
	"""
        #      Private
        #
	#  Requires:
	#    graph: DAG object
        #    ifile: input file handle
	#  Effects:
	#    Parses GO flat file to retrieve parents that are only listed
        #    adjacent the GO terms
	#  Modifies:
	#  Returns:
	#  Exceptions:
        """

	lines = ifile.readlines()
	for line in lines:
            line = string.lstrip(line)
            if parent_re.search(line) == -1:
                continue
            tokens = string.split(line, ';')
            child = string.strip(tokens[0][1:])
            try:
                childNode = graph.nodeByName[child]
            except KeyError:
                continue
            self.addParents(graph, line, childNode)

    def findMatches(self, query):
	"""
        #      Private
        #
	#  Requires:
	#    query: string
	#  Effects:
	#    Finds terms and/or synonyms that match query string
	#  Modifies:
	#  Returns:
	#    matches: list of nodes
	#  Exceptions:
	"""

        tag = regex.compile('\(<[^>]+>\)')

	l_query = string.lower(query)
        
        # if query string is a GO id...
	if regex.search('^GO:', query) != -1:
            try:
                node = self.graph.nodeById[query]
                return [node]
            except KeyError:
                return []
		
	# find and keep matches to terms and/or synonyms
	matches = []
	terms = self.graph.nodeByName.keys()
	terms.sort()
	for term in terms:
            # case insensitive search, get rid of HTML tags in term
            if string.find(term, '<') != -1:
                lc_term = string.lower(regsub.gsub(tag, '', term))
            else:
                lc_term = string.lower(term)
            node = self.graph.nodeByName[term]
            if string.find(lc_term, l_query) == -1:
                for syn in node.synonyms:
                    lc_syn = string.lower(syn)
                    if string.find(lc_syn, l_query) != -1:
                        matches.append(node)
                        break
            else:
                matches.append(node)

	return matches

    def buildVocab (self, defs_file, dag_file):
	# build this GOVocab using the specified definitions file and dag
	# file

	self.etypes = ['%', '<' ]

	# if we don't already have this definitions file in the cache, then
	# add it:

	if not self.definitions.has_key (defs_file):
		defFile = open (defs_file, 'r')
		self.definitions[defs_file] = self.getDefs (defFile)
		defFile.close()

	defs = self.definitions[defs_file]	# use cached result

	fh = open (dag_file, 'r')
	self.graph = self.parseGOfile(fh)
	fh.close()

	to_do = [ (self.graph.getRoot(), '') ]		# edge type irrelevant

	while to_do:
		node, edge_type = to_do[0]
		id = node.getId()
		del to_do[0]

		if defs.has_key(id):
			node.setDefinition (defs[id])

		to_do = to_do + self.graph.getChildrenOf (node)
	return

    def getRoot (self):
	return self.graph.getRoot()

#
# Warranty Disclaimer and Copyright Notice
#
#  THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE SUITABILITY OR
#  ACCURACY OF THIS SOFTWARE OR DATA FOR ANY PURPOSE, AND MAKES NO WARRANTIES,
#  EITHER EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A
#  PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA WILL NOT
#  INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS, OR OTHER RIGHTS.
#  THE SOFTWARE AND DATA ARE PROVIDED "AS IS".
#
#  This software and data are provided to enhance knowledge and encourage
#  progress in the scientific community and are to be used only for research
#  and educational purposes.  Any reproduction or use for commercial purpose
#  is prohibited without the prior express written permission of the Jackson
#  Laboratory.
#
# Copyright © 1996, 1999, 2000 by The Jackson Laboratory
# All Rights Reserved
#
