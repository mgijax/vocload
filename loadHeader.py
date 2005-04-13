#!/usr/local/bin/python
#
#  $Header$
#  $Name$
#
#  loadHeader.py
###########################################################################
#
#  Purpose:
#
#      This script will use the accession IDs in the VOC_Header table in
#      the RADAR database to identify the DAG nodes for the vocabulary
#      terms and set the label key for each node to make it a header node.
#
#  Usage:
#
#      loadHeader.py
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
#      This script will perform following steps to establish the header
#      nodes for a vocabulary:
#
#      1) Use the accession IDs in the VOC_Header table in the RADAR
#         database to identify the DAG nodes for the current vocabulary.
#      2) Update the DAG_Node._Label_key attribute of each of these nodes
#         with the label key for a "Header" node (from DAG_Label).
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
#  03/17/2005  DBM  Initial development
#
###########################################################################

import sys 
import db
import string
import os


dbServer = os.environ['DBSERVER']
dbName_MGD = os.environ['DATABASE']
dbName_RADAR = os.environ['RADAR_DATABASE']
dbUser = os.environ['DBUSER']
passwordFileName = os.environ['DBPASSWORD_FILE']
fp = open(passwordFileName, 'r')
dbPassword = string.strip(fp.readline())

db.set_sqlServer(dbServer)
db.set_sqlDatabase(dbName_MGD)
db.set_sqlUser(dbUser)
db.set_sqlPassword(dbPassword)
db.useOneConnection(1)

vocabName = os.environ['VOCAB_NAME']
mgiType = os.environ['MGITYPE']

#
#  Get the vocabulary key for the current vocabulary.
#
results = db.sql('select _Vocab_key ' + \
                 'from VOC_Vocab ' + \
                 'where name = "' + vocabName + '"', \
                 'auto')
vocabKey = results[0]['_Vocab_key']

#
#  Get the DAG key for the current vocabulary.
#
cmds = []
cmds.append('select d._DAG_key ' + \
            'from VOC_VocabDAG v, DAG_DAG d ' + \
            'where v._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  'v._DAG_key = d._DAG_key and ' + \
                  'd.name = "' + vocabName + '"')

#
#  Get the label key for a "Header" label.
#
cmds.append('select _Label_key ' + \
            'from DAG_Label ' + \
            'where label = "Header"')

results = db.sql(cmds, 'auto')

dagKey = results[0][0]['_DAG_key']
labelKey = results[1][0]['_Label_key']

print 'Vocab key: %d' % vocabKey
print 'DAG key: %d' % dagKey
print 'Label key: %d' % labelKey

#
#  Find all the DAG nodes for the accession IDs in the VOC_Header table
#  and save them in a temp table.
#
cmds = []
cmds.append('select n._Node_key ' + \
            'into #Nodes ' + \
            'from ' + dbName_RADAR + '..VOC_Header h, ' + \
                 'ACC_Accession a, ' + \
                 'VOC_Term t, ' + \
                 'DAG_Node n ' + \
            'where h.accID = a.accID and ' + \
                  'a._MGIType_key = ' + str(mgiType) + ' and ' + \
                  'a._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  't._Term_key = n._Object_key and ' + \
                  'n._DAG_key = ' + str(dagKey))

cmds.append('select count(*) "count" from #Nodes')

#
#  Update the label key for each of the identified nodes using the label key
#  for a header label.
#
cmds.append('update DAG_Node ' + \
            'set _Label_key = ' + str(labelKey) + ' ' + \
            'from DAG_Node n, #Nodes t ' + \
            'where n._Node_key = t._Node_key')

results = db.sql(cmds, 'auto')

print 'Number of header nodes identified: %d' % results[1][0]['count']

db.useOneConnection(0)
sys.exit(0)
