#!/usr/local/bin/python
#
#  $Header$
#  $Name$
#
#  loadNote.py
###########################################################################
#
#  Purpose:
#
#      This script will use the accession IDs in the VOC_Note table in
#      the RADAR database to identify the terms to add the notes to.
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
#  Implementation:
#
#      This script will perform following steps to add the notes for the
#      given terms:
#
#      1) Delete any note from the MGI_Note table if the note type exists
#         in the VOC_Note table in the RADAR database and the term for
#         the note belongs to the current vocabulary that is being loaded.
#         A trigger will delete the corresponding MGI_NoteChunk records.
#      2) Load a temp table with the values needed for inserting records
#         into the MGI_Note and MGI_NoteChunk tables, including an identity
#         column for generating the sequential primary key.
#      3) Create a record in the MGI_Note and MGI_NoteChunk table for each
#         note in the temp table.
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
userKey = os.environ['USER_KEY']

chunkSequence = 1

#
#  Get the vocabulary key for the current vocabulary.
#
results = db.sql('select _Vocab_key from VOC_Vocab where name = "' + vocabName + '"', 'auto')
vocabKey = results[0]['_Vocab_key']

#
#  Get the maximum note key currently in use.
#
results = db.sql('select max(_Note_key) "_Note_key" from MGI_Note', 'auto')
maxKey = results[0]['_Note_key']

print 'Vocab key: %d' % vocabKey

#
#  Delete any note from the MGI_Note table if the note type exists
#  in the VOC_Note table in the RADAR database and the term for the
#  note belongs to the current vocabulary that is being loaded.
#  A trigger will delete the corresponding MGI_NoteChunk records.
#
noteTypes = []
results = db.sql('select distinct nt._NoteType_key ' + \
	'from ' + dbName_RADAR + '..VOC_Note v, MGI_NoteType nt ' + \
	'where v.noteType = nt.noteType ' + \
	'and nt._MGIType_key = ' + str(mgiType), 'auto')
for r in results:
    noteTypes.append(str(r['_NoteType_key']))
noteTypesIn = string.join(noteTypes, ",")

db.sql('delete MGI_Note ' + \
            'from MGI_Note n, MGI_NoteType nt, VOC_Term t ' + \
            'where n._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  'n._NoteType_key in (' + noteTypesIn + ')', None)

#
#  Create a temp table that has an idenity column that can be used to
#  generate the sequential note keys for each note that is added. The
#  table also contains the term key, note type key and note that are
#  needed for adding notes.
#
db.sql('select tempKey = identity(10), t._Term_key, ' + \
                   'nt._NoteType_key, n.note ' + \
            'into #Notes ' + \
            'from ' + dbName_RADAR + '..VOC_Note n, ' + \
                 'ACC_Accession a, ' + \
                 'VOC_Term t, ' + \
                 'MGI_NoteType nt ' + \
            'where n.accID = a.accID and ' + \
                  'a._MGIType_key = ' + str(mgiType) + ' and ' + \
                  'a._Object_key = t._Term_key and ' + \
                  't._Vocab_key = ' + str(vocabKey) + ' and ' + \
                  'n.noteType = nt.noteType and ' + \
		  'nt._MGIType_key = ' + str(mgiType), None)

#
#  Count how many notes are to be added.
#
results = db.sql('select count(*) "count" from #Notes', 'auto')
print 'Number of notes to add: %d' % results[0]['count']

#
#  Add the records to the MGI_Note table.
#
db.sql('insert into MGI_Note ' + \
            'select tempKey+' + str(maxKey) + ', _Term_key, ' + \
                    str(mgiType) + ', _NoteType_key, ' + \
                    str(userKey) + ', ' + str(userKey) + ', ' + \
                   'getdate(), getdate() '
            'from #Notes', None)

#
#  Add the records to the MGI_NoteChunk table.
#
db.sql('insert into MGI_NoteChunk ' + \
            'select tempKey+' + str(maxKey) + ', ' + \
                    str(chunkSequence) + ', note, ' + \
                    str(userKey) + ', ' + str(userKey) + ', ' + \
                   'getdate(), getdate() '
            'from #Notes', None)

db.useOneConnection(0)
sys.exit(0)
