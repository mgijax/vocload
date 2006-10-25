#!/usr/local/bin/python
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
#  04/29/2005  LEC  Changes for OMIM vocabulary
#	- need to check _MGIType_key of Synonym Type (for both deletions and inserts)
#	  because a Synonym Type name is only unique for a given _MGIType_key.
#
#  03/17/2005  DBM  Initial development
#
###########################################################################

import sys 
import db
import string
import os


dbServer = os.environ['MGD_DBSERVER']
dbName_MGD = os.environ['MGD_DBNAME']
dbName_RADAR = os.environ['RADAR_DBNAME']
dbUser = os.environ['MGD_DBUSER']
passwordFileName = os.environ['MGD_DBPASSWORDFILE']
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

#
#  Get the vocabulary key for the current vocabulary.
#
results = db.sql('select _Vocab_key from VOC_Vocab where name = "' + vocabName + '"', 'auto')
vocabKey = results[0]['_Vocab_key']

#
#  Get the reference key for the J-Number.
#
results = db.sql('select _Object_key from ACC_Accession ' + \
	'where accID = "' + jNumber + '" and _MGIType_key = 1 and _LogicalDB_key = 1', 'auto')
refsKey = results[0]['_Object_key']

#
#  Get the maximum synonym key currently in use.
#
results = db.sql('select max(_Synonym_key) "_Synonym_key" from MGI_Synonym', 'auto')
maxKey = results[0]['_Synonym_key']

print 'Vocab key: %d' % vocabKey

#
#  Delete any synonym from the MGI_Synonym table if the synonym type
#  exists in the VOC_Synonym table in the RADAR database and the term
#  for the synonym belongs to the current vocabulary that is being loaded.
#

synTypes = []
results = db.sql('select distinct st._SynonymType_key ' + \
	'from ' + dbName_RADAR + '..VOC_Synonym v, MGI_SynonymType st ' + \
	'where v.synonymType = st.synonymType ' + \
	'and st._MGIType_key = ' + str(mgiType), 'auto')
for r in results:
    synTypes.append(str(r['_SynonymType_key']))
synTypesIn = string.join(synTypes, ",")

db.sql('delete MGI_Synonym ' + \
            'from MGI_Synonym s, MGI_SynonymType st, VOC_Term t ' + \
            'where s._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  's._SynonymType_key in (' + synTypesIn + ')', None)

#
#  Create a temp table that has an idenity column that can be used to
#  generate the sequential synonym keys for each synonym that is added.
#  The table also contains the term key, synonym type key and synonym
#  that are needed for adding synonyms.
#
db.sql('select tempKey = identity(10), t._Term_key, st._SynonymType_key, s.synonym ' + \
            'into #Synonyms ' + \
            'from ' + dbName_RADAR + '..VOC_Synonym s, ACC_Accession a, VOC_Term t, MGI_SynonymType st ' + \
            'where s.accID = a.accID and ' + \
                  'a._MGIType_key = ' + str(mgiType) + ' and ' + \
                  'a._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  's.synonymType = st.synonymType ' + ' and ' + \
		  'st._MGIType_key = ' + str(mgiType), None)

#
#  Count how many synonyms are to be added.
#
results = db.sql('select count(*) "count" from #Synonyms', 'auto')
print 'Number of synonyms to add: %d' % results[0]['count']

#
#  Add the records to the MGI_Synonym table.
#
db.sql('insert into MGI_Synonym ' + \
            'select tempKey+' + str(maxKey) + ', _Term_key, ' + \
                    str(mgiType) + ', _SynonymType_key, ' + \
                    str(refsKey) + ', synonym, ' + \
                    str(userKey) + ', ' + str(userKey) + ', ' + \
                   'getdate(), getdate() '
            'from #Synonyms', None)

db.useOneConnection(0)
sys.exit(0)

