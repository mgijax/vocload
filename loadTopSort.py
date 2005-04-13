#!/usr/local/bin/python
#
#  $Header$
#  $Name$
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
import db
import string
import os

import DAG


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

    #  Get the database configuration parameters and set up a connection.
    #
    dbServer = os.environ['DBSERVER']
    dbName_MGD = os.environ['DATABASE']
    dbName_RADAR = os.environ['RADAR_DATABASE']
    dbUser = os.environ['DBUSER']
    passwordFile = os.environ['DBPASSWORD_FILE']
    fp = open(passwordFile, 'r')
    dbPassword = string.strip(fp.readline())
    fp.close()

    db.set_sqlServer(dbServer)
    db.set_sqlDatabase(dbName_MGD)
    db.set_sqlUser(dbUser)
    db.set_sqlPassword(dbPassword)
    db.useOneConnection(1)

    #  Get other configuration setting for the load.
    #
    vocabName = os.environ['VOCAB_NAME']
    mgiType = os.environ['MGITYPE']

    #  Open the bcp file.
    #
    dagSortBCPFile = os.environ['VOC_DAG_SORT_BCP_FILE']
    fpBCP = open(dagSortBCPFile,'w')

    #  Get the vocabulary key for the current vocabulary.
    #
    results = db.sql('select _Vocab_key ' + \
                     'from VOC_Vocab ' + \
                     'where name = "' + vocabName + '"', 'auto')
    vocabKey = results[0]['_Vocab_key']

    #  Get the DAG key for the current vocabulary.
    #
    results = db.sql('select d._DAG_key ' + \
                     'from VOC_VocabDAG v, DAG_DAG d ' + \
                     'where v._Vocab_key = ' + str(vocabKey) + ' and ' + \
                           'v._DAG_key = d._DAG_key and ' + \
                           'd.name = "' + vocabName + '"', 'auto')
    dagKey = results[0]['_DAG_key']

    print 'Vocab key: %d' % vocabKey
    print 'DAG key: %d' % dagKey

    #  Get the root key for the DAG.
    #
    results = db.sql('select n._Node_key ' + \
                     'from DAG_Node n ' + \
                     'where n._DAG_key = ' + str(dagKey) + ' and ' + \
                           'not exists (select 1 ' + \
                                       'from DAG_Edge e ' + \
                                       'where n._Node_key = e._Child_key)',  \
                     'auto')
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

    results = db.sql(cmds, 'auto')

    print 'Nodes: %d' % len(results[1])

    #  Get all the parent/child node pairs that share an edge.
    #
    cmds = []
    cmds.append('select t1._Node_key "parentNodeKey", ' + \
                       't1._Term_key "parentTermKey", ' + \
                       't1.term "parentTerm", ' + \
                       't2._Node_key "childNodeKey", ' + \
                       't2._Term_key "childTermKey", ' + \
                       't2.term "childTerm" ' + \
                'from #TermNode t1, #TermNode t2, DAG_Edge e ' + \
                'where e._Parent_key = t1._Node_key and ' + \
                      'e._Child_key = t2._Node_key and ' + \
                      'e._DAG_key = ' + str(dagKey))

    results = db.sql(cmds, 'auto')

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
        fpBCP.write('%d\t%d\n' % (node.getTermKey(),sequenceNum))
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

    #  Terminate the database connection.
    #
    db.useOneConnection(0)

    return


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

sys.exit(0)
