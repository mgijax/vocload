#!/usr/local/bin/python

# Program: loadTerms
# Purpose: to load the input file of vocabulary terms to database tables
#   VOC_Vocab, VOC_Term, VOC_Text, VOC_Synonym
# User Requirements Satisfied by This Program:
# System Requirements Satisfied by This Program:
#   Usage: see USAGE definition below
#   Uses:
#   Envvars:
#   Inputs:
#       1. tab-delimited input file in with the following columns:
#           Term (required)
#           Accession ID (optional)
#           Status (required - 'current' or 'obsolete')
#           Abbreviation (optional)
#           Definition (optional)
#           Synonyms (optional)
#           Secondary Accession IDs (optional)
#       2. mode (full or incremental)
#           'incremental' is not valid for simple vocabularies
#       3. primary key of Vocabulary being loaded
#           (why not the name?)
#   Outputs:
#   Exit Codes:
#       0. script completed successfully, data loaded okay
#       1. script halted, data did not load, error noted in stderr
#           (database is left in a consistent state)
#   Other System Requirements:
# Assumes:
#   We assume no other users are adding/modifying database records during
#   the run of this script.
# Implementation:
#   Modules:

import sys          # standard Python libraries
import types
import string
import getopt

USAGE = '''Usage: %s [-f|-i][-n][-l <file>] <server> <db> <user> <pwd> <key> <input>
    -f | -i : full load or incremental load? (default is full)
    -n  : use no-load option (log changes, but don't execute them)
    -l  : name of the log file to create (default is stderr only)
    server  : name of the database server
    db  : name of the database
    user    : database login name
    pwd : password for 'user'
    key : _Vocab_key for which to load terms
    input   : term input file
''' % sys.argv[0]

import Log          # MGI-written Python libraries
import vocloadlib
import accessionlib
import Set
import html

###--- Exceptions ---###

error = 'TermLoad.error'    # exception raised with these values:

unknown_mode = 'unknown load mode: %s'
unknown_data_loader = 'unknown data loader: %s'

full_only = 'simple vocabulary (%s) may only use mode "full"'
has_refs = 'cannot do a full load on vocab %s which has cross references'

########################################################################
###--- SQL/BCP INSERT Statements ---###
########################################################################

# templates placed here for readability of the code and
# formatted for readability of the log file

INSERT_TERM = '''insert VOC_Term (_Term_key, _Vocab_key, term,
        abbreviation, sequenceNum, isObsolete)
    values (%d, %d, "%s",
        "%s", %s, %d)'''
BCP_INSERT_TERM = '''%d^%d^%s^%s^%s^%d^^\n'''

INSERT_TEXT = '''insert VOC_Text (_Term_key, sequenceNum, note)
    values (%d, %d, "%s")'''
BCP_INSERT_TEXT = '''%d^%d^%s^^\n'''


INSERT_SYNONYM ='''insert VOC_Synonym (_Synonym_key, _Term_key, synonym)
    values (%d, %d, "%s")'''
BCP_INSERT_SYNONYM ='''%d^%d^%s^^\n'''

INSERT_ACCESSION = '''insert ACC_Accession (_Accession_key, accID, prefixPart, numericPart,
        _LogicalDB_key, _Object_key, _MGIType_key, private, preferred)
    values (%d, "%s", "%s", %s,
        %d, %d, %d, %d, %d)'''
BCP_INSERT_ACCESSION = '''%d^%s^%s^%s^%d^%d^%d^%d^%d^^^\n'''


DELETE_TEXT = '''delete from VOC_Text where _Term_key = %d'''

DELETE_ALL_SYNONYMS ='''delete from VOC_Synonym where _Term_key = %d'''

UPDATE_TERM = '''update VOC_Term set term = '%s', isObsolete = %d where _Term_key = %d '''

UPDATE_SYNONYM = '''update VOC_Synonym set synonym = '%s' where _Term_key = %d'''

MERGE_TERMS = '''exec VOC_mergeTerms %d, %d'''
########################################################################
########################################################################

# GO_ROOT_ID is for the GO load only - I hate to put in
# in the code but it is necessary for processing
# and should not adversely affect anything other apps
GO_ROOT_ID = "GO:0003673"

# defines used for convenience
PRIMARY   = "Primary"
SECONDARY = "Secondary"
PRIMARY_SECONDARY_COLLISION_MSG = "Duplicate Primary/Secondary Accession ID Used. This is a fatal error - no data was loaded to the database"
OTHER_ID_DELIMITER = '|'
SYNONYM_DELIMITER = '|'
MGI_LOGICALDB_KEY = 1

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

    def __init__ (self,
        filename,    # string; path to input file of term info
        mode,        # string; do a 'full' or 'incremental' load?
        vocab,       # integer vocab key or string vocab name;
                     # which vocabulary to load terms for
        log,         # Log.Log object; used for logging progress
        config,      # configuration (.rcd) file reference
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

        self.config = config

        self.passwordFile = passwordFile

        self.primaryAccIDFileList = {}
        self.secondaryAccIDFileList = Set.Set()

        # find vocab key and name (propagate vocloadlib.error if
        # invalid)

        if type(vocab) == types.StringType:
            self.vocab_name = vocab
            self.vocab_key = vocloadlib.getVocabKey (vocab)
        else:
            self.vocab_name = vocloadlib.getVocabName (vocab)
            self.vocab_key = vocab

        self.LOGICALDB_KEY = self.config.getConstant('LOGICALDB_KEY')

        # write heading to log

        self.log.writeline ('=' * 40)
        self.log.writeline ('Loading %s Vocabulary Terms...' % \
            self.vocab_name)
        self.log.writeline (vocloadlib.timestamp ('Init Start:'))

        # find whether this vocab is private and/or simple,
        # and what its logical db key is

        self.isPrivate = vocloadlib.isPrivate (self.vocab_key)
        self.isSimple = vocloadlib.isSimple (self.vocab_key)
        self.logicalDBkey = vocloadlib.getLogicalDBkey(self.vocab_key)

        # check that the mode is valid

        if mode not in [ 'full', 'incremental' ]:
            raise error, unknown_mode % mode
        self.mode = mode

        # determine if you will be creating a bcp file
        # or performing on-line updates
        self.isBCPLoad = self.setFullModeDataLoader()

        # validity checks...
        # 1. we cannot do incremental loads on simple vocabularies
        # 2. we cannot do full loads on vocabularies which are cross-
        #   referenced

        if self.isSimple and mode != 'full':
            raise error, full_only % vocab

        if mode == 'full' and vocloadlib.anyTermsCrossReferenced (
            self.vocab_key):
                raise error, has_refs % vocab

        # when we actually do the load, we'll look up the current
        # maximum keys for various tables...  For now, we'll just
        # initialize them to None

        self.max_term_key = None    # to be filled in once at the
        self.max_synonym_key = None # start of the load

        if self.isBCPLoad:
           # Need to look up this number immediately and only once
           # for BCP
           self.max_accession_key = max (0, vocloadlib.getMax (
               '_Accession_key', 'ACC_Accession'))
        else:
           self.max_accession_key = None   # to be filled in later for
                           # each term (because MGI IDs
                           # may be added by a trigger)

        # remember the filename and read the data file

        self.filename = filename
        self.datafile = vocloadlib.readTabFile (filename,
            [ 'term', 'accID', 'status', 'abbreviation',
            'definition', 'synonyms', 'otherIDs' ])

        self.mgitype_key = vocloadlib.VOCABULARY_TERM_TYPE

        self.id2key = {}    # maps term IDs to term keys

        self.log.writeline (vocloadlib.timestamp ('Init Stop:'))
        return

    def go (self):
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
        # only major discrepancies cause this variable to 
        # be reset
        self.commitTransaction = 1 
        if self.isIncrementalLoad():
           # Incremental loads perform on-line updates
           self.goIncremental ()
        else:
           # Full loads employ BCP *OR* On-line SQL
           self.goFull()
        self.log.writeline ('=' * 40)       # end of the load
        self.closeDiscrepancyFiles()
        if not self.commitTransaction:
            msg = "Loading Terms FAILED! Please check %s for errant terms which caused failure" % self.accDiscrepFileName
            self.log.writeline ( msg )
            raise msg
        # always update accession statistics after the load has run
        vocloadlib.updateStatistics ( "ACC_Accession", self.log )
        return

    def openBCPFiles ( self ):
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
        self.loadTextBCP      = 0
        self.loadSynonymBCP   = 0
        self.loadAccessionBCP = 0
            
        self.termTermBCPFileName     = self.config.getConstant('TERM_TERM_BCP_FILE')
        self.termTextBCPFileName     = self.config.getConstant('TERM_TEXT_BCP_FILE')
        self.termSynonymBCPFileName  = self.config.getConstant('TERM_SYNONYM_BCP_FILE')
        self.accAccessionBCPFileName = self.config.getConstant('ACCESSION_BCP_FILE')

        self.termTermBCPFile      = open( self.termTermBCPFileName     , 'w')
        self.termTextBCPFile      = open( self.termTextBCPFileName     , 'w')
        self.termSynonymBCPFile   = open( self.termSynonymBCPFileName  , 'w')
        self.accAccessionBCPFile  = open( self.accAccessionBCPFileName , 'w')

    def openDiscrepancyFiles ( self ):
        # Purpose: opens discrepancy file, and begins writing the HTML
        #          tags for the report content
        # Returns: nothing
        # Assumes: user executing program has write access in output directory;
        # Effects: discrepancy files are open for writing
        # Throws:  propagates all exceptions opening files

        # open the discrepancy file
        self.accDiscrepFileName = self.config.getConstant('DISCREP_FILE')
        self.accDiscrepFile     = open( self.accDiscrepFileName     , 'w')

        # now write HTML header information
        self.accDiscrepFile.write ( html.getStartHTMLDocumentHTML ( "Curator Report" ) )
        self.accDiscrepFile.write ( html.getStartTableHTML () )
        self.accDiscrepFile.write ( html.getStartTableRowHTML () )
        self.accDiscrepFile.write ( html.getTableHeaderLabelHTML ( "Accession ID" ) )
        self.accDiscrepFile.write ( html.getTableHeaderLabelHTML ( "Term" ) )
        self.accDiscrepFile.write ( html.getTableHeaderLabelHTML ( "Discrepancy" ) )
        self.accDiscrepFile.write ( html.getEndTableRowHTML () )

    def closeDiscrepancyFiles ( self ):
        # Purpose: writes HTML tags to close the table and document tags
        #          and physically closes discrepancy file
        # Returns: nothing
        # Assumes: discrepancy file is open
        # Effects: discrepancy files are closed
        # Throws:  propagates all exceptions closing files

        # write html tags to end the table and html document
        self.accDiscrepFile.write ( html.getEndTableHTML () )
        self.accDiscrepFile.write ( html.getEndHTMLDocumentHTML ( ) )

        # now, close the file
        self.accDiscrepFile.close ()


    def closeBCPFiles ( self ):
        # Purpose: closes BCP files
        # Returns: nothing
        # Assumes: BCP files are open
        # Effects: bcp files are closed
        # Throws:  propagates all exceptions closing files

        self.termTermBCPFile.close()    
        self.termTextBCPFile.close()    
        self.termSynonymBCPFile.close() 
        self.accAccessionBCPFile.close() 

    def loadBCPFiles (self):
        # Purpose: if the load flags are set, calls vocloadlib
        #          which in turn loads the BCP files
        # Returns: nothing
        # Assumes: bcp is in the path
        # Effects: database is loaded
        # Throws:  propagates all bcp exceptions

        bcpLogFile   = self.config.getConstant('BCP_LOG_FILE')
        bcpErrorFile = self.config.getConstant('BCP_ERROR_FILE')

        if not vocloadlib.NO_LOAD:
           if self.loadTermBCP:
              vocloadlib.loadBCPFile ( self.termTermBCPFileName    , bcpLogFile, bcpErrorFile, 'VOC_Term', self.passwordFile )
                                                                   
           if self.loadTextBCP:                                    
              vocloadlib.loadBCPFile ( self.termTextBCPFileName    , bcpLogFile, bcpErrorFile, 'VOC_Text', self.passwordFile )
                                                                   
           if self.loadSynonymBCP:                                 
              vocloadlib.loadBCPFile ( self.termSynonymBCPFileName , bcpLogFile, bcpErrorFile, 'VOC_Synonym', self.passwordFile )
                                                                   
           if self.loadAccessionBCP:                               
              vocloadlib.loadBCPFile ( self.accAccessionBCPFileName, bcpLogFile, bcpErrorFile, 'ACC_Accession', self.passwordFile )

    
    def goFull (self):
        # Purpose: does a full load for this vocabulary in the
        #   database (delete existing records and completely
        #   reload)
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: for this vocabulary, deletes all term records, with
        #   their associated text fields and synonyms, and reloads
        #   them
        # Throws: propagates all exceptions

        self.log.writeline (vocloadlib.timestamp (
            'Full Term Load Start:'))

        # open the bcp files if using bcp
        if self.isBCPLoad:
            self.openBCPFiles()

        # delete the existing terms, and report how many were deleted.
        count = vocloadlib.countTerms (self.vocab_key)
        vocloadlib.deleteVocabTerms (self.vocab_key, self.log)
        self.log.writeline ('   deleted all (%d) remaining terms' % \
            count)

        # look up the maximum keys for remaining items in VOC_Term
        # and VOC_Synonym.  We use the max() function to initialize
        # to 0 if the call to getMax() returns None.

        self.max_term_key = max (0, vocloadlib.getMax ('_Term_key',
            'VOC_Term'))
        self.max_synonym_key = max (0, vocloadlib.getMax (
            '_Synonym_key', 'VOC_Synonym'))

        # if this is a simple vocabulary, we provide sequence numbers
        # for the terms.  if it isn't simple, the sequence number is
        # null.

        if self.isSimple:
            termSeqNum = 0
        else:
            termSeqNum = 'null'

        # each record in the data file should be added as a new term:
         
        # open up a transaction if not loading via bcp
        if not self.isBCPLoad:
           vocloadlib.beginTransaction ( self.log )

        for record in self.datafile:
            if record['accID'] != GO_ROOT_ID:
               # Check for duplication on the primary term
               # Need to decide how to exit if this returns a dupe!!!!!
               duplicate = self.checkForDuplication ( record['accID'], record['term'], "Primary", self.getIsObsolete ( record['status'] ) )
               if duplicate:
                   self.commitTransaction = 0
            if self.isSimple:
               termSeqNum = termSeqNum + 1
            self.addTerm (record, termSeqNum)
            self.addSecondaryTerms ( record, self.max_term_key )

        # if we're running as no-load, we need to pass the ID to key
        # mapping to vocloadlib in case the DAG load needs it

        if vocloadlib.isNoLoad():
            vocloadlib.setTermIDs (self.id2key)

        # if commitTransaction == 1, either BCP in the data
        # or commit the transaction; otherwise, rollback
        # the transaction (or don't load BCP files)
        if self.commitTransaction:
           if self.isBCPLoad:
              self.closeBCPFiles()
              self.loadBCPFiles()
           else:
              vocloadlib.commitTransaction ( self.log )
        else:
           if not self.isBCPLoad:
              vocloadlib.rollbackTransaction ( self.log )

        self.log.writeline (vocloadlib.timestamp (
            'Full Term Load Stop:'))

        return

    def addTerm (self,
        record,     # dictionary of fieldname -> value pairs
        termSeqNum  # integer sequence number for a simple vocab's
                #   term, or the string 'null' for complex
                #   vocabularies
        ):
        # Purpose: add info for the term in 'record' to the database
        #   with the given sequence number
        # Returns: nothing
        # Assumes: nothing
        # Effects: adds a record to VOC_Term and records to
        #   VOC_Synonym and VOC_Text as needed
        # Throws: propagates all exceptions
        # Notes: 'record' must contain values for the following
        #   fieldnames- term, abbreviation, status, definition,
        #   synonyms, accID, otherIDs

        self.max_term_key = self.max_term_key + 1
        #self.log.writeline ('------ Term: %s ------' % record['term'])

        # add record to VOC_Term:
        if self.isBCPLoad:
           self.loadTermBCP = 1
           self.termTermBCPFile.write (BCP_INSERT_TERM % \
                                      (self.max_term_key,
                                      self.vocab_key,
                                      record['term'],
                                      record['abbreviation'],
                                      vocloadlib.setNull ( termSeqNum ),
                                      self.getIsObsolete( record['status'] ) ) )
        else: # asserts self.isIncrementalLoad() or full load with on-line sql:
           vocloadlib.nl_sqlog (INSERT_TERM % \
                       (self.max_term_key,
                       self.vocab_key,
                       vocloadlib.escapeDoubleQuotes (
                       record['term']),
                       vocloadlib.escapeDoubleQuotes (
                       record['abbreviation']),
                       termSeqNum,
                       self.getIsObsolete( record['status'] ) ),
                       self.log)




        # add records as needed to VOC_Text:
        self.generateDefinitionSQL ( record['definition'], self.max_term_key )

        # add records as needed to VOC_Synonym:
        synonyms = string.split (record['synonyms'], SYNONYM_DELIMITER )
        self.generateSynonymSQL( synonyms, self.max_term_key )

        # We can add non-MGI accession numbers to the ACC_Accession
        # table.  For MGI accession numbers, we do not add them.
        # (MGI accession numbers are added by a trigger when we add
        # to VOC_Term, if the _LogicalDB_key for the vocabulary is 1)
        # We assume that the 'otherIDs' come from the same logical
        # database as the primary 'accID', probably due to merges
        # occurring.

        # note that we look up the maximum accession key here, as the
        # addition to VOC_Term may have caused a trigger to add a new
        # MGI number for the term.  We use the max() function to start
        # at 0 in the event that getMax() returns None.  Note also
        # that we only do this if the program is performing on-line
        # updates.
        if not self.isBCPLoad:
           self.max_accession_key = max (0, vocloadlib.getMax (
               '_Accession_key', 'ACC_Accession'))

        # add the primary ID, if there is one.  If the logical DB is
        # non-MGI, then it is the preferred ID.

        if record['accID']:
            self.addAccID (record['accID'], self.max_term_key, self.logicalDBkey > 1)
            self.id2key[record['accID']] = self.max_term_key

        return


    def addSecondaryTerms (self,
        record,     # dictionary of input file fieldname -> value pairs
        associatedTermKey # primary term key associated with the secondary ID
        ):
        # Purpose: add secondary ids for the term in 'record' 
        #   to the database
        # Returns: nothing
        # Assumes: nothing
        # Effects: makes call to addAccID (to add record to ACC_Accession)
        # Throws: propagates all exceptions
        # Notes: 'record' must contain values (or None) for the following
        #   fieldnames- term, abbreviation, status, definition,
        #   synonyms, accID, otherIDs

        otherIDs = string.strip (record['otherIDs'])
        # add the secondary IDs, if there are any:
        if otherIDs:
            for id in string.split (otherIDs, OTHER_ID_DELIMITER):
                # now check for duplication on secondary terms
                duplicate = self.checkForDuplication ( id, record['term'], "Secondary", 0 )
                if duplicate:
                    self.commitTransaction = 0
                self.addAccID (string.strip ( id ), associatedTermKey )



    def generateDefinitionSQL ( self, definitionRecord, termKey ):
       # Purpose: generates SQL/BCP chunks for VOC_Text table (must be max size 255)
       # Returns: nothing
       # Assumes: nothing
       # Effects: adds records to VOC_Text in the database
       # Throws: propagates any exceptions raised by vocloadlib's
       #   nl_sqlog() function
       defSeqNum = 0   # sequence number for definition chunks
       for chunk in vocloadlib.splitBySize( definitionRecord, 255 ):
           defSeqNum = defSeqNum + 1
           if self.isBCPLoad:
              self.loadTextBCP = 1
              self.termTextBCPFile.write (BCP_INSERT_TEXT % \
                                          (termKey,
                                           defSeqNum,
                                           chunk))

           else: # asserts self.isIncrementalLoad() or full load with on-line sql:
              vocloadlib.nl_sqlog (INSERT_TEXT % \
                      (termKey,
                      defSeqNum,
                      vocloadlib.escapeDoubleQuotes(chunk)),
                      self.log)




    def addAccID (self,
        accID,      # string; accession ID to add
        associatedTermKey, #Term Key associated with the record being added
        preferred = 0   # boolean (0/1); is this the object's
                #   preferred ID?
        ):
        # Purpose: adds 'accID' as an accession ID for the currently
        #   loading term.
        # Returns: nothing
        # Assumes: called only by self.addTerm()
        # Effects: adds a record to ACC_Accession in the database
        # Throws: propagates any exceptions raised by vocloadlib's
        #   nl_sqlog() function

        self.max_accession_key = self.max_accession_key + 1
        prefixPart, numericPart = accessionlib.split_accnum (accID)

        if self.isBCPLoad:
           self.loadAccessionBCP = 1
           self.accAccessionBCPFile.write (BCP_INSERT_ACCESSION % \
                                          (self.max_accession_key, 
                                          accID,
                                          prefixPart,
                                          numericPart,
                                          self.logicalDBkey,
                                          associatedTermKey,
                                          self.mgitype_key,
                                          self.isPrivate,
                                          preferred) )
        else: # asserts self.isIncrementalLoad() or full load with on-line sql:
           vocloadlib.nl_sqlog (INSERT_ACCESSION % \
                   (self.max_accession_key, 
                   accID,
                   prefixPart,
                   numericPart,
                   self.logicalDBkey,
                   associatedTermKey,
                   self.mgitype_key,
                   self.isPrivate,
                   preferred),
                   self.log)

        return

    def goIncremental (self):
        # Purpose: placeholder method for when we do get around to
        #   implementing incremental loads
        # Returns: ?
        # Assumes: ?
        # Effects: ?
        # Throws: currently always throws error with a message
        #   stating that incremental loads have not been
        #   implemented.

        # Purpose: does an incremental load for this vocabulary in the
        #   database (comparing the input file to the database and
        #   accounting for differences only)
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: updates the database with data that is new or has
        #          changed since the last load
        # Throws: propagates all exceptions

        self.log.writeline (vocloadlib.timestamp (
            'Incremental Term Load Start:'))

        # look up the maximum keys for remaining items in VOC_Term
        # and VOC_Synonym.  We use the max() function to initialize
        # to 0 if the call to getMax() returns None.
        self.max_term_key = max (0, vocloadlib.getMax ('_Term_key',
            'VOC_Term'))
        self.max_synonym_key = max (0, vocloadlib.getMax (
            '_Synonym_key', 'VOC_Synonym'))

        # if this is a simple vocabulary, we provide sequence numbers
        # for the terms.  if it isn't simple, the sequence number is
        # null.
        if self.isSimple:
            termSeqNum = max (0, vocloadlib.getMax ('sequenceNum',
            'VOC_Term where _Vocab_key = %d') % self.vocab_key )
        else:
            termSeqNum = 'null'

        # set annotation type key - this will be used for merging changes
        self.ANNOT_TYPE_KEY = self.config.getConstant('ANNOT_TYPE_KEY')

        # get the existing Accession IDs/Terms from the database
        # all at once
        print "Getting Accession IDs..."
        primaryTermIDs = vocloadlib.getTermIDs ( self.vocab_key )
        secondaryTermIDs = vocloadlib.getSecondaryTermIDs ( self.vocab_key )

        #get the existing terms for the database
        print "Getting Existing Vocabulary Terms..."
        recordSet = vocloadlib.getTerms (  self.vocab_key )
        # process data file
        vocloadlib.beginTransaction ( self.log )
        for record in self.datafile:
            if record['accID'] != GO_ROOT_ID:
                # Check for duplication on the primary term - primary accIDs
                # may not refer to more than one term
                duplicate = self.checkForDuplication ( record['accID'], record['term'], "Primary", self.getIsObsolete ( record['status'] ) )
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
            if primaryTermIDs.has_key ( record['accID'] ):
               [termKey, isObsolete] = primaryTermIDs[record['accID'] ]
               dbRecord = recordSet.find ( '_Term_key', termKey )
               if dbRecord == []:
                  raise error, 'Accession ID in ACC_Accession does not exist \
                                in VOC Tables for _Object/_Term_Key: "%d"' % termKey
               else:
                  # Existing record found in VOC tables.  Now check
                  # if record changed
                  recordChanged = self.processRecordChanges ( record, dbRecord, termKey )
                  self.processSecondaryTerms ( record, primaryTermIDs, secondaryTermIDs, termKey )
            else: #New term
               # in this case, perform full load
               if self.isSimple:
                  termSeqNum = termSeqNum + 1
               self.addTerm (record, termSeqNum)
               self.processSecondaryTerms ( record, primaryTermIDs, secondaryTermIDs, self.max_term_key )
        if self.commitTransaction:
           vocloadlib.commitTransaction ( self.log )
        else:
           vocloadlib.rollbackTransaction ( self.log )
        return

    def checkForDuplication (self, accID, term, termType, isObsolete ):
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

        # only check if using actual accession ids (mgi ids will be blank in 
        # the Termfile)
        if self.LOGICALDB_KEY != MGI_LOGICALDB_KEY:
           # the primaryAccIDFileList and secondaryAccIDFileList are simply individual
           # lists of accIDs contained in the input file; if duplicates are found
           # either within a list or across both lists, the record is a potential 
           # duplicate
           if self.primaryAccIDFileList.has_key ( accID ) or self.secondaryAccIDFileList.contains ( accID ):
              if termType == SECONDARY:
                 # if it is a secondary term that is also an obsolete primary term
                 # it is permissible for it to appear on the list
                 # otherwise it is a duplicate
                 if self.primaryAccIDFileList.has_key ( accID ):
                     isObsolete = self.primaryAccIDFileList[accID]
                     if isObsolete == 0:
                        self.writeDiscrepancyFile ( accID, term, PRIMARY_SECONDARY_COLLISION_MSG )  
                        duplicate = 1
                 else: #accID already appears in secondary list
                    self.writeDiscrepancyFile ( accID, term, PRIMARY_SECONDARY_COLLISION_MSG )  
                    duplicate = 1
              else: #duplicate primary term
                 self.writeDiscrepancyFile ( accID, term, PRIMARY_SECONDARY_COLLISION_MSG )  
                 duplicate = 1
           else: #new term - add to list
              if termType == PRIMARY:
                 self.primaryAccIDFileList[accID] = isObsolete
              else:
                 self.secondaryAccIDFileList.add ( accID )
        return duplicate

    def writeDiscrepancyFile (self, accID, term, msg ):
        # Purpose: write a record to the discrepancy file
        # Returns: nothing
        # Assumes: discrepancy file is open and writeable
        # Effects: report output
        # Throws:  propagates any exceptions raised 
        self.accDiscrepFile.write ( html.getStartTableRowHTML () )
        self.accDiscrepFile.write ( html.getCellHTML ( accID ) )
        self.accDiscrepFile.write ( html.getCellHTML ( term  ) )
        self.accDiscrepFile.write ( html.getCellHTML ( msg   ) )
        self.accDiscrepFile.write ( html.getEndTableRowHTML () )


    def processSecondaryTerms (self, record, primaryTermIDs, secondaryTermIDs, associatedTermKey ):
        # Purpose: Determines if input records need to be merged with other terms
        #          and if secondary terms should be added to the accession table
        #          and does so as necessary
        # Returns: noting
        # Assumes: getTermsIDs only gets Term IDs with the prefered bit set to '1'
        #          i.e., true, because records are only eligible to be merged
        #          if they are primary IDs
        # Effects: Terms are merged and new accession records are added as necessary
        # Throws:  propagates any exceptions raised 
        otherIDs = string.strip (record['otherIDs'])
        if otherIDs:
            for id in string.split (otherIDs, OTHER_ID_DELIMITER ):
                id = string.strip ( id )
                # Check to see if secondary term is a duplicated
                duplicate = self.checkForDuplication ( id, record['term'], "Secondary", 0 )
                if duplicate:
                    self.commitTransaction = 0

                if primaryTermIDs.has_key ( id ) and not duplicate:
                    # If the secondary term is in the primaryTermIDs 
                    # structure of existing database records, that means
                    # that the prefered bit is set to true in mgd 
                    # and we therefore need to execute a merge
                    # but only if the primary term is NOT obsolete
                    [termKey, isObsolete] = primaryTermIDs[id]
                    if not isObsolete:
                       oldKey = termKey
                       newKey = associatedTermKey
                       vocloadlib.nl_sqlog ( ( MERGE_TERMS % (oldKey, newKey) ), self.log )
                else:
                    # check to see if secondary id already exists in database;
                    # if not, add it to accession table
                    if not secondaryTermIDs.has_key ( id ):
                       # The secondary term doesn't exist, so add the term to the
                       # database and point it to the primary term
                       if not self.isBCPLoad:
                          self.max_accession_key = max (0, vocloadlib.getMax (
                              '_Accession_key', 'ACC_Accession'))
                       self.addAccID ( id, associatedTermKey, 0 )

        return

    def processRecordChanges (self, record, dbRecord, termKey ):
       # Purpose: Check to see if input file record is different from the database
       #          in terms of the definition, the synonyms, the 
       #          isObsolete field, and the term field.  Writes a 
       #          record to the Curator/Discrepancy Report if there are definition
       #          differences or the record has been obsoleted AND there
       #          have been annotations against the record
       # Returns: 1 - true, record has changed, or 0 - false, record has not changed
       # Assumes: Database records for the Term have been retrieved into the dbRecord structure
       # Effects: Executes deletes/inserts into the VOC_Text table
       #          Executes deletes/inserts into the VOC_Synonym table
       #          Executes updates to the term table (status and terms fields);
       #          note that, for efficiency, both the status and term fields
       #          are updated if either or both fields have to be updated
       # Throws:  propagates any exceptions raised 
       recordChanged = 0
       ###########################################################################
       # Check definition#########################################################
       ###########################################################################
       definitionDescrepancy = obsoleteTermDiscrepancy = 0
       #Get dbRecord in sync with file record by converting "None" to blank
       dbDefinition = dbRecord[0]['notes']
       if dbDefinition == None:
          dbDefinition = ""
       if ( string.strip ( record['definition'] ) != string.strip ( dbDefinition ) ):
          # can't do simple update because of 255 size limit; therefore, do a delete
          # and insert
          vocloadlib.nl_sqlog ( DELETE_TEXT % termKey, self.log )
          self.generateDefinitionSQL( record['definition'], termKey )
          recordChanged = 1

          # Now write report record if the DB record is not null or blank
          # and the term has annotations associated with it
          if dbRecord[0]['notes'] > 0:
             definitionDescrepancy = 1

       ###########################################################################
       # Check synonyms###########################################################
       ###########################################################################
       fileSynonyms = string.split (record['synonyms'], SYNONYM_DELIMITER )
       if fileSynonyms == ['']:
           fileSynonyms = []
       dbSynonyms = dbRecord[0]['synonyms']

       # make sure synonyms are in the same order
       dbSynonyms.sort()
       fileSynonyms.sort()

       if ( fileSynonyms != dbSynonyms ):
          # if there are any differences between the file and
          # the database, simply delete all existing synonyms
          # and reinsert them
          vocloadlib.nl_sqlog ( DELETE_ALL_SYNONYMS % termKey, self.log )
          self.generateSynonymSQL ( fileSynonyms, termKey )
          recordChanged = 1

       ###########################################################################
       # Finally, check term and status###########################################
       ###########################################################################
       fileIsObsoleteField = self.getIsObsolete ( record['status'] )
       if ( record['term'] != dbRecord[0]['term'] ) or \
          ( fileIsObsoleteField != dbRecord[0]['isObsolete'] ):
          # If either (or both) of the fields change, it's simpler and probably more
          # efficient to just update both fields in 1 statement
          vocloadlib.nl_sqlog ( UPDATE_TERM % ( record['term'], fileIsObsoleteField, termKey ), self.log )
          recordChanged = 1

          # Now write report record if the term is obsoleted 
          # and the term has annotations associated with it
          if ( fileIsObsoleteField != dbRecord[0]['isObsolete'] ):
             obsoleteTermDiscrepancy = 1

       ###########################################################################
       # Now write report discrepancy record(s) if necessary######################
       ###########################################################################
       if ( definitionDescrepancy or obsoleteTermDiscrepancy ):
          annotations = vocloadlib.getAnyTermsCrossReferenced ( termKey, self.ANNOT_TYPE_KEY )
          # only write record if annotations exist
          if len ( annotations ) >= 1:
             symbols = ""
             for annotation in annotations: #build list of symbols
                symbols = symbols + " " + annotation['symbol']
             if definitionDescrepancy:
                msg = "Definition change for Term with annotations.  Old Definition: %s, New Definition: %s, Symbols: %s" % ( dbRecord[0]['notes'], record['definition'], symbols ) 
                self.writeDiscrepancyFile ( record['accID'], record['term'], msg )  
             if obsoleteTermDiscrepancy:
                msg = "Term has been obsoleted but has annotations, Symbols: %s" % ( symbols ) 
                self.writeDiscrepancyFile ( record['accID'], record['term'], msg )  

       return recordChanged
    
    def generateSynonymSQL (self, fileSynonyms, termKey ):
       # Purpose: add records as needed to VOC_Synonym table
       # Returns: nothing
       # Assumes: open database connection or bcp file
       # Effects: inserts via online sql or bcp into the
       #          VOC_Synonym table
       # Throws:  propagates any exceptions raised 
       for synonym in fileSynonyms:
          if synonym:
             self.max_synonym_key = self.max_synonym_key +1
             if self.isBCPLoad:
                self.loadSynonymBCP = 1
                self.termSynonymBCPFile.write (BCP_INSERT_SYNONYM % \
                       (self.max_synonym_key,
                        termKey,
                        vocloadlib.escapeDoubleQuotes(synonym)) )
             else: # asserts self.isIncrementalLoad() or full load with on-line sql:
                vocloadlib.nl_sqlog (INSERT_SYNONYM % \
                       (self.max_synonym_key,
                        termKey,
                        vocloadlib.escapeDoubleQuotes(synonym)),self.log)

    def getIsObsolete ( self, recordStatus ):
       # Purpose: Returns an isObsolete bit based on the record status
       # Returns: 1 - record is obsolete, 0 - record is not obsolete
       # Assumes: recordStatus is 'obsolete' or 'current'
       # Effects: nothing
       # Throws:  propagates any exceptions raised
       return recordStatus == 'obsolete'

    def isIncrementalLoad ( self ):
       # Purpose: Returns an isIncremental bit based on the self.mode
       # Returns: 1 - load is incremental, 0 - load is full
       # Assumes: mode is 'full' or 'incremental'
       # Effects: nothing
       # Throws:  propagates any exceptions raised
       return self.mode == 'incremental'

    def setFullModeDataLoader ( self ):
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
       fullModeDataLoader = self.config.getConstant('FULL_MODE_DATA_LOADER')
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
           raise error, unknown_data_loader % fullModeDataLoader

###--- Main Program ---###

# needs to be rewritten to get configuration from an rcd file

if __name__ == '__main__':
    try:
        options, args = getopt.getopt (sys.argv[1:], 'finl:')
    except getopt.error:
        print 'Error: Unknown command-line options/args'
        print USAGE
        sys.exit(1)

    if len(args) != 6:
        print 'Error: Wrong number of arguments'
        print USAGE
        sys.exit(1)

    mode = 'full'
    log = Log.Log()
    [ server, database, username, password ] = args[:4]
    [ vocab_key, input_file ] = args[4:]
    vocab_key = string.atoi(vocab_key)

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
            log = Log.Log (filename = value)

    if noload:
        log.writeline ('Operating in NO-LOAD mode')

    vocloadlib.setupSql (server, database, username, password)
    load = TermLoad (input_file, mode, vocab_key, log)
    load.go()
