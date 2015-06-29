#!/usr/local/bin/python
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
#  Assumes:
#
#      This script assumes that a note is not greater than 255 bytes, so it
#      can fit in one record in MGI_NoteChunk.
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
#  04/29/2005  LEC  Need to check _MGIType_key for MGI_Note...
#                   because a Note Type name is only unique for a given _MGIType_key
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
userKey = os.environ['USER_KEY']
noteBcpFile = os.environ['TERM_NOTE_BCP_FILE']
noteChunkBcpFile = os.environ['TERM_NOTECHUNK_BCP_FILE']
bcpErrorFile = os.environ['BCP_ERROR_FILE']
bcpLogFile = os.environ['BCP_LOG_FILE']
cdate = mgi_utils.date("%m/%d/%Y")

chunkSequence = 1

# load synonym file into memory
# in format  ID\ttype\tsynonym
noteFile = sys.argv[1]

print "loading note file %s" % noteFile
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
maxKey = vocloadlib.getMax ('_Note_key', 'MGI_Note')

print 'Vocab key: %d' % vocabKey

# delete existing note records
noteTypes = set([])
for record in noteRecords:
        noteTypes.add(record[1])

noteTypeKeys = []
for noteType in noteTypes:
        typeKey = vocloadlib.getNoteTypeKey(noteType)
        noteTypeKeys.append(typeKey)

noteTypesIn = ','.join([str(key) for key in noteTypeKeys])


vocloadlib.sql('delete from MGI_Note ' + \
            'using MGI_NoteType nt, VOC_Term t ' + \
            'where MGI_Note._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  'MGI_Note._NoteType_key in (' + noteTypesIn + ')')

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
noteChunkBcpRecords = []
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
                userKey,
                userKey,
                cdate,
                cdate
        ])

	# NOTE (kstone): previous version of this load
	# 	always assumed only one note chunk.
	#	You can split the chunks here if needed in the future.
        noteChunkBcpRecords.append([
                count,
		1,
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
print 'Number of notes to add: %d' % len(noteBcpRecords)

#
#  Add the records to the MGI_Note + MGI_NoteChunk tables.
#
fp = open(noteBcpFile, 'w')
for r in noteBcpRecords:
        fp.write('%s\n' % '|'.join([str(c) for c in r]))
fp.close()

fp = open(noteChunkBcpFile, 'w')
for r in noteChunkBcpRecords:
        fp.write('%s\n' % '|'.join([str(c) for c in r]))
fp.close()

vocloadlib.loadBCPFile( noteBcpFile, bcpLogFile, bcpErrorFile, 'mgi_note', passwordFileName)
vocloadlib.loadBCPFile( noteChunkBcpFile, bcpLogFile, bcpErrorFile, 'mgi_notechunk', passwordFileName)


sys.exit(0)
