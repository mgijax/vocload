#!/usr/local/bin/python
#
#  $Header$
#  $Name$
#
#  loadSynonym.py
###########################################################################
#
#  Purpose:
#
#      This script will use the accession IDs in the VOC_Synonym table in
#      the RADAR database to identify the terms to add the synonyms to.
#
#  Usage:
#
#      loadSynonym.py
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
#      This script will perform following steps to add the synonyms for the
#      given terms:
#
#      1) Delete any synonym from the MGI_Synonym table if the synonym type
#         exists in the VOC_Synonym table in the RADAR database and the term
#         for the synonym belongs to the current vocabulary that is being
#         loaded.
#      2) Load a temp table with the values needed for inserting records
#         into the MGI_Synonym table, including an identity column for
#         generating the sequential primary key.
#      3) Create a record in the MGI_Synonym table for each synonym in the
#         temp table.
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
jNumber = os.environ['JNUM']
userKey = os.environ['USER_KEY']

cmds = []
#
#  Get the vocabulary key for the current vocabulary.
#
cmds.append('select _Vocab_key ' + \
            'from VOC_Vocab ' + \
            'where name = "' + vocabName + '"')

#
#  Get the reference key for the J-Number.
#
cmds.append('select _Object_key ' + \
            'from ACC_Accession ' + \
            'where accID = "' + jNumber + '" and ' + \
                  '_MGIType_key = 1 and ' + \
                  '_LogicalDB_key = 1')

#
#  Get the maximum synonym key currently in use.
#
cmds.append('select max(_Synonym_key) "_Synonym_key" from MGI_Synonym')

results = db.sql(cmds, 'auto')

vocabKey = results[0][0]['_Vocab_key']
refsKey = results[1][0]['_Object_key']
maxKey = results[2][0]['_Synonym_key']

print 'Vocab key: %d' % vocabKey

cmds = []
#
#  Delete any synonym from the MGI_Synonym table if the synonym type
#  exists in the VOC_Synonym table in the RADAR database and the term
#  for the synonym belongs to the current vocabulary that is being loaded.
#
cmds.append('delete MGI_Synonym ' + \
            'from MGI_Synonym s, ' + \
                 'MGI_SynonymType st, ' + \
                 'VOC_Term t ' + \
            'where s._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  's._SynonymType_key = st._SynonymType_key and ' + \
                  'st._MGIType_key = ' + str(mgiType) + ' and ' + \
                  'exists (select 1 ' + \
                          'from ' + dbName_RADAR + '..VOC_Synonym v ' + \
                          'where v.synonymType = st.synonymType)')

#
#  Create a temp table that has an idenity column that can be used to
#  generate the sequential synonym keys for each synonym that is added.
#  The table also contains the term key, synonym type key and synonym
#  that are needed for adding synonyms.
#
cmds.append('select tempKey = identity(10), t._Term_key, ' + \
                   'st._SynonymType_key, s.synonym ' + \
            'into #Synonyms ' + \
            'from ' + dbName_RADAR + '..VOC_Synonym s, ' + \
                 'ACC_Accession a, ' + \
                 'VOC_Term t, ' + \
                 'MGI_SynonymType st ' + \
            'where s.accID = a.accID and ' + \
                  'a._MGIType_key = ' + str(mgiType) + ' and ' + \
                  'a._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  's.synonymType = st.synonymType')

results = db.sql(cmds, 'auto')

cmds = []
#
#  Count how many synonyms are to be added.
#
cmds.append('select count(*) "count" from #Synonyms')

#
#  Add the records to the MGI_Synonym table.
#
cmds.append('insert into MGI_Synonym ' + \
            'select tempKey+' + str(maxKey) + ', _Term_key, ' + \
                    str(mgiType) + ', _SynonymType_key, ' + \
                    str(refsKey) + ', synonym, ' + \
                    str(userKey) + ', ' + str(userKey) + ', ' + \
                   'getdate(), getdate() '
            'from #Synonyms')

results = db.sql(cmds, 'auto')

print 'Number of synonyms to add: %d' % results[0][0]['count']

db.useOneConnection(0)
sys.exit(0)
