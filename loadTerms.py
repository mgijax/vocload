# Purpose: to load the input file of vocabulary terms to database tables
#
#   VOC_Term
#   VOC_Vocab
#   ACC_Accession
#   MGI_Note
#   MGI_Synonym
#
# System Requirements Satisfied by This Program:
#
#   Usage: see USAGE definition below
#
#   Inputs:
#
#       1. tab-delimited input file in with the following columns:
#           Term (required)
#           Accession ID (optional)
#           Status (required - 'current' or 'obsolete')
#           Abbreviation (optional)
#           Definition (optional)
#           Comment (optional)
#           Synonyms (optional)
#           Secondary Accession IDs (optional)
#
#       2. mode (full or incremental)
#           'incremental' is not valid for simple vocabularies
#
#       3. primary key of Vocabulary being loaded
#           (why not the name?)
#
#   Outputs:
#
#   Exit Codes:
#       0. script completed successfully, data loaded okay
#       1. script halted, data did not load, error noted in stderr
#           (database is left in a consistent state)
#
# Assumes:
#   We assume no other users are adding/modifying database records during
#   the run of this script.
#
# History
#
# kstone 06/09/2016
#   - TR12336 Fixing bug with new EMAPA terms not getting VOC_Term_EMAPA records.
#   The logic in here was too coupled to the EMAP load, and made it difficult to
#   fix the order in which VOC_Term_EMAPA information is gathered. 
#
#       EMAPA/S logic moved to sub classes in the emap directory
#       They use TermLoad.loadDataFile and TermLoad.postProcess as hooks into 
#       customizing the file input format and the loading of additional tables.
#
# lec	02/18/2016
#	- TR12223/gxd anatomy II
#	merged emapload product into vocload product so we could use the
#	same loadTerms.py class for the EMAPA/EMAPS obo load.  The loadTerms.py was
#	split into a separate emapload version (see TR12188) when only full term loads
#	were required by both EMAPA and EMAPS.  but now the EMAPA load requires an
#	incremental mode.
#
#       the merge of the 2 products allows us to have 1 common loadTerms.py class.
#
#	the other parts of the emapload product are in the vocload/emap directory, as is.
#	added minor changes to support the vocload directory structures, and the
#	incremental mode.
#
# lec	08/02/2005
#	- added UPDATE_STATUS to separate the updating of the status from the term.
#	- if updating the status to obsolete, then don't update the term
#
# lec	04/02/2003
#	- TR 4564; added support for comments
#	- changed GO_ROOT_ID to DAG_ROOT_ID and define an environment variable to store this value
#
# lec	05/15/2002
#	- MGI_LOGICALDB_KEY is an int, but self.logicalDBkey is a str. so the 
#	  check in checkForDuplication was always falling through the "if" statement
#	  because the values will never be equal.  so, MGI_LOGICALDB_KEY is now set to '1';
#	  a str.
#
# lec	05/09/2002
#	- TR 3670; UPDATE_TERM was using single quotes; all other SQL was using double quotes
#

import sys
import types
import getopt
import os

import Log          # MGI-written Python libraries
import vocloadlib
import accessionlib
import Set
import voc_html
import mgi_utils
import db

USAGE = '''Usage: %s [-f|-i][-n][-l <file>] <server> <db> <user> <pwd> <key> <input>
    -f | -i : full load or incremental load? (default is full)
    -n      : use no-load option (log changes, but don't execute them)
    -l      : name of the log file to create (default is stderr only)
    server  : name of the database server
    db      : name of the database
    user    : database login name
    pwd     : password for 'user'
    key     : _Vocab_key for which to load terms
    input   : term input file
''' % sys.argv[0]

# constant for today's date, to be used in BCP files
CDATE = mgi_utils.date("%m/%d/%Y")

# constant for _createdby_key, to be used in BCP files
CREATEDBY_KEY = 1001

###--- Exceptions ---###

class TermLoadError(Exception):
    """
    For all TermLoad exceptions
    """

unknown_mode = 'unknown load mode: %s'
unknown_data_loader = 'unknown data loader: %s'

full_only = 'simple vocabulary (%s) may only use mode "full"'
has_refs = 'cannot do a full load on vocab %s which has cross references'

########################################################################
###--- SQL/BCP INSERT Statements ---###
########################################################################

# templates placed here for readability of the code and
# formatted for readability of the log file

INSERT_TERM = '''insert into VOC_Term (_Term_key, _Vocab_key, term, abbreviation, note, sequenceNum, isObsolete)
    values (%d, %d, '%s', '%s', '%s', %s, %d)'''

BCP_INSERT_TERM = '''%%d|%%d|%%s|%%s|%%s|%%s|%%d|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)

INSERT_NOTE = '''insert into MGI_Note (_Note_key, _Object_key, _MGIType_key, _NoteType_key, note)
    values (%d, %d, %s, %s, '%s')'''

BCP_INSERT_NOTE = '''%%d|%%d|%%s|%%s|%%s|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)

INSERT_SYNONYM ='''insert into MGI_Synonym (_Synonym_key, _Object_key, _MGIType_key, _SynonymType_key, _Refs_key, synonym)
    values (%d, %d, %d, %d, %d, '%s')'''

BCP_INSERT_SYNONYM ='''%%d|%%d|%%d|%%d|%%d|%%s|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)

INSERT_ACCESSION = '''insert into ACC_Accession (_Accession_key, accID, prefixPart, numericPart, _LogicalDB_key, _Object_key, _MGIType_key, private, preferred)
    values (%d, '%s', '%s', %s, %d, %d, %d, %d, %d)'''

BCP_INSERT_ACCESSION_NULL_NUMPART = '''%%d|%%s|%%s||%%d|%%d|%%d|%%d|%%d|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)

BCP_INSERT_ACCESSION_NUMPART = '''%%d|%%s|%%s|%%s|%%d|%%d|%%d|%%d|%%d|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)

#
# note : using 'delete' will fire triggers; truncate will not
#

DELETE_NOTE = '''delete from MGI_Note where _Object_key = %d and _NoteType_key = %s'''

DELETE_ALL_SYNONYMS ='''delete from MGI_Synonym where _Object_key = %d and _MGIType_key = %d'''

#
# specific delete for Disease Ontology only
#
DELETE_DO_XREF = '''delete from ACC_Accession a
USING VOC_Term t
WHERE a.preferred = 0
AND a._LogicalDB_key in (15, 180, 192, 193, 194, 195, 196, 197, 198, 201)
and a._Object_key = t._Term_key
AND t._Vocab_key = 125
'''

UPDATE_TERM = '''update VOC_Term 
        set term = '%s', modification_date = now(), _ModifiedBy_key = 1001
        where _Term_key = %d '''

# note %s : "note = 'xxxx'" OR "note = null" (no quotes)
UPDATE_TERMNOTE = '''update VOC_Term 
        set note = %s, modification_date = now(), _ModifiedBy_key = 1001
        where _Term_key = %d '''

UPDATE_STATUS = '''update VOC_Term 
        set isObsolete = %d, modification_date = now(), _ModifiedBy_key = 1001
        where _Term_key = %d '''

MERGE_TERMS = '''select * from VOC_mergeTerms(%d, %d);'''

########################################################################
########################################################################

# if the vocabulary contains multiple DAGS, then the ID of the DAG ROOT Node
# may be repeated in each dag file.  we don't want to consider this a duplicate ID.
DAG_ROOT_ID = os.environ['DAG_ROOT_ID']

# defines used for convenience
PRIMARY   = "Primary"
SECONDARY = "Secondary"
PRIMARY_SECONDARY_COLLISION_MSG = "FATAL ERROR : no data loaded : Duplicate Primary/Secondary Accession ID used."
TERM_MISSING_FROM_INPUT_FILE = "FATAL ERROR: Term exists in database but NOT in the input file."
OTHER_ID_DELIMITER = '|'
SYNONYM_DELIMITER = '|'
SYNONYM_TYPE_DELIMITER = '|'
MGI_LOGICALDB_KEY = 1		# compared to self.logicalDBkey

###--- Classes ---###

class TermLoad:
    # IS: a data load of vocabulary terms into the database
    # HAS: the following attributes, encompassing both the vocabulary
    #   and the load itself:
    #   vocab_key, vocab_name, isPrivate, isSimple, mode, filename,
    #   datafile, log, max_term_key, max_synonym_key,
    #   max_accession_key, self.id2key
    # DOES: reads from an input data file of term info to load it into
    #   the MGI database

    def __init__(self,
        filename,    # str. path to input file of term info
        mode,        # str. do a 'full' or 'incremental' load?
        vocab,       # integer vocab key or str.vocab name;
                     # which vocabulary to load terms for
        refs_key,    # integer key for the load reference;
        log,         # Log.Log object; used for logging progress
        passwordFile # password file for use with bcp
        ):
        # Purpose: constructor
        # Returns: nothing
        # Assumes: 'filename' is readable
        # Effects: instantiates the object, reads from 'filename'
        # Throws: 1. error if the 'mode' is invalid, if we try to
        #   do an incremental load on a simple vocabulary, or
        #   if try to do a full load on a vocabulary which has
        #   existing cross-references to its terms;
        #   2. propagates vocloadlib.error if we have problems
        #   getting vocab info from the database;
        #   3. propagates exceptions raised by vocloadlib's
        #   readTabFile() function

        # remember the log to which we'll need to write

        self.log = log
        self.passwordFile = passwordFile
        self.primaryAccIDFileList = {}
        self.secondaryAccIDFileList = Set.Set()

        # find vocab key and name (propagate vocloadlib.error if invalid)

        if type(vocab) == str:
            self.vocab_name = vocab
            self.vocab_key = vocloadlib.getVocabKey(vocab)
        else:
            self.vocab_name = vocloadlib.getVocabName(vocab)
            self.vocab_key = vocab

        # write heading to log
        self.log.writeline('=' * 40)
        self.log.writeline('Loading %s Vocabulary Terms...' % self.vocab_name)
        self.log.writeline(vocloadlib.timestamp('Init Start:'))

        # find whether this vocab is private and/or simple,
        # and what its logical db key is
        self.isPrivate = vocloadlib.isPrivate(self.vocab_key)
        self.isSimple = vocloadlib.isSimple(self.vocab_key)
        self.logicalDBkey = vocloadlib.getLogicalDBkey(self.vocab_key)

        # check that the mode is valid
        if mode not in [ 'full', 'incremental' ]:
            raise TermLoadError(unknown_mode % mode)
        self.mode = mode

        # determine if you will be creating a bcp file
        # or performing on-line updates
        self.isBCPLoad = self.setFullModeDataLoader()

        # 01/09/2019 ; fixed but in getMax() for simple vocabularies
        # and now we can allow isSimple/incremental
        # validity checks...
        # 1. we cannot do incremental loads on simple vocabularies
        # 2. we cannot do full loads on vocabularies which are cross-
        #   referenced

        #if self.isSimple and mode != 'full':
        #    raise TermLoadError(full_only % vocab)

        if mode == 'full' and vocloadlib.anyTermsCrossReferenced(self.vocab_key):
                raise TermLoadError(has_refs % vocab)

        # when we actually do the load, we'll look up the current
        # maximum keys for various tables...  For now, we'll just
        # initialize them to None
        self.max_term_key = None    # to be filled in once at the
        self.max_synonym_key = None # start of the load
        self.max_note_key = None

        # Need to look up this number immediately and only once for BCP
        self.max_accession_key = vocloadlib.getMax('_Accession_key', 'ACC_Accession')

        # **** FOR BACKWARD COMPATIBILITY ****
        # Determine if the load should expect to find a synonym type column
        # in the Termfile.  If this environment variable is not set, it is
        # assumed that the load is be used to process an 8-column file
        # without the synonym type column.  If the environment variable is
        # set to 1, it is assumed that the load needs to process a
        # 9-column file that includes a synonym type column.
        #
        try:
            self.useSynonymType = os.environ['USE_SYNONYM_TYPE']
        except:
            self.useSynonymType = 0

        # remember the filename and read the data file
        self.filename = filename

        self.mgitype_key = vocloadlib.VOCABULARY_TERM_TYPE

        self.refs_key = refs_key

        self.id2key = {}    # maps term IDs to term keys

        # initialize and load term datafile
        self.loadDataFile(filename)

        self.log.writeline(vocloadlib.timestamp('Init Stop:'))

        return

    def loadDataFile(self, filename):
        """
        Load the term datafile from filename
        sets self.datafile
        """

        if self.useSynonymType:
            self.datafile = vocloadlib.readTabFile(filename,
                ['term', 'accID', 'status', 'abbreviation',
                'note', 'comment', 'synonyms', 'synonymTypes', 'otherIDs'])
        else:
            self.datafile = vocloadlib.readTabFile(filename,
                ['term', 'accID', 'status', 'abbreviation',
                'note', 'comment', 'synonyms', 'otherIDs'])



    def go(self):
        # Purpose: run the load
        # Returns: nothing
        # Assumes: see self.goFull() and self.goIncremental()
        # Effects: writes to self.log, runs the load and updates the
        #   database
        # Throws: propagates all exceptions from self.goFull() or
        #   self.goIncremental(), whichever is called

        # open the discrepancy file(s) for writing and
        # put in headers
        self.openDiscrepancyFiles()

        # unless this is reset to 0, transaction will be committed
        # (or, in the case of bcp, bcp files will be loaded);
        # only major discrepancies cause this variable to be reset

        self.commitTransaction = 1 

        if self.isIncrementalLoad():
           # Incremental loads perform on-line updates
           self.goIncremental()
        else:
           # Full loads employ BCP *OR* On-line SQL
           self.goFull()

        self.log.writeline('=' * 40)       # end of the load
        self.closeDiscrepancyFiles()
        
        # call any post-processing defined by sub class
        self.postProcess()

        if not self.commitTransaction:
            db.sql('rollback')
            self.log.writeline('Rolling Back Transaction...') 
            msg = "Loading Terms FAILED! Please check %s for errant terms which caused failure" % self.accDiscrepFileName
            self.log.writeline(msg)
            raise TermLoadError(msg)

        # update mgi_synonym_seq and voc_term_seq auto-sequence
        db.sql(''' select setval('mgi_synonym_seq', (select max(_Synonym_key) from MGI_Synonym)) ''', None)
        db.sql(''' select setval('voc_term_seq', (select max(_Term_key) from VOC_Term)) ''', None)
        db.sql(''' select setval('mgi_note_seq', (select max(_Note_key) from MGI_Note)) ''', None)
        db.commit()

        return

    def openBCPFiles(self):
        # Purpose: opens BCP files
        # Returns: nothing
        # Assumes: user executing program has write access in output directory;
        #          this routine only runs if bcp is the method for loading
        #          data
        # Effects: bcp files are open for writing
        # Throws: propagates all exceptions opening files

        # these variables are used to track whether the applicable BCP
        # file has been created

        self.loadTermBCP      = 0
        self.loadNoteBCP      = 0
        self.loadSynonymBCP   = 0
        self.loadAccessionBCP = 0
            
        self.termTermBCPFileName      = os.environ['TERM_TERM_BCP_FILE']
        self.termNoteBCPFileName      = os.environ['TERM_NOTE_BCP_FILE']
        self.termSynonymBCPFileName   = os.environ['TERM_SYNONYM_BCP_FILE']
        self.accAccessionBCPFileName  = os.environ['ACCESSION_BCP_FILE']

        #
        # open files for write
        #
        self.termTermBCPFile      = open(self.termTermBCPFileName, 'w')
        self.termNoteBCPFile      = open(self.termNoteBCPFileName, 'w')
        self.termSynonymBCPFile   = open(self.termSynonymBCPFileName, 'w')
        self.accAccessionBCPFile  = open(self.accAccessionBCPFileName, 'w')

        return

    def openDiscrepancyFiles(self):
        # Purpose: opens discrepancy file, and begins writing the HTML
        #          tags for the report content
        # Returns: nothing
        # Assumes: user executing program has write access in output directory;
        # Effects: discrepancy files are open for writing
        # Throws:  propagates all exceptions opening files

        # open the discrepancy file
        self.accDiscrepFileName = os.environ['DISCREP_FILE']
        
        print("Discrepancy filename: %s" % self.accDiscrepFileName)
        self.accDiscrepFile = open(self.accDiscrepFileName, 'w')

        # now write HTML header information
        self.accDiscrepFile.write(voc_html.getStartHTMLDocumentHTML("Curator Report"))
        self.accDiscrepFile.write(voc_html.getStartTableHTML())
        self.accDiscrepFile.write(voc_html.getStartTableRowHTML())
        self.accDiscrepFile.write(voc_html.getTableHeaderLabelHTML("Accession ID"))
        self.accDiscrepFile.write(voc_html.getTableHeaderLabelHTML("Term"))
        self.accDiscrepFile.write(voc_html.getTableHeaderLabelHTML("Discrepancy"))
        self.accDiscrepFile.write(voc_html.getEndTableRowHTML())

        return

    def closeDiscrepancyFiles(self):
        # Purpose: writes HTML tags to close the table and document tags
        #          and physically closes discrepancy file
        # Returns: nothing
        # Assumes: discrepancy file is open
        # Effects: discrepancy files are closed
        # Throws:  propagates all exceptions closing files

        # write html tags to end the table and html document
        self.accDiscrepFile.write(voc_html.getEndTableHTML())
        self.accDiscrepFile.write(voc_html.getEndHTMLDocumentHTML())

        # now, close the file
        self.accDiscrepFile.close()

        return

    def closeBCPFiles(self):
        # Purpose: closes BCP files
        # Returns: nothing
        # Assumes: BCP files are open
        # Effects: bcp files are closed
        # Throws:  propagates all exceptions closing files

        self.termTermBCPFile.close()    
        self.termNoteBCPFile.close()    
        self.termSynonymBCPFile.close() 
        self.accAccessionBCPFile.close() 

        return

    def loadBCPFiles(self):
        # Purpose: if the load flags are set, calls vocloadlib
        #          which in turn loads the BCP files
        # Returns: nothing
        # Assumes: bcp is in the path
        # Effects: database is loaded
        # Throws:  propagates all bcp exceptions

        if not vocloadlib.NO_LOAD:

           if self.loadTermBCP:
              db.bcp(self.termTermBCPFileName, 'VOC_Term', delimiter='|')
                                                                   
           if self.loadNoteBCP:
              db.bcp(self.termNoteBCPFileName, 'MGI_Note', delimiter='|')
                                                                   
           if self.loadSynonymBCP:                                 
              db.bcp(self.termSynonymBCPFileName, 'MGI_Synonym', delimiter='|')
                                                                   
           if self.loadAccessionBCP:                               
              db.bcp(self.accAccessionBCPFileName, 'ACC_Accession', delimiter='|')

        return

    def goFull(self):
        # Purpose: does a full load for this vocabulary in the
        #   database (delete existing records and completely
        #   reload)
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: for this vocabulary, deletes all term records, with
        #   their associated text fields and synonyms, and reloads
        #   them
        # Throws: propagates all exceptions

        self.log.writeline(vocloadlib.timestamp('Full Term Load Start:'))

        # open the bcp files if using bcp
        if self.isBCPLoad:
            self.openBCPFiles()

        # delete the existing terms, and report how many were deleted.
        count = vocloadlib.countTerms(self.vocab_key)
        # wts2-1147/fl2-270
        #vocloadlib.deleteVocabTerms(self.vocab_key, self.log)
        # do this instead; it's faster
        db.sql('select * from VOC_deleteByVocab(%s)' % (self.vocab_key), None)
        self.log.writeline('deleted all (%d) remaining terms' % count)

        # look up the maximum keys for remaining items in VOC_Term and MGI_Synonym.
        results = db.sql(''' select nextval('voc_term_seq') as termKey ''', 'auto')
        self.max_term_key = results[0]['termKey']

        results = db.sql(''' select nextval('mgi_note_seq') as noteKey ''', 'auto')
        self.max_note_key = results[0]['noteKey']

        results = db.sql(''' select nextval('mgi_synonym_seq') as synKey ''', 'auto')
        self.max_synonym_key = results[0]['synKey']

        # if this is a simple vocabulary, provide sequence numbers for the terms.  
        # if it isn't simple, the sequence number is null.

        if self.isSimple:
            termSeqNum = 0
        else:
            termSeqNum = 'null'

        # each record in the data file should be added as a new term:

        for record in self.datafile:

            if record['accID'] != DAG_ROOT_ID:
               # Check for duplication on the primary term
               duplicate = self.checkForDuplication(record['accID'], record['term'], \
                        "Primary", self.getIsObsolete(record['status']))
               if duplicate:
                   self.log.writeline('Duplicate Primary Term')
                   self.commitTransaction = 0

            if self.isSimple:
               termSeqNum = termSeqNum + 1

            self.addTerm(record, termSeqNum)
            self.addSecondaryTerms(record, self.max_term_key)

        # if we're running as no-load, we need to pass the ID to key
        # mapping to vocloadlib in case the DAG load needs it
        if vocloadlib.isNoLoad():
            vocloadlib.setTermIDs(self.id2key)

        # if commitTransaction == 1, either BCP in the data
        # or commit the transaction; otherwise, rollback
        # the transaction (or don't load BCP files)
        if self.commitTransaction:
           if self.isBCPLoad:
              self.closeBCPFiles()
              self.loadBCPFiles()

        self.log.writeline(vocloadlib.timestamp('Full Term Load Stop:'))

        return

    def addTerm(self,
        record,     # dictionary of fieldname -> value pairs
        termSeqNum  # integer sequence number for a simple vocab's
                    # term, or the str.'null' for complex vocabularies
        ):
        # Purpose: add info for the term in 'record' to the database
        #   with the given sequence number
        # Returns: nothing
        # Assumes: nothing
        # Effects: adds a record to VOC_Term and records to
        #   MGI_Synonym, MGI_Note needed
        # Throws: propagates all exceptions
        # Notes: 'record' must contain values for the following
        #   fieldnames- term, abbreviation, status, definition,
        #   comment, synonyms, accID, otherIDs

        self.max_term_key = self.max_term_key + 1
        #self.log.writeline('------ Term: %s ------' % record['term'])

        # add record to VOC_Term:
        if self.isBCPLoad:

           self.loadTermBCP = 1

           self.termTermBCPFile.write(BCP_INSERT_TERM % \
                                       (self.max_term_key,
                                       self.vocab_key,
                                       record['term'],
                                       record['abbreviation'],
                                       record['note'],
                                       vocloadlib.setNull(termSeqNum),
                                       self.getIsObsolete(record['status'])))

        else: # asserts self.isIncrementalLoad() or full load with on-line sql:

           vocloadlib.nl_sqlog(INSERT_TERM % \
                           (self.max_term_key,
                           self.vocab_key,
                           record['term'].replace('\'','\'\''),
                           record['abbreviation'].replace('\'','\'\''),
                           record['note'].replace('\'','\'\''),
                           termSeqNum,
                           self.getIsObsolete(record['status'])),
                           self.log)

        # add records as needed to MGI_Note:
        self.generateCommentSQL(record['comment'], self.max_term_key)

        # add records as needed to MGI_Synonym:
        synonyms = str.split(record['synonyms'], SYNONYM_DELIMITER)

        # If the input record has synonym types, use them.  
        # Otherwise, use a list of "exact" synonym types for each synonym.
        if self.useSynonymType:
            synonymTypes = str.split(record['synonymTypes'], SYNONYM_TYPE_DELIMITER)
        else:
            synonymTypes = []
            for i in range(len(synonyms)):
                synonymTypes.append("exact")

        self.generateSynonymSQL(synonyms, synonymTypes, self.max_term_key)

        # We can add non-MGI accession numbers to the ACC_Accession
        # table.  We are no longer adding MGI accession IDs to terms
        # All term accession ids from the database 1/2020
        #
        # We assume that the 'otherIDs' come from the same logical
        # database as the primary 'accID', probably due to merges
        # occurring.

        if record['accID']:
            self.addAccID(record['accID'], self.max_term_key, self.logicalDBkey > 1)
            self.id2key[record['accID']] = self.max_term_key

        return

    def addSecondaryTerms(self,
        record,           # dictionary of input file fieldname -> value pairs
        associatedTermKey # primary term key associated with the secondary ID
        ):
        # Purpose: add secondary ids for the term in 'record' 
        #   to the database
        # Returns: nothing
        # Assumes: nothing
        # Effects: makes call to addAccID (to add record to ACC_Accession)
        # Throws: propagates all exceptions
        # Notes: 'record' must contain values (or None) for the following
        #   fieldnames- term, abbreviation, status, definition, comments,
        #   synonyms, accID, otherIDs

        otherIDs = str.strip(record['otherIDs'])

        # add the secondary IDs, if there are any:
        if otherIDs:
            for id in str.split(otherIDs, OTHER_ID_DELIMITER):
                # now check for duplication on secondary terms
                duplicate = self.checkForDuplication(id, record['term'], "Secondary", 0)
                if duplicate:
                    self.commitTransaction = 0
                self.addAccID(str.strip(id), associatedTermKey)

        return

    def generateCommentSQL(self, commentRecord, termKey):
       # Purpose: generates SQL/BCP for MGI_Note table
       # Returns: nothing
       # Assumes: nothing
       # Effects: adds records to MGI_Note in the database
       # Throws: propagates any exceptions raised by vocloadlib's nl_sqlog() function

       if len(commentRecord) == 0:
           return

       self.max_note_key = self.max_note_key + 1
       commentRecord = ''.join([i if ord(i) < 128 else ' ' for i in commentRecord])

       if self.isBCPLoad:
           self.loadNoteBCP = 1
           self.termNoteBCPFile.write(BCP_INSERT_NOTE % (self.max_note_key, 
               termKey, os.environ['MGITYPE'], os.environ['VOCAB_COMMENT_KEY'], commentRecord))
       else:
           vocloadlib.nl_sqlog(INSERT_NOTE % \
                      (self.max_note_key, 
                       termKey, 
                       os.environ['MGITYPE'], 
                       os.environ['VOCAB_COMMENT_KEY'], 
                       commentRecord.replace('\'','\'\'')),
                       self.log)

       return

    def addAccID(self,
        accID,             # str. accession ID to add
        associatedTermKey, # Term Key associated with the record being added
        preferred = 0      # boolean (0/1); is this the object's preferred ID?
        ):
        # Purpose: adds 'accID' as an accession ID for the currently
        #   loading term.
        # Returns: nothing
        # Assumes: called only by self.addTerm()
        # Effects: adds a record to ACC_Accession in the database
        # Throws: propagates any exceptions raised by vocloadlib's
        #   nl_sqlog() function

        self.max_accession_key = self.max_accession_key + 1

        prefixPart, numericPart = accessionlib.split_accnum(accID)
        if numericPart == None:
           numericPart = 'null'

        useLogicalDBkey = self.logicalDBkey

        #
        # TR12427/Disease Ontology
        # pull in tag 'xref'
        # but use a different logicalDB based on the accession id prefix (minus the ending ":")
        # for now, just do this for 'Disease Ontology'
        #
        # that is:
        # if prefixPart = 'OMIM:xxx', then search database for ACC_LogicalDB.name = 'OMIM'
        #
        if (self.vocab_name == 'Disease Ontology'):
            if prefixPart.find('OMIM:PS') >= 0:
                findLDB = 'OMIM:PS'
            else:
                xrefs = prefixPart.split(':')
                findLDB = xrefs[0]
            results = db.sql('''select _LogicalDB_key from ACC_LogicalDB where name = '%s' ''' % (findLDB), 'auto')
            if len(results) > 0:
                useLogicalDBkey = results[0]['_LogicalDB_key']

        if self.isBCPLoad:

           self.loadAccessionBCP = 1

           self.accAccessionBCPFile.write(BCP_INSERT_ACCESSION_NUMPART % \
                                          (self.max_accession_key,
                                          accID,
                                          prefixPart,
                                          numericPart,
                                          useLogicalDBkey,
                                          associatedTermKey,
                                          self.mgitype_key,
                                          self.isPrivate,
                                          preferred)) 

        else: # asserts self.isIncrementalLoad() or full load with on-line sql:

           vocloadlib.nl_sqlog(INSERT_ACCESSION % \
                   (self.max_accession_key, 
                   accID,
                   prefixPart,
                   numericPart,
                   useLogicalDBkey,
                   associatedTermKey,
                   self.mgitype_key,
                   self.isPrivate,
                   preferred),
                   self.log)

        return

    def goIncremental(self):
        # Purpose: does an incremental load for this vocabulary in the
        #   database (comparing the input file to the database and
        #   accounting for differences only)
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: updates the database with data that is new or has
        #          changed since the last load
        # Throws: propagates all exceptions

        self.log.writeline(vocloadlib.timestamp('Incremental Term Load Start:'))

        # look up the maximum keys for remaining items in VOC_Term and MGI_Synonym.
        results = db.sql(''' select nextval('voc_term_seq') as termKey ''', 'auto')
        self.max_term_key = results[0]['termKey']

        self.max_note_key = vocloadlib.getMax('_Note_key', 'MGI_Note')

        results = db.sql(''' select nextval('mgi_synonym_seq') as synKey ''', 'auto')
        self.max_synonym_key = results[0]['synKey']

        # if this is a simple vocabulary, we provide sequence numbers
        # for the terms.  if it isn't simple, the sequence number is
        # null.
        if self.isSimple:
            termSeqNum = vocloadlib.getMax('sequenceNum', 'VOC_Term where _Vocab_key = %d' % (self.vocab_key))
        else:
            termSeqNum = 'null'

        # set annotation type key - this will be used for merging changes
        self.ANNOT_TYPE_KEY = os.environ['ANNOT_TYPE_KEY']

        #
        # DELETE_DO_XREF
        #
        if (self.vocab_name == 'Disease Ontology'):
                vocloadlib.nl_sqlog(DELETE_DO_XREF, self.log)

        # get the existing Accession IDs/Terms from the database
        print("Getting Accession IDs...")
        primaryTermIDs = vocloadlib.getTermIDs(self.vocab_key)
        secondaryTermIDs = vocloadlib.getSecondaryTermIDs(self.vocab_key)

        #get the existing terms for the database
        print("Getting Existing Vocabulary Terms...")
        recordSet = vocloadlib.getTerms(self.vocab_key)

        for record in self.datafile:

            # Cross reference input file records to database records
            # Check for duplication on the primary term - primary accIDs
            # may not refer to more than one term

            self.crossReferenceFileToDB(record['accID'], primaryTermIDs, secondaryTermIDs)

            if record['accID'] != DAG_ROOT_ID:
                duplicate = self.checkForDuplication(record['accID'], record['term'], "Primary", self.getIsObsolete(record['status']))
                if duplicate:
                    # this is considered a serious error, so data will not
                    # be loaded; however, processing will continue so that
                    # we may identify ALL problems with the input file
                    self.commitTransaction = 0

            # Check to see if term exists in the database
            # if term doesn't exist, add it and process
            # its secondary terms; if it does exist
            # check for changes to it and process the 
            # secondary terms

            if record['accID'] in primaryTermIDs:

               [termKey, isObsolete, term, termFound] = primaryTermIDs[record['accID']]

               dbRecord = recordSet.find('_Term_key', termKey)

               if dbRecord == []:
                  raise TermLoadError('AccID in ACC_Accession does not exist in VOC tables for _Object/_Term_Key: "%d"' % termKey)

               else: # Existing record found in VOC tables.  
               
                  # check if record changed
                  recordChanged = self.processRecordChanges(record, dbRecord, termKey)
                  self.processSecondaryTerms(record, primaryTermIDs, secondaryTermIDs, termKey)

            else: # New term

               # in this case, perform full load
               if self.isSimple:
                  termSeqNum = termSeqNum + 1

               self.addTerm(record, termSeqNum)
               self.processSecondaryTerms(record, primaryTermIDs, secondaryTermIDs, self.max_term_key)

        self.checkForMissingTermsInInputFile(primaryTermIDs, secondaryTermIDs)

        return

    def crossReferenceFileToDB(self, accID, primaryTermIDs, secondaryTermIDs):
        # Purpose: Obsoleted terms should always remain in the input file.
        #          This subroutine is used to cross reference each record
        #          in the database to the input file; if the input file record 
        #          exists in the database, it is flagged as such in the
        #          primaryTermID or secondaryTermID structure.  Once processing
        #          is complete, this structure will be iterated through; if 
        #          any terms exist in the database but not the input file,
        #          a discrepancy report record will be written.
        # Returns: nothing
        # Effects: primaryTermID and secondaryTermID structures
        # Throws:  propagates any exceptions raised 

        if accID in primaryTermIDs:
           [termKey, isObsolete, term, termFound] = primaryTermIDs[accID]
           termFound = 1
           primaryTermIDs[accID] = [termKey, isObsolete, term, termFound]

        if accID in secondaryTermIDs:
           [ termKey, term, termFound ] = secondaryTermIDs[accID]
           termFound = 1
           secondaryTermIDs[accID] = [termKey, term, termFound]

    def checkForMissingTermsInInputFile(self, primaryTermIDs, secondaryTermIDs):
        # Purpose: Obsoleted terms should always remain in the input file.
        #          This subroutine is used to check and make sure that all records
        #          in the database also exist in the input file; if the input file
        #          exists in the database, it is flagged as such in the
        #          primaryTermID or secondaryTermID structure in the crossReferenceFileToDB
        #          subroutine.  All records which were not flagged in that routine
        #          are considered non-fatal discrepancies and are written to the Discrepancy 
        #          Report file.
        # Returns: nothing
        # Effects: Discrepancy Report file
        # Throws:  propagates any exceptions raised 

        # Check both the primary AND secondary lists because 
        # if it is a secondary term that is also an obsolete primary term
        # it is permissible for it to appear on both lists

        for accID in list(primaryTermIDs.keys()):
            [termKey, isObsolete, term, termFound] = primaryTermIDs[accID]
            if not termFound:
               self.writeDiscrepancyFile(accID, term, TERM_MISSING_FROM_INPUT_FILE)

        for accID in list(secondaryTermIDs.keys()):
            [termKey, term, termFound] = secondaryTermIDs[accID]
            if not termFound:
              self.writeDiscrepancyFile(accID, term, TERM_MISSING_FROM_INPUT_FILE)

        return

    def checkForDuplication(self, accID, term, termType, isObsolete):
        # Purpose: Check to see if id is duplicated across primary
        #          or secondary terms within the input file (note 
        #          that some "duplication" may legitimately occur
        #          in the case of merges, but that duplication
        #          is between the database and the file, not
        #          within the file, which is what this method checks)
        # Returns: 1 - true, duplication exists, or 0 - false, not a duplicate
        # Assumes: A primary terms should only appear once in the
        #          primary set and not in the secondary 
        #          set and vice versa for secondary terms
        #          UNLESS it is a secondary terms being evaluated
        #          and the primary term is obsolete
        # Effects: writes duplicates to the discrepancy report
        # Throws:  propagates any exceptions raised 

        duplicate = 0

        # only check if using actual accession ids (mgi ids will be blank in the Termfile)

        if self.logicalDBkey != MGI_LOGICALDB_KEY and self.logicalDBkey != -1:

           # the primaryAccIDFileList and secondaryAccIDFileList are simply individual
           # lists of accIDs contained in the input file; if duplicates are found
           # either within a list or across both lists, the record is a potential 
           # duplicate

           if accID in self.primaryAccIDFileList or self.secondaryAccIDFileList.contains(accID):

              # if it is a secondary term that is also an obsolete primary term
              # it is permissible for it to appear on the list
              # otherwise it is a duplicate

              if termType == SECONDARY:

                 if accID in self.primaryAccIDFileList:

                    isObsolete = self.primaryAccIDFileList[accID]

                    if isObsolete == 0:
                       self.writeDiscrepancyFile(accID, term, PRIMARY_SECONDARY_COLLISION_MSG)
                       duplicate = 1

                 else: # accID already appears in secondary list
                    self.writeDiscrepancyFile(accID, term, PRIMARY_SECONDARY_COLLISION_MSG)
                    duplicate = 1

              else: # duplicate primary term
                 self.writeDiscrepancyFile(accID, term, PRIMARY_SECONDARY_COLLISION_MSG)
                 duplicate = 1

           else: # new term - add to list
              if termType == PRIMARY:
                 self.primaryAccIDFileList[accID] = isObsolete
              else:
                 self.secondaryAccIDFileList.add(accID)

        #
        # DO: print the discrepency but do not process as a duplicate
        # at some point, perhaps just entirely skip this entire check for DO?
        #
        if (self.vocab_name == 'Disease Ontology'):
            duplicate = 0

        return duplicate

    def writeDiscrepancyFile(self, accID, term, msg):
        # Purpose: write a record to the discrepancy file
        # Returns: nothing
        # Assumes: discrepancy file is open and writeable
        # Effects: report output
        # Throws:  propagates any exceptions raised 

        self.accDiscrepFile.write(voc_html.getStartTableRowHTML())
        self.accDiscrepFile.write(voc_html.getCellHTML(accID))
        self.accDiscrepFile.write(voc_html.getCellHTML(term))
        self.accDiscrepFile.write(voc_html.getCellHTML(msg))
        self.accDiscrepFile.write(voc_html.getEndTableRowHTML())

        return

    def processSecondaryTerms(self, record, primaryTermIDs, secondaryTermIDs, associatedTermKey):
        # Purpose: Determines if input records need to be merged with other terms
        #          and if secondary terms should be added to the accession table
        #          and does so as necessary
        # Returns: noting
        # Assumes: getTermsIDs only gets Term IDs with the prefered bit set to '1'
        #          i.e., true, because records are only eligible to be merged
        #          if they are primary IDs
        # Effects: Terms are merged and new accession records are added as necessary
        # Throws:  propagates any exceptions raised 

        otherIDs = str.strip(record['otherIDs'])

        if otherIDs:

            for id in str.split(otherIDs, OTHER_ID_DELIMITER):

                id = str.strip(id)
                self.crossReferenceFileToDB(id, primaryTermIDs, secondaryTermIDs)

                # Check to see if secondary term is a duplicated
                # For 'Disease Ontology', skip this step as duplicate secondary ids are allowed

                duplicate = 0

                if (self.vocab_name != 'Disease Ontology'):
                    duplicate = self.checkForDuplication(id, record['term'], "Secondary", 0)

                    if duplicate:
                        self.commitTransaction = 0

                if id in primaryTermIDs and not duplicate:

                    # If the secondary term is in the primaryTermIDs 
                    # structure of existing database records, that means
                    # that the prefered bit is set to true in mgd 
                    # and we therefore need to execute a merge
                    # but only if the primary term is NOT obsolete

                    [termKey, isObsolete, term, termFound] = primaryTermIDs[id]

                # 01/31/2005; this is causing a problem because sometimes obsoleted terms
                # are merged.

#                    if not isObsolete:
                    oldKey = termKey
                    newKey = associatedTermKey

                    # If the keys are the same this is not a merge, e.g. in the mcv there is
                    # a SO id and an MCV id associated with the same term with different
                    # logicalDBs and both preferred ids

                    if oldKey != newKey:
                        vocloadlib.nl_sqlog((MERGE_TERMS %(oldKey, newKey)), self.log)

                else:

                    # check to see if secondary id already exists in database;
                    # if not, add it to accession table

                    if id not in secondaryTermIDs:

                       # The secondary term doesn't exist, so add the term to the
                       # database and point it to the primary term

                       if not self.isBCPLoad:
                          self.max_accession_key = vocloadlib.getMax('_Accession_key', 'ACC_Accession')

                       self.addAccID(id, associatedTermKey, 0)

        return

    def processRecordChanges(self, record, dbRecord, termKey):
       # Purpose: Check to see if input file record is different from the database
       #          in terms of the definition, the comments, the synonyms, the 
       #          isObsolete field, and the term field.  Writes a 
       #          record to the Curator/Discrepancy Report if there are definition
       #          differences or the record has been obsoleted AND there
       #          have been annotations against the record
       # Returns: 1 - true, record has changed, or 0 - false, record has not changed
       # Assumes: Database records for the Term have been retrieved into the dbRecord structure
       # Effects: Executes upates to the term table/note
       #          Executes deletes/inserts into the MGI_Synonym table
       #          Executes updates to the term table (status and terms fields);
       #          note that, for efficiency, both the status and term fields
       #          are updated if either or both fields have to be updated
       # Throws:  propagates any exceptions raised 

       recordChanged = 0

       #
       # Check definition
       #

       definitionDiscrepancy = obsoleteTermDiscrepancy = 0

       #Get dbRecord in sync with file record by converting "None" to blank

       dbDefinition = dbRecord[0]['note']
       recordDefinition = record['note']

       if dbDefinition == None:
           dbDefinition = ""
       if recordDefinition == None:
           recordDefinition = ""

       #self.log.writeline('note: ' + str(dbRecord[0]['_term_key']) + ', ' + str(dbRecord[0]['note']))
       #self.log.writeline('dbDefinition: ' + str(dbDefinition))
       #self.log.writeline('record: ' + str(record['note']))

       if recordDefinition == None:
          vocloadlib.nl_sqlog(UPDATE_TERMNOTE % ('null', termKey), self.log)
          recordChanged = 1
       elif (recordDefinition != dbDefinition):
          vocloadlib.nl_sqlog(UPDATE_TERMNOTE % ("'" + record['note'].replace("'", "''") + "'", termKey), self.log)
          recordChanged = 1
          # Now write report record if the DB record is not null or blank
          # and the term has annotations associated with it
          if dbRecord[0]['note'] is not None:
             definitionDiscrepancy = 1

       #
       # Check comment
       #

       commentDiscrepancy = obsoleteTermDiscrepancy = 0

       # Get dbRecord in sync with file record by converting "None" to blank

       dbComment = dbRecord[0]['comments']

       if dbComment == None:
          dbComment = ""

       if (str.strip(record['comment']) != str.strip(dbComment)):

          # can't do simple update because of 255 size limit; therefore, do a delete and insert
          # no longer true...this should be rewritten to use UPDATE

          vocloadlib.nl_sqlog(DELETE_NOTE % (termKey, os.environ['VOCAB_COMMENT_KEY']), self.log)
          self.generateCommentSQL(record['comment'], termKey)
          recordChanged = 1

          # Now write report record if the DB record is not null or blank
          # and the term has annotations associated with it
          if dbRecord[0]['comments'] is not None:
             commentDiscrepancy = 1

       #
       # Check synonyms
       #

       fileSynonyms = str.split(record['synonyms'], SYNONYM_DELIMITER)

       if fileSynonyms == ['']:
           fileSynonyms = []

       if self.useSynonymType:
           fileSynonymTypes = str.split(record['synonymTypes'], SYNONYM_TYPE_DELIMITER)
           if fileSynonymTypes == ['']:
               fileSynonymTypes = []
       else:
           fileSynonymTypes = []
           for i in range(len(fileSynonyms)):
               fileSynonymTypes.append("exact")

       dbSynonyms = dbRecord[0]['synonyms']
       dbSynonymTypes = dbRecord[0]['synonymTypes']

       # make sure synonyms and synonym types are in the same order
       for i in range(0,len(dbSynonyms)):
           for j in range(i+1,len(dbSynonyms)):
               if dbSynonyms[i] > dbSynonyms[j]:
                   tmpSynonym = dbSynonyms[i]
                   dbSynonyms[i] = dbSynonyms[j]
                   dbSynonyms[j] = tmpSynonym
                   tmpSynonymType = dbSynonymTypes[i]
                   dbSynonymTypes[i] = dbSynonymTypes[j]
                   dbSynonymTypes[j] = tmpSynonymType

       for i in range(0,len(fileSynonyms)):
           for j in range(i+1,len(fileSynonyms)):
               if fileSynonyms[i] > fileSynonyms[j]:
                   tmpSynonym = fileSynonyms[i]
                   fileSynonyms[i] = fileSynonyms[j]
                   fileSynonyms[j] = tmpSynonym
                   tmpSynonymType = fileSynonymTypes[i]
                   fileSynonymTypes[i] = fileSynonymTypes[j]
                   fileSynonymTypes[j] = tmpSynonymType

       if self.useSynonymType and (fileSynonymTypes != dbSynonymTypes):
           changeSynonymTypes = 1
       else:
           changeSynonymTypes = 0

       if (fileSynonyms != dbSynonyms or changeSynonymTypes):
          # if there are any differences between the file and
          # the database, simply delete all existing synonyms
          # and reinsert them
          vocloadlib.nl_sqlog(DELETE_ALL_SYNONYMS % (termKey, self.mgitype_key), self.log)
          self.generateSynonymSQL(fileSynonyms, fileSynonymTypes, termKey)
          recordChanged = 1

       #
       # Finally, check term and status
       #

       fileIsObsoleteField = self.getIsObsolete(record['status'])

       # If field is obsoleted, don't bother updating the term...
       # In the case of OMIM, this would wipe out the "real" term.

       if (fileIsObsoleteField != dbRecord[0]['isObsolete']):

          vocloadlib.nl_sqlog(UPDATE_STATUS % (fileIsObsoleteField, termKey), self.log)
          recordChanged = 1

          # Now write report record if the term is obsoleted 
          # and the term has annotations associated with it
          if (fileIsObsoleteField != dbRecord[0]['isObsolete']):
             obsoleteTermDiscrepancy = 1

       elif (record['term'] != dbRecord[0]['term']):
          # double-quote any single-quote values
          vocloadlib.nl_sqlog(UPDATE_TERM % (record['term'].replace("'", "''"), termKey), self.log)
          recordChanged = 1

       #
       # Now write report discrepancy record(s) if necessary
       #

       if (definitionDiscrepancy or commentDiscrepancy or obsoleteTermDiscrepancy):

          annotations = vocloadlib.getAnyTermMarkerCrossReferences(termKey, self.ANNOT_TYPE_KEY)

          # only write record if annotations exist
          if len (annotations) >= 1:

             symbols = ""

             #build list of symbols

             for annotation in annotations:
                symbols = symbols + " " + annotation['symbol']

             if definitionDiscrepancy:
                msg = "Definition change for Term with annotations.\n" + \
                    "Old Definition: %s\n" % (dbRecord[0]['note']) + \
                    "New Definition: %s\n" % (record['note']) + \
                    "Symbols: %s" % (symbols) 
                self.writeDiscrepancyFile(record['accID'], record['term'], msg)  
           
             if commentDiscrepancy:
                msg = "Comment change for Term with annotations.\n" + \
                    "Old Comment: %s\n" % (dbRecord[0]['comments']) + \
                    "New Comment: %s\n" % (record['comment']) + \
                    "Symbols: %s" % (symbols) 
                self.writeDiscrepancyFile(record['accID'], record['term'], msg)  

             if obsoleteTermDiscrepancy:
                msg = "Term has been obsoleted but has annotations.\n" + \
                    "Symbols: %s" % (symbols) 
                self.writeDiscrepancyFile(record['accID'], record['term'], msg)

       return recordChanged
    
    def generateSynonymSQL(self, fileSynonyms, fileSynonymTypes, termKey):
       # Purpose: add records as needed to MGI_Synonym table
       # Returns: nothing
       # Assumes: open database connection or bcp file
       # Effects: inserts via online sql or bcp into the
       #          MGI_Synonym table
       # Throws:  propagates any exceptions raised 

       for i in range(len(fileSynonyms)):

          if fileSynonyms[i]:

             self.max_synonym_key = self.max_synonym_key + 1
             synonymTypeKey = vocloadlib.getSynonymTypeKey(fileSynonymTypes[i])

             if self.isBCPLoad:
                synonym = fileSynonyms[i]
                self.loadSynonymBCP = 1
                self.termSynonymBCPFile.write(BCP_INSERT_SYNONYM % \
                       (self.max_synonym_key,
                        termKey,
                        self.mgitype_key,
                        synonymTypeKey,
                        self.refs_key,
                        synonym))

             else: # asserts self.isIncrementalLoad() or full load with on-line sql:
                synonym = fileSynonyms[i]
                synonym = synonym.replace("'","''")
                vocloadlib.nl_sqlog(INSERT_SYNONYM % \
                       (self.max_synonym_key,
                        termKey,
                        self.mgitype_key,
                        synonymTypeKey,
                        self.refs_key,
                        synonym), self.log)

       return

    def getIsObsolete(self, recordStatus):
       # Purpose: Returns an isObsolete bit based on the record status
       # Returns: 1 - record is obsolete, 0 - record is not obsolete
       # Assumes: recordStatus is 'obsolete' or 'current'
       # Effects: nothing
       # Throws:  propagates any exceptions raised

       return recordStatus == 'obsolete'

    def isIncrementalLoad(self):
       # Purpose: Returns an isIncremental bit based on the self.mode
       # Returns: 1 - load is incremental, 0 - load is full
       # Assumes: mode is 'full' or 'incremental'
       # Effects: nothing
       # Throws:  propagates any exceptions raised

       return self.mode == 'incremental'

    def setFullModeDataLoader(self):
       # Purpose: Determines the mode of loading data to the database.
       #          The mode of loading is either bcp or on-line SQL.
       #          Incremental loads, by definition, use on-line SQL.
       #          However, if the load is not incremental 
       #          (ie. is full) and a configuration variable, 
       #          'FULL_MODE_DATA_LOADER', is set to 'bcp', then 
       #          bcp will be the method of loading data to the database
       # Returns: 1 - bcp is mode of loading, 0 - online sql is mode of loading
       # Assumes: mode is 'full' or 'incremental'
       # Effects: nothing
       # Throws:  propagates any exceptions raised

       fullModeDataLoader = os.environ['FULL_MODE_DATA_LOADER']

       if fullModeDataLoader == None:
           return 0

       elif fullModeDataLoader == "bcp":

           # Only do BCPs if it is a FULL load and FULL_MODE_DATA_LOADER
           # is set to 'bcp'; INCREMENTALS ALWAYS use on-line SQL

           if self.isIncrementalLoad():
              return 0
           else:
              return 1

       else:
           raise TermLoadError(unknown_data_loader % fullModeDataLoader)
       
       
    ###--- Post Process Hook ---###
    def postProcess(self):
       """
       Use this method in a sub class to do unique post processing
       of a vocabulary load
       """
       pass
       

###--- Main Program ---###

# needs to be rewritten to get configuration from an rcd file

if __name__ == '__main__':

    try:
        options, args = getopt.getopt(sys.argv[1:], 'finl:')

    except getopt.error:
        print('Error: Unknown command-line options/args')
        print(USAGE)
        sys.exit(1)

    if len(args) != 6:
        print('Error: Wrong number of arguments')
        print(USAGE)
        sys.exit(1)

    mode = 'full'
    log = Log.Log()

    [server, database, username, password] = args[:4]
    [vocab_key, refs_key, input_file] = args[4:]

    vocab_key = int(vocab_key)

    noload = 0

    for (option, value) in options:
        if option == '-f':
            mode = 'full'
        elif option == '-i':
            mode = 'incremental'
        elif option == '-n':
            vocloadlib.setNoload()
            noload = 1
        else:
            log = Log.Log(filename = value)

    if noload:
        log.writeline('Operating in NO-LOAD mode')

    vocloadlib.setupSql(server, database, username, password)
    load = TermLoad(input_file, mode, vocab_key, refs_key, log)
    load.go()
    if load.commitTransaction:
           db.commit()
    vocloadlib.unsetupSql()
