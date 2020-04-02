
#
# Program: loadVOC.py
#
# Purpose: do a vocabulary load.  This includes terms for a simple vocabulary
#   and the terms and DAG structure for complex vocabularies.
#
# User Requirements Satisfied by This Program:
#
# System Requirements Satisfied by This Program:
#   Usage: see USAGE below
#   Uses:
#   Envvars:
#   Inputs: Configuration file, mode (full or incremental), and a log file
#   Outputs:
#   Exit Codes: throws exception if unsuccessful
#   Other System Requirements:
#
# Assumes:
#   We assume no other users are adding/modifying database records during
#
# Implementation:
#   Modules:
#
# Modification History
#
#	03/26/2003	lec
#	- TR 3702 (InterPro); do not delete VOC_Vocab record during a full load.
#	A simple vocabulary may be associated with an Annotation Type (VOC_AnnotType).
#	For InterPro, the Annotations will be deleted, the IP Vocab will be reloaded,
#	and the Annotations will be reloaded.  However, we don't want to have to
#	re-create the Annotation Type record, because then the IP Annotation load.
#	

import sys      # standard Python libraries
import os
import vocloadlib   # MGI-written Python libraries
import loadDAG
import loadTerms
import db

###--- Exceptions ---###

error = 'VOCLoad.error'     # exception raised with values:

unknown_mode = 'unknown load mode: %s'
bad_simple = 'mismatching isSimple value for vocab key %d'
unknown_jnum = 'cannot find _Refs_key for jnum %s'
unknown_vocab = 'cannot find _Vocab_key for vocab \'%s\''

###--- SQL INSERT Statements ---###

# We define these template here to aid reability of the code.  They
# are formatted to increase readability of the log file.

INSERT_VOCAB = '''insert into VOC_Vocab (_Vocab_key, _Refs_key, isSimple, isPrivate, _LogicalDB_key, name)
    values (%d, %d, %d, %d, %d, '%s')
    '''

INSERT_DAG = '''insert into DAG_DAG (_DAG_key, _Refs_key, _MGIType_key, abbreviation, name)
    values (%d, %d, %d, '%s', '%s')
    '''

INSERT_VOCABDAG = 'insert into VOC_VocabDAG (_Vocab_key, _DAG_key) values (%d, %d)'

###--- Classes ---###

class VOCLoad:
    # IS: a vocabulary load, including sub-loads for a set of terms and
    #   possibly a DAG structure
    # HAS: a log, an RcdFile configuration, a file of terms, a mode (full
    #   or incremental), and other attributes of the vocabulary
    # DOES: loads a set of terms and (for complex vocabularies) a DAG
    #   structure for them

    def __init__ (self,
        config,     # RcdFile for info about dags
        mode,       # str. do a 'full' or 'incremental' load?
        log     # Log.Log object; where to do logging
        ):
        # Purpose: constructor
        # Returns: nothing
        # Assumes: nothing
        # Effects: initializes vocloadlib by calling setupSql(), sends
        #   a few queries to the database
        # Throws: error if the mode is unknown or if vocloadlib's SQL
        #   routines could not be initialized and tested
        #   successfully
        # Notes: (opt)
        # Example: (opt)

        self.log = log
        self.config = config
        self.termfile = os.environ['TERM_FILE']

        if mode in [ 'full', 'incremental' ]:
            self.mode = mode
        else:
            raise error(unknown_mode % mode)

        self.server = os.environ['DBSERVER']
        self.database = os.environ['DBNAME']
        self.username = os.environ['DBUSER']
        self.passwordFileName = os.environ['DBPASSWORDFILE']
        self.passwordFile = open ( self.passwordFileName, 'r' )
        self.password = str.strip ( self.passwordFile.readline() )

        vocloadlib.setupSql (self.server, self.database, self.username, self.password)
        # confirm the sql setup worked by doing simple query
        db.sql ('select count(1) from VOC_Vocab')

        self.vocab_name = os.environ['VOCAB_NAME']
        #self.isSimple = str.atoi(os.environ['IS_SIMPLE'])
        #self.isPrivate = str.atoi(os.environ['IS_PRIVATE'])
        #self.logicalDBkey = str.atoi(os.environ['LOGICALDB_KEY'])
        #self.mgitype_key = str.atoi(os.environ['MGITYPE'])
        self.isSimple = int(os.environ['IS_SIMPLE'])
        self.isPrivate = int(os.environ['IS_PRIVATE'])
        self.logicalDBkey = int(os.environ['LOGICALDB_KEY'])
        self.mgitype_key = int(os.environ['MGITYPE'])

        vocloadlib.setVocabMGITypeKey (self.mgitype_key)

        results = db.sql (
            '''select _Vocab_key, isSimple
                from VOC_Vocab
                where name = '%s' 
            ''' % self.vocab_name)
        if len(results) > 0:
            self.vocab_key = results[0]['_Vocab_key']
            if results[0]['isSimple'] != self.isSimple:
                raise error(bad_simple % self.vocab_key)
        else:
            self.vocab_key = None

        self.jnum = os.environ['JNUM']

        result = db.sql ('''select _Refs_key
                    from BIB_View
                    where jnumID = '%s' 
                    ''' % self.jnum)
        if len(result) == 0:
            raise error(unknown_jnum % self.jnum)
        self.refs_key = result[0]['_Refs_key']
        return

    def go (self):
        # Purpose: run the load in full or incremental mode
        # Returns: nothing
        # Assumes: see self.goFull() and self.goIncremental()
        # Effects: nothing
        # Throws: propagates all exceptions from self.goFull() or
        #   self.goIncremental(), whichever is called
         if self.mode == 'full':
             self.goFull()
         else:
             self.goIncremental()
         vocloadlib.unsetupSql()
         return

    def goFull (self):
        # Purpose: controls the processing of performing full
        #   loads of a vocabulary and, in the cases of complex
        #   vocabulary, a DAG structure
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: prepares the database for a full load by deleting
        #   all existing vocabulary and DAG structures as applicable,
        #   loading the VOC_Vocab, DAG_DAG, and VOC_VocabDAG
        #   tables, and instantiating and executing the TermLoad
        #   and DAGLoad objects.
        # Throws: propagates all exceptions
        self.log.writeline (vocloadlib.timestamp (
            'Full VOC Load Start:'))

        # Only delete data if it currently exists in the database
        if self.vocab_key:
            dags = db.sql ('''select _DAG_key
                        from VOC_VocabDAG
                        where _Vocab_key = %d
                        ''' % self.vocab_key)
            for dag in dags:
                vocloadlib.nl_sqlog ( 'delete from DAG_DAG where _DAG_key = %d' % dag['_DAG_key'], self.log )

            vocloadlib.deleteVocabTerms (self.vocab_key, self.log)

            # don't delete the master VOC_Vocab record; a simple vocab may be used 
            # in an VOC_AnnotType record.  for example, InterPro; the annotations get deleted;
            # the vocabulary gets a full reload; the annotations get re-added;
            # but the Annotation Type record still needs to exist.

#            vocloadlib.nl_sqlog ('''delete from VOC_Vocab
#                    where _Vocab_key = %d''' % \
#                    self.vocab_key,
#                self.log)
        else:
            #insert into VOC_Vocab table only if a record does not already exist

            result = db.sql ('''select max(_Vocab_key) as maxkey from VOC_Vocab''')
            self.vocab_key = max (0, result[0]['maxkey']) + 1

            vocloadlib.nl_sqlog (INSERT_VOCAB % (self.vocab_key,
                    self.refs_key, self.isSimple, self.isPrivate,
                    self.logicalDBkey, self.vocab_name),
                    self.log)

        # load the terms

        termload = loadTerms.TermLoad (self.termfile, self.mode, self.vocab_key, self.refs_key, self.log, self.passwordFileName )
        termload.go()

        # load the DAGs if it is a complex vocabulary

        if not self.isSimple:
            result = db.sql ('select max(_DAG_key) as maxkey from DAG_DAG')
            dag_key = max (0, result[0]['maxkey']) + 1

            for (key, dag) in list(self.config.items()):

                #insert into DAG_DAG table
                vocloadlib.nl_sqlog (INSERT_DAG % (dag_key, self.refs_key, self.mgitype_key, 
                        dag['ABBREV'], dag['NAME']), self.log)

                #insert into VOC_VocabDag table
                vocloadlib.nl_sqlog (INSERT_VOCABDAG % (self.vocab_key, dag_key), self.log)

                dag['KEY'] = dag_key
                dag_key = dag_key + 1

        if not self.isSimple:
            for (key, dag) in list(self.config.items()):
                dagload = loadDAG.DAGLoad (dag['LOAD_FILE'], self.mode, dag['NAME'], self.log, self.passwordFileName )
                dagload.go()

        self.log.writeline (vocloadlib.timestamp (
            'Full VOC Load Stop:'))
        return

    def goIncremental (self):
        # Purpose: controls the processing of performing incremental
        #   loads of a vocabulary and, in the cases of complex
        #   vocabulary, a DAG structure.
        # Returns: nothing
        # Assumes: vocloadlib.setupSql() has been called appropriatley
        # Effects: Instantiates and executes the TermLoad
        #   and DAGLoad objects.
        # Throws: propagates all exceptions

        self.log.writeline (vocloadlib.timestamp (
            'Incremental VOC Load Start:'))

        if not self.vocab_key:
            raise error(unknown_vocab % self.vocab_name)

        # Now load the terms
        termload = loadTerms.TermLoad (self.termfile, self.mode,
            self.vocab_key, self.refs_key, self.log, self.passwordFileName )
        termload.go()

        # load DAGs
        if not self.isSimple:
            for (key, dag) in list(self.config.items()):
                dagload = loadDAG.DAGLoad (dag['LOAD_FILE'],
                    self.mode, dag['NAME'], self.log, self.passwordFileName )
                dagload.go()

        self.log.writeline (vocloadlib.timestamp (
            'Incremental VOC Load Stop:'))

        return

###--- Main Program ---###

# needs to be rewritten:

if __name__ == '__main__':
    print("not currently runnable from the command-line")

#   import rcdlib
#   import Log
#   config = rcdlib.RcdFile ('voc.rcd', rcdlib.Rcd, 'NAME')
#   vocload = VOCLoad (config, 'full', Log.Log())
#   vocload.go()
