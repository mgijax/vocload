#!/usr/local/bin/python

# Program: loadVOC.py
# Purpose: do a vocabulary load.  This includes terms for a simple vocabulary
#   and the terms and DAG structure for complex vocabularies.
# User Requirements Satisfied by This Program:
# System Requirements Satisfied by This Program:
#   Usage: see USAGE below
#   Uses:
#   Envvars:
#   Inputs:
#   Outputs:
#   Exit Codes:
#   Other System Requirements:
# Assumes:
# Implementation:
#   Modules:

import sys      # standard Python libraries
import string

import vocloadlib   # MGI-written Python libraries
import loadDAG
import loadTerms

###--- Exceptions ---###

error = 'VOCLoad.error'     # exception raised with values:

unknown_mode = 'unknown load mode: %s'
bad_simple = 'mismatching isSimple value for vocab key %d'
unknown_jnum = 'cannot find _Refs_key for jnum %s'
unknown_vocab = 'cannot find _Vocab_key for vocab "%s"'

###--- SQL INSERT Statements ---###

    # We define these template here to aid reability of the code.  They
    # are formatted to increase readability of the log file.

INSERT_VOCAB = '''insert VOC_Vocab (_Vocab_key, _Refs_key, isSimple, isPrivate,
        _LogicalDB_key, name)
    values (%d, %d, %d, %d, %d, "%s")'''

INSERT_DAG = '''insert DAG_DAG (_DAG_key, _Refs_key, _MGIType_key,
        abbreviation, name)
    values (%d, %d, %d,
        "%s", "%s")'''

INSERT_VOCABDAG = 'insert VOC_VocabDAG (_Vocab_key, _DAG_key) values (%d, %d)'

###--- Classes ---###

class VOCLoad:
    # IS: a vocabulary load, including sub-loads for a set of terms and
    #   possibly a DAG structure
    # HAS: a log, an RcdFile configuration, a file of terms, a mode (full
    #   or incremental), and other attributes of the vocabulary
    # DOES: loads a set of terms and (for complex vocabularies) a DAG
    #   structure for them

    def __init__ (self,
        config,     # RcdFile for info about config, vocab, dags
        mode,       # string; do a 'full' or 'incremental' load?
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
        self.termfile = config.getConstant('TERM_FILE')

        if mode in [ 'full', 'incremental' ]:
            self.mode = mode
        else:
            raise error, unknown_mode % mode

        try:
            self.server = config.getConstant('DBSERVER')
            self.database = config.getConstant('DATABASE')
            self.username = config.getConstant('DBUSER')
            self.passwordFile = open ( config.getConstant('DBPASSWORD_FILE'), 'r' )
            self.password = string.strip ( self.passwordFile.readline() )

            vocloadlib.setupSql (self.server, self.database,
                self.username, self.password)
            vocloadlib.sql ('select count(1) from VOC_Vocab')
        except:
            raise error, 'failed SQL initialization: %s' % \
                sys.exc_value

        self.vocab_name = config.getConstant('VOCAB_NAME')
        self.isSimple = string.atoi(config.getConstant('IS_SIMPLE'))
        self.isPrivate = string.atoi(config.getConstant('IS_PRIVATE'))
        self.logicalDBkey = string.atoi(config.getConstant(
            'LOGICALDB_KEY'))
        self.mgitype_key = string.atoi(config.getConstant('MGITYPE'))

        vocloadlib.setVocabMGITypeKey (self.mgitype_key)

        results = vocloadlib.sql (
            '''select _Vocab_key, isSimple
                from VOC_Vocab
                where name = "%s"''' % self.vocab_name
                )
        if len(results) > 0:
            self.vocab_key = results[0]['_Vocab_key']
            if results[0]['isSimple'] != self.isSimple:
                raise error, bad_simple % self.vocab_key
        else:
            self.vocab_key = None

        self.jnum = config.getConstant('JNUM')

        result = vocloadlib.sql ('''select _Refs_key
                    from BIB_View
                    where jnumID = "%s"''' % self.jnum)
        if len(result) == 0:
            raise error, unknown_jnum % self.jnum
        self.refs_key = result[0]['_Refs_key']
        return

    def go (self):
        self.goFull()
        return

    def real_go (self):
        try:
            if self.mode == 'full':
                self.goFull()
            else:
                self.goIncremental()
        except:
            raise error, sys.exc_value
        return

    def goFull (self):
        self.log.writeline (vocloadlib.timestamp (
            'Full VOC Load Start:'))

        if self.vocab_key:
            dags = vocloadlib.sql ('''select _DAG_key
                        from VOC_VocabDAG
                        where _Vocab_key = %d''' % \
                        self.vocab_key)
            for dag in dags:
                vocloadlib.truncateTransactionLog (
                    self.database, self.log)
                # deleting from DAG_DAG should cascade to other tables
                # TAKE OUT !!! vocloadlib.deleteDagComponents (
                    # dag['_DAG_key'], self.log)
                vocloadlib.nl_sqlog ( 'delete from DAG_DAG where _DAG_key = %d' % dag['_DAG_key'], self.log )

            vocloadlib.truncateTransactionLog (
                self.database, self.log)
            vocloadlib.deleteVocabTerms (self.vocab_key, self.log)
            vocloadlib.nl_sqlog ('''delete from VOC_Vocab
                    where _Vocab_key = %d''' % \
                    self.vocab_key,
                self.log)
        else:
            result = vocloadlib.sql ('''select max(_Vocab_key)
                    from VOC_Vocab''')
            self.vocab_key = max (0, result[0]['']) + 1

        vocloadlib.nl_sqlog (INSERT_VOCAB % (self.vocab_key,
            self.refs_key, self.isSimple, self.isPrivate,
            self.logicalDBkey, self.vocab_name),
            self.log)

        result = vocloadlib.sql ('select max(_DAG_key) from DAG_DAG')
        dag_key = max (0, result[0]['']) + 1

        for (key, dag) in self.config.items():
            vocloadlib.nl_sqlog (INSERT_DAG % (dag_key,
                self.refs_key, self.mgitype_key,
                dag['ABBREV'], dag['NAME']),
                self.log)
            vocloadlib.nl_sqlog (INSERT_VOCABDAG % (
                self.vocab_key, dag_key),
                self.log)

            dag['KEY'] = dag_key
            dag_key = dag_key + 1

        # load terms

        vocloadlib.truncateTransactionLog (self.database, self.log)
        termload = loadTerms.TermLoad (self.termfile, self.mode,
            self.vocab_key, self.log, self.config )
        termload.go()

        # load DAGs

        if not self.isSimple:
            for (key, dag) in self.config.items():
                vocloadlib.truncateTransactionLog (
                    self.database, self.log)
                dagload = loadDAG.DAGLoad (dag['LOAD_FILE'],
                    self.mode, dag['NAME'], self.log,
                                        self.config )
                dagload.go()

        self.log.writeline (vocloadlib.timestamp (
            'Full VOC Load Stop:'))
        return

    def goIncremental (self):
        if not self.vocab_key:
            raise error, unknown_vocab % self.vocab_name
        raise error, 'incremental load not yet implemented'
        return

###--- Main Program ---###

# needs to be rewritten:

if __name__ == '__main__':
    print "not currently runnable from the command-line"

#   import rcdlib
#   import Log
#   config = rcdlib.RcdFile ('voc.rcd', rcdlib.Rcd, 'NAME')
#   vocload = VOCLoad (config, 'full', Log.Log())
#   vocload.go()
