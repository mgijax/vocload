# Name: GOVocab.py
# Purpose: GO vocabulary class
#
# History
#
# 04/02/2003 lec
#	TR 4564
#
#	- getDefs; added processing of comments from definitions file;
#	  revised from using regular expressions to reading file line by line
#	  and extracting the data by tokens instead.  just couldn't get the
#         thing to work the other way...
#
#	- removed id_re, def_re because they are no longer used by getDefs
#
#	- added call to node.setComment() in buildVocab()
#
# 08/26/2002 lec
# 	TR 3809
#
#	- modifications to enable the same source to be used for processsing *any* vocabulary
#	  in "GO" format 
#
#	- moved global definitions of regular expressions into GO_Vocab method initializeRegExps().
#	  (GO_re, syn_re, id_re, def_re, cmt_re)
#
#	- the following were removed because they were part of the original GO browser which
#	  is not used anymore...
#
#	- removed regular expression "parent_re" (not used)
#
#        # regular expression for parent terms listed on same line in ontology files
#        parent_re = regex.compile('\( [<%] \)\([^;<%\n]+\)')
#
#	- removed these methods because i couldn't find anything that used them:
#		addParents()
#		parentSweep()
#		findMatches()
#
#	- removed "files" definitions (not used):
#
#          # mapping of ontology names to corresponding data file names
#          files = {'molecular_function': 'function.ontology.txt',
#                   'biological_process': 'process.ontology.txt',
#                   'cellular_component': 'component.ontology.txt'}    
#
#

import os, string, regsub, regex
import DAG, Vocab, GONode

# Globals
##########

GO_re = None
syn_re = None

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

    definitions = { }		# cache of definition files loaded so far...
				#	filename -> result of self.getDefs()

    comments = { }		# cache of comments files loaded so far...
				#	filename -> result of self.getDefs()

    def initializeRegExps(self, accPrefix):
	"""
	#
	# Requires:
	#	accPrefix: string, accession id prefix (example:  "GO", "MP"
	# Effects:
	#	initializes regular expressions
	# Modifies:
	#	GO_re, syn_re
	# Returns:
	# Exceptions:
	"""

        global GO_re, syn_re

        # regular expression for GO id in ontology files
        GO_re = regex.compile( ' ; \(%s:[0-9]+\)' % (accPrefix))

        # regular expression for synonyms in ontology files
        syn_re = regex.compile('synonym:\([^;<%\n]+\)')

    def getDefs(self, inFile):
	"""
        #      Private
        #
	#  Requires:
	#    inFile: file handle (GO definitions file)
	#  Effects:
	#    Creates a dictionary of definitions keyed by GO id
	#    Creates a dictionary of comments keyed by GO id
	#  Modifies:
	#  Returns:
	#    defs: dictionary
	#    cmts: dictionary
	#  Exceptions:
	"""

	# field tokens we're interested in grabbing

        ID_TAG = 'goid: '
        DEF_TAG = 'definition: '
        CMT_TAG = 'comment: '

	defs = {}
	cmts = {}

        for line in inFile.readlines():

		token = string.strip(line)

                if token == '!' or len(token) == 0:
                    continue

                if string.find(token, ID_TAG) != -1:
                    goID = token[string.index(token, ID_TAG) + len(ID_TAG):]

                if string.find(token, DEF_TAG) != -1:
                    definition = token[string.index(token, DEF_TAG) + len(DEF_TAG):]
		    defs[goID] = definition

                if string.find(token, CMT_TAG) != -1:
                    comment = token[string.index(token, CMT_TAG) + len(CMT_TAG):]
		    cmts[goID] = comment

	return defs, cmts

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


    def buildVocab (self, defs_file, dag_file):
	# build this GOVocab using the specified definitions file and dag file

	self.etypes = ['%', '<' ]

	# if we don't already have this definitions file in the cache, then add it:

	if not self.definitions.has_key (defs_file):

		defFile = open (defs_file, 'r')
		self.definitions[defs_file], self.comments[defs_file] = self.getDefs (defFile)
		defFile.close()

	defs = self.definitions[defs_file]	# use cached result
	cmts = self.comments[defs_file]		# use cached result

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

		if cmts.has_key(id):
			node.setComment (cmts[id])

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
