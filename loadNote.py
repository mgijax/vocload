#
#  loadNote.py
###########################################################################
#
#  Purpose:
#
#	Loads a note file for voc terms
#
#  Usage:
#
#      loadNote.py
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
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  04/29/2005  LEC  Need to check _MGIType_key for MGI_Note...
#                   because a Note Type name is only unique for a given _MGIType_key
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
userKey = os.environ['USER_KEY']
noteBcpFile = os.environ['TERM_NOTE_BCP_FILE']
bcpErrorFile = os.environ['BCP_ERROR_FILE']
bcpLogFile = os.environ['BCP_LOG_FILE']
cdate = mgi_utils.date("%m/%d/%Y")

# load synonym file into memory
# in format  ID\ttype\tsynonym
noteFile = sys.argv[1]

print("loading note file %s" % noteFile)
noteRecords = []
fp = open(noteFile, 'r')
for line in fp.readlines():
        line = line.strip()
        if line:
                noteRecords.append(line.split('\t'))
fp.close()

#
#  Get the vocabulary key for the current vocabulary.
#
vocabKey = vocloadlib.getVocabKey(vocabName)

#
#  Get the maximum note key currently in use.
#
results = db.sql(''' select nextval('mgi_note_seq') as nextKey ''', 'auto')
maxKey = results[0]['nextKey']

print('Vocab key: %d' % vocabKey)

# delete existing note records
noteTypes = set([])
for record in noteRecords:
        noteTypes.add(record[1])

noteTypeKeys = []
for noteType in noteTypes:
        typeKey = vocloadlib.getNoteTypeKey(noteType)
        noteTypeKeys.append(typeKey)

noteTypesIn = ','.join([str(key) for key in noteTypeKeys])


db.sql('''
        delete from MGI_Note 
        using MGI_NoteType nt, VOC_Term t 
        where MGI_Note._Object_key = t._Term_key 
        and t._Vocab_key = %s
        and MGI_Note._NoteType_key in (%s)
        ''' % (str(vocabKey), noteTypesIn))

#
# map term ID to _term_key
#
termIds = set([])
for record in noteRecords:
        termIds.add(record[0])

termIds = list(termIds)
termKeyMap = vocloadlib.getTermKeyMap(termIds, vocabName)


#
# transform note record into BCP rows
#
count = maxKey + 1
noteBcpRecords = []
for record in noteRecords:

        termid = record[0]
        type = record[1]
        note = record[2]

        # skip any error rows
        if termid not in termKeyMap:
                continue

        typeKey = vocloadlib.getNoteTypeKey(type)

        noteBcpRecords.append([
                count,
                termKeyMap[termid],
                mgiType,
                typeKey,
                note,
                userKey,
                userKey,
                cdate,
                cdate
        ])

        count += 1

#
#  Count how many notes are to be added.
#
print('Number of notes to add: %d' % len(noteBcpRecords))

#
#  Add the records to the MGI_Note table.
#
fp = open(noteBcpFile, 'w')
for r in noteBcpRecords:
        fp.write('%s\n' % '|'.join([str(c) for c in r]))
fp.close()

db.bcp(noteBcpFile, 'MGI_Note', delimiter='|')
db.commit()

db.sql(''' select setval('mgi_note_seq', (select max(_Note_key) from MGI_Note)) ''', None)
db.commit()

sys.exit(0)
