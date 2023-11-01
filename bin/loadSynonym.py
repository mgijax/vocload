#
#  loadSynonym.py
###########################################################################
#
#  Purpose:
#
#	Load a synonym file for voc terms
#       This appends Synonym rows to the TERM_SYNONYM_BCP_FILE that was created by VOCTerm.py
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
import os
import mgi_utils
import db

vocloadpath = os.environ['VOCLOAD'] + '/lib'
sys.path.insert(0, vocloadpath)
import vocloadlib

# init database connection
server = os.environ['DBSERVER']
database = os.environ['DBNAME']
username = os.environ['DBUSER']
passwordFileName = os.environ['DBPASSWORDFILE']
fp = open(passwordFileName, 'r')
password = str.strip(fp.readline())
fp.close()
vocloadlib.setupSql (server, database, username, password)


# get vocabName, mgiTypeKey, jNumber and userKey from environment
vocabName = os.environ['VOCAB_NAME']
mgiType = os.environ['MGITYPE']
jNumber = os.environ['JNUM']
userKey = os.environ['USER_KEY']
bcpFile = os.environ['TERM_SYNONYM_BCP_FILE']
cdate = mgi_utils.date("%m/%d/%Y")

# load synonym file into memory
# in format  ID\ttype\tsynonym
synonymFile = sys.argv[1]

print("loading synonym file %s" % synonymFile)
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
print("vocab name = %s" % vocabName)
print('Vocab key: %d' % vocabKey)

#
#  Get the reference key for the J-Number.
#
results = db.sql('select _object_key from ACC_Accession where accID = \'' + jNumber + '\' and _MGIType_key = 1 and _LogicalDB_key = 1')
refsKey = results[0]['_object_key']

# Delete existing synonym records
synTypes = set([])
for record in synonymRecords:
        synTypes.add(record[1])
synTypeKeys = []
for synType in synTypes:
        typeKey = vocloadlib.getSynonymTypeKey(synType)
        synTypeKeys.append(typeKey)
synTypesIn = ','.join([str(key) for key in synTypeKeys])
db.sql('''
        delete from MGI_Synonym
        using MGI_SynonymType st, VOC_Term t
        where MGI_Synonym._Object_key = t._Term_key
        and t._Vocab_key = %s
        and MGI_Synonym._SynonymType_key in (%s)
        ''' % (str(vocabKey), synTypesIn))
db.commit()
#  Get the maximum synonym key currently in use.
results = db.sql(''' select nextval('mgi_synonym_seq') as synKey ''', 'auto')
synKey = results[0]['synKey']

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
                synKey,	
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
        synKey += 1

#
#  Count how many synonyms are to be added.
#
print('Number of synonyms to add: %d' % len(bcpRecords))

#
#  Add the records to the MGI_Synonym table.
#
fp = open(bcpFile, 'w')
for r in bcpRecords:
        fp.write('%s\n' % '|'.join([str(c) for c in r]))
fp.close()

db.bcp(bcpFile, 'MGI_Synonym', delimiter='|', setval="mgi_synonym_seq", setkey="_synonym_key")
db.commit()

sys.exit(0)
