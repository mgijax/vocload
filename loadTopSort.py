#!/usr/local/bin/python
#
#  loadTopSort.py
###########################################################################
#
#  Purpose:
#
#      This script will determine the topological sort order for a
#      vocabulary using its DAG and create an output file that contains
#      the key for each term in the vocabulary and it sequence number.
#
#  Usage:
#
#      loadTopSort.py
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:  None
#
#  Outputs:
#
#      - Log file (${FULL_LOG_FILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps to determine the
#      topological sort order for a vocabulary:
#
#      1) Load a temp table with term/node information for the vocabulary
#         using the data in the VOC_Term and DAG_Node tables.
#      2) Build a DAG structure using the temp table and the edges defined
#         in the DAG_Edge table.
#      3) Traverse the DAG and sort the nodes at each level based on the
#         term name.
#      4) As each node is visited for the first time, write the term key
#         for that node and a sequence number to the bcp file.
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  03/23/2005  DBM  Initial development
#
###########################################################################

import sys 
import string
import os

import DAG
import vocloadlib


# init database connection
server = os.environ['DBSERVER']
database = os.environ['DBNAME']
username = os.environ['DBUSER']
passwordFileName = os.environ['DBPASSWORDFILE']
fp = open(passwordFileName, 'r')
password = string.strip(fp.readline())
fp.close()
vocloadlib.setupSql (server, database, username, password)
dagSortBCPFile = os.environ['VOC_DAG_SORT_BCP_FILE']
bcpErrorFile = os.environ['BCP_ERROR_FILE']
bcpLogFile = os.environ['BCP_LOG_FILE']

#  Get other configuration setting for the load.
#
vocabName = os.environ['VOCAB_NAME']
mgiType = os.environ['MGITYPE']

#
#  CLASSES
#

class Node:
    #
    # IS: An object that holds the attributes of a DAG node.
    # HAS: A node key identifying the DAG node in the database that this
    #      object represents; a term key and term within the vocabuary
    #      that is associated with this DAG node.
    # DOES: Nothing
    #
    def __init__(self, nodeKey, termKey, term):
        self.nodeKey = nodeKey
        self.termKey = termKey
        self.term = term

    def getId(self):
        return self.nodeKey

    def getLabel(self):
        return self.term

    def getTermKey(self):
        return self.termKey


#
#  FUNCTIONS
#

def initialize():
    #
    # Purpose: Initialize variables, open the bcp file, connects to the
    #          database and obtain keys needed by this load.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables
    # Throws: Nothing
    #
    global vocabKey
    global dagKey
    global rootKey
    global sequenceNum
    global visitedNodes
    global fpBCP

    sequenceNum = 0
    visitedNodes = {}


    #  Open the bcp file.
    #
    fpBCP = open(dagSortBCPFile,'w')

    vocabKey = vocloadlib.getVocabKey(vocabName)

    results = vocloadlib.sql('''
        select _dag_key from voc_vocabdag vd 
	where vd._vocab_key=%s
    ''' % vocabKey)

    dagKey = results[0]['_dag_key']

    print 'Vocab key: %d' % vocabKey
    print 'DAG key: %d' % dagKey

    #  Get the root key for the DAG.
    #
    results = vocloadlib.sql('select n._Node_key ' + \
                     'from DAG_Node n ' + \
                     'where n._DAG_key = ' + str(dagKey) + ' and ' + \
                           'not exists (select 1 ' + \
                                       'from DAG_Edge e ' + \
                                       'where n._Node_key = e._Child_key)')
    rootKey = results[0]['_Node_key']

    print 'Root key: %d' % rootKey

    return


def buildDAG ():
    #
    # Purpose: Build a DAG structure in memory using the node and edge
    #          information for a DAG in the database.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Builds the DAG
    # Throws: Nothing
    #
    global dag

    #  Load the term/node relationships into a temp table for the current DAG.
    #
    cmds = []
    cmds.append('select t._Term_key, t.term, n._Node_key ' + \
                'into #TermNode ' + \
                'from VOC_Term t, DAG_Node n ' + \
                'where t._Term_key = n._Object_key and ' + \
                      'n._DAG_key = ' + str(dagKey))
    cmds.append('select * from #TermNode')

    results = vocloadlib.sql(cmds)

    print 'Nodes: %d' % len(results[1])

    #  Get all the parent/child node pairs that share an edge.
    #
    cmds = []
    cmds.append('select t1._Node_key as parentNodeKey, ' + \
                       't1._Term_key as parentTermKey, ' + \
                       't1.term as parentTerm, ' + \
                       't2._Node_key as childNodeKey, ' + \
                       't2._Term_key as childTermKey, ' + \
                       't2.term as childTerm ' + \
                'from #TermNode t1, #TermNode t2, DAG_Edge e ' + \
                'where e._Parent_key = t1._Node_key and ' + \
                      'e._Child_key = t2._Node_key and ' + \
                      'e._DAG_key = ' + str(dagKey))

    results = vocloadlib.sql(cmds)

    print 'Edges: %d' % len(results[0])

    #  Initialize a DAG object.
    #
    dag = DAG.DAG()

    #  Construct the DAG using each parent/child node pair in the results set.
    #
    for r in results[0]:

        #  Create the parent and child node objects.
        pNode = Node(r['parentNodeKey'],r['parentTermKey'],r['parentTerm'])
        cNode = Node(r['childNodeKey'],r['childTermKey'],r['childTerm'])

        #  Add nodes to the DAG for the parent and child.
        dag.addNode(pNode)
        dag.addNode(cNode)

        #  Add an edge between the parent and child.
        dag.addEdge(pNode,cNode)

    return


def sortNode (node):
    #
    # Purpose: Traverses the DAG structure and applies a sort order to
    #          each node based on the term for each node.  Creates a bcp
    #          file for updating the terms with the sort order.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Writes to the bcp file
    # Throws: Nothing
    #
    global dag
    global sequenceNum
    global fpBCP

    #  If the node has not been visited yet, write its term key and the
    #  next available sequence number to the bcp file.  Otherwise, this
    #  node and all of its children must have been visited already, so
    #  skip it.
    #
    nodeKey = node.getId()
    if not visitedNodes.has_key(nodeKey):
        sequenceNum = sequenceNum + 1
        fpBCP.write('%d|%d\n' % (node.getTermKey(),sequenceNum))
        visitedNodes[nodeKey] = sequenceNum
    else:
        return

    #  Get the list of child nodes (if any).
    #
    childList = dag.getChildrenOf(node)

    #  Sort the child nodes by their term name.
    #
    for i in range(len(childList)):
        for j in range(i+1,len(childList)):
            child1, edgeType1 = childList[i]
            child2, edgeType2 = childList[j]
            term1 = child1.getLabel()
            term2 = child2.getLabel()
            if term1 > term2:
                childList[i] = child2, None
                childList[j] = child1, None

    #  Recursively process each child node.
    #
    for child, edgeType in childList:
        sortNode(child)

    return


def finalize():
    #
    # Purpose: Closes the bcp file and the connection to the database.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    global fpBCP


    #  Close the bcp file.
    #
    fpBCP.close()

    return

def loadBCPFile(bcpFileName):
    """
    Loads the BCP file into 
    a database table and uses that to update voc_term
    """

    # create a table to insert the bcp file
    tempTable = 'tmp_voc_dagsort'
    vocloadlib.sql('''create table %s (_term_key int, sequencenum int)''' % tempTable)

    try:
	# import term sort data
	vocloadlib.loadBCPFile( bcpFileName, bcpLogFile, bcpErrorFile, tempTable, passwordFileName)

	vocloadlib.sql('''create index %s_idx_term_key on %s (_term_key)''' % (tempTable, tempTable))

	# now update voc_term using this imported data
	vocloadlib.sql('''update VOC_Term
	    set sequenceNum = seq.sequenceNum
	    from VOC_Vocab v,
		 %s seq
	    where VOC_Term._Term_key = seq._Term_key and
		  VOC_Term._Vocab_key = v._Vocab_key and
		  v.name = '%s'
	''' % (tempTable, vocabName))
    finally:
        # ensure table is removed when we are finished
        vocloadlib.sql('''drop table %s''' % tempTable)


#
#  MAIN
#

print 'Perform initialization'
initialize()

print 'Build the DAG'
buildDAG()

node = dag.findNode(rootKey)
print 'Root term: %s' % node.getLabel()

print 'Apply topological sort order to the DAG'
sortNode(node)

finalize()

print 'import term sequencenum into voc_term'
loadBCPFile(dagSortBCPFile)

sys.exit(0)
