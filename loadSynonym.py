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
#  Inputs:  synonym input file
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
#  10/03/2013  LEC  added "preferred" to accession id query
#
#  04/29/2005  LEC  Changes for OMIM vocabulary
#	- need to check _MGIType_key of Synonym Type (for both deletions and inserts)
#	  because a Synonym Type name is only unique for a given _MGIType_key.
#
#  03/17/2005  DBM  Initial development
#
###########################################################################

import sys 
import string
import os
import vocloadlib
import mgi_utils


# init database connection
server = os.environ['DBSERVER']
database = os.environ['DBNAME']
username = os.environ['DBUSER']
passwordFileName = os.environ['DBPASSWORDFILE']
fp = open(passwordFileName, 'r')
password = string.strip(fp.readline())
fp.close()
vocloadlib.setupSql (server, database, username, password)


# get vocabName, mgiTypeKey, jNumber and userKey from environment
vocabName = os.environ['VOCAB_NAME']
mgiType = os.environ['MGITYPE']
jNumber = os.environ['JNUM']
userKey = os.environ['USER_KEY']
bcpFile = os.environ['TERM_SYNONYM_BCP_FILE']
bcpErrorFile = os.environ['BCP_ERROR_FILE']
bcpLogFile = os.environ['BCP_LOG_FILE']
cdate = mgi_utils.date("%m/%d/%Y")

# load synonym file into memory
# in format  ID\ttype\tsynonym
synonymFile = sys.argv[1]

print "loading synonym file %s" % synonymFile
synonymRecords = []
fp = open(synonymFile, 'r')
for line in fp.readlines():
	line = line.strip()
	if line:
		synonymRecords.append(line.split('\t'))
fp.close()

#
#  Get the vocabulary key for the current vocabulary.
#
vocabKey = vocloadlib.getVocabKey (vocabName)
print "vocab name = %s" % vocabName
print 'Vocab key: %d' % vocabKey

#
#  Get the reference key for the J-Number.
#
results = vocloadlib.sql('select _object_key from ACC_Accession ' + \
	'where accID = \'' + jNumber + '\' and _MGIType_key = 1 and _LogicalDB_key = 1')
refsKey = results[0]['_object_key']

#
#  Get the maximum synonym key currently in use.
#
maxKey = vocloadlib.getMax ('_Synonym_key', 'MGI_Synonym')


#
#  Delete any synonym from the MGI_Synonym table if the synonym type
#  exists in the VOC_Synonym table in the RADAR database and the term
#  for the synonym belongs to the current vocabulary that is being loaded.
#

synTypes = set([])
for record in synonymRecords:
	synTypes.add(record[1])

synTypeKeys = []
for synType in synTypes:
	typeKey = vocloadlib.getSynonymTypeKey(synType)
	synTypeKeys.append(typeKey)
	
synTypesIn = ','.join([str(key) for key in synTypeKeys])

vocloadlib.sql('delete from MGI_Synonym ' + \
            'from MGI_SynonymType st, VOC_Term t ' + \
            'where MGI_Synonym._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  'MGI_Synonym._SynonymType_key in (' + synTypesIn + ')')

#
# map term ID to _term_key
#
termIds = set([])
for record in synonymRecords:
	termIds.add(record[0])

termIds = list(termIds)
termKeyMap = vocloadlib.getTermKeyMap(termIds, vocabName)


#
# transform synonym record into BCP row
#
count = maxKey + 1
bcpRecords = []
for record in synonymRecords:

	termid = record[0]
	type = record[1]
	synonym = record[2]

	# skip any error rows
	if termid not in termKeyMap:
		continue


	typeKey = vocloadlib.getSynonymTypeKey(type)

	bcpRecords.append([
		count,	
		termKeyMap[termid],
		mgiType,
		typeKey,
		refsKey,
		synonym,
		userKey,
		userKey,
		cdate,
		cdate
	])
	count += 1

#
#  Count how many synonyms are to be added.
#
print 'Number of synonyms to add: %d' % len(bcpRecords)

#
#  Add the records to the MGI_Synonym table.
#
fp = open(bcpFile, 'w')
for r in bcpRecords:
	fp.write('%s\n' % '|'.join([str(c) for c in r]))
fp.close()

vocloadlib.loadBCPFile( bcpFile, bcpLogFile, bcpErrorFile, 'mgi_synonym', passwordFileName) 


sys.exit(0)

