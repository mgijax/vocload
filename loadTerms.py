#!/usr/local/bin/python

# Program: loadTerms
# Purpose: to load the input file of vocabulary terms to database tables
#	VOC_Vocab, VOC_Term, VOC_Text, VOC_Synonym
# User Requirements Satisfied by This Program:
# System Requirements Satisfied by This Program:
#	Usage: see USAGE definition below
#	Uses:
#	Envvars:
#	Inputs:
#		1. tab-delimited input file in with the following columns:
#			Term (required)
#			Accession ID (optional)
#			Status (required - 'current' or 'obsolete')
#			Abbreviation (optional)
#			Definition (optional)
#			Synonyms (optional)
#			Secondary Accession IDs (optional)
#		2. mode (full or incremental)
#			'incremental' is not valid for simple vocabularies
#		3. primary key of Vocabulary being loaded
#			(why not the name?)
#	Outputs:
#	Exit Codes:
#		0. script completed successfully, data loaded okay
#		1. script halted, data did not load, error noted in stderr
#			(database is left in a consistent state)
#	Other System Requirements:
# Assumes:
#	We assume no other users are adding/modifying database records during
#	the run of this script.
# Implementation:
#	Modules:

import sys			# standard Python libraries
import types
import string
import getopt

USAGE = '''Usage: %s [-f|-i][-n][-l <file>] <server> <db> <user> <pwd> <key> <input>
	-f | -i	: full load or incremental load? (default is full)
	-n	: use no-load option (log changes, but don't execute them)
	-l	: name of the log file to create (default is stderr only)
	server	: name of the database server
	db	: name of the database
	user	: database login name
	pwd	: password for 'user'
	key	: _Vocab_key for which to load terms
	input	: term input file
''' % sys.argv[0]

import Log			# MGI-written Python libraries
import vocloadlib
import accessionlib

###--- Exceptions ---###

error = 'TermLoad.error'	# exception raised with these values:

unknown_mode = 'unknown load mode: %s'
full_only = 'simple vocabulary (%s) may only use mode "full"'
has_refs = 'cannot do a full load on vocab %s which has cross references'

###--- SQL INSERT Statements ---###

	# templates placed here for readability of the code and
	# formatted for readability of the log file

INSERT_TERM = '''insert VOC_Term (_Term_key, _Vocab_key, term,
		abbreviation, sequenceNum, isObsolete)
	values (%d, %d, "%s",
		"%s", %s, %d)'''

INSERT_TEXT = '''insert VOC_Text (_Term_key, sequenceNum, note)
	values (%d, %d, "%s")'''

INSERT_SYNONYM ='''insert VOC_Synonym (_Synonym_key, _Term_key, synonym)
	values (%d, %d, "%s")'''

INSERT_ACCESSION = '''insert ACC_Accession (_Accession_key, accID, prefixPart, numericPart,
		_LogicalDB_key, _Object_key, _MGIType_key, private, preferred)
	values (%d, "%s", "%s", %s,
		%d, %d, %d, %d, %d)'''

###--- Classes ---###

class TermLoad:
	# IS: a data load of vocabulary terms into the database
	# HAS: the following attributes, encompassing both the vocabulary
	#	and the load itself:
	#	vocab_key, vocab_name, isPrivate, isSimple, mode, filename,
	#	datafile, log, max_term_key, max_synonym_key,
	#	max_accession_key
	# DOES: reads from an input data file of term info to load it into
	#	the MGI database

	def __init__ (self,
		filename,	# string; path to input file of term info
		mode,		# string; do a 'full' or 'incremental' load?
		vocab,		# integer vocab key or string vocab name;
				#	which vocabulary to load terms for
		log		# Log.Log object; used for logging progress
		):
		# Purpose: constructor
		# Returns: nothing
		# Assumes: 'filename' is readable
		# Effects: instantiates the object, reads from 'filename'
		# Throws: 1. error if the 'mode' is invalid, if we try to
		#	do an incremental load on a simple vocabulary, or
		#	if try to do a full load on a vocabulary which has
		#	existing cross-references to its terms;
		#	2. propagates vocloadlib.error if we have problems
		#	getting vocab info from the database;
		#	3. propagates exceptions raised by vocloadlib's
		#	readTabFile() function

		# remember the log to which we'll need to write

		self.log = log

		# find vocab key and name (propagate vocloadlib.error if
		# invalid)

		if type(vocab) == types.StringType:
			self.vocab_name = vocab
			self.vocab_key = vocloadlib.getVocabKey (vocab)
		else:
			self.vocab_name = vocloadlib.getVocabName (vocab)
			self.vocab_key = vocab

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

		# validity checks...
		# 1. we cannot do incremental loads on simple vocabularies
		# 2. we cannot do full loads on vocabularies which are cross-
		#	referenced

		if self.isSimple and mode != 'full':
			raise error, full_only % vocab

		if mode == 'full' and vocloadlib.anyTermsCrossReferenced (
			self.vocab_key):
				raise error, has_refs % vocab

		# when we actually do the load, we'll look up the current
		# maximum keys for various tables...  For now, we'll just
		# initialize them to None

		self.max_term_key = None	# to be filled in once at the
		self.max_synonym_key = None	# start of the load

		self.max_accession_key = None	# to be filled in later for
						# each term (because MGI IDs
						# may be added by a trigger)

		# remember the filename and read the data file

		self.filename = filename
		self.datafile = vocloadlib.readTabFile (filename,
			[ 'term', 'accID', 'status', 'abbreviation',
			'definition', 'synonyms', 'otherIDs' ])

		self.mgitype_key = vocloadlib.VOCABULARY_TERM_TYPE

		self.log.writeline (vocloadlib.timestamp ('Init Stop:'))
		return

	def go (self):
		# Purpose: run the load
		# Returns: nothing
		# Assumes: see self.goFull() and self.goIncremental()
		# Effects: writes to self.log, runs the load and updates the
		#	database
		# Throws: propagates all exceptions from self.goFull() or
		#	self.goIncremental(), whichever is called

		if self.mode == 'full':
			self.goFull ()
		else:
			self.goIncremental ()
		self.log.writeline ('=' * 40)		# end of the load
		return

	def goFull (self):
		# Purpose: does a full load for this vocabulary in the
		#	database (delete existing records and completely
		#	reload)
		# Returns: nothing
		# Assumes: vocloadlib.setupSql() has been called appropriatley
		# Effects: for this vocabulary, deletes all term records, with
		#	their associated text fields and synonyms, and reloads
		#	them
		# Throws: propagates all exceptions

		self.log.writeline (vocloadlib.timestamp (
			'Full Term Load Start:'))

		# delete the existing terms, and report how many were deleted.

		count = vocloadlib.countTerms (self.vocab_key)
		vocloadlib.deleteVocabTerms (self.vocab_key, self.log)
		self.log.writeline ('	deleted all (%d) remaining terms' % \
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

		for record in self.datafile:
			if self.isSimple:
				termSeqNum = termSeqNum + 1
			self.addTerm (record, termSeqNum)

		self.log.writeline (vocloadlib.timestamp (
			'Full Term Load Stop:'))
		return

	def addTerm (self,
		record,		# dictionary of fieldname -> value pairs
		termSeqNum	# integer sequence number for a simple vocab's
				#	term, or the string 'null' for complex
				#	vocabularies
		):
		# Purpose: add info for the term in 'record' to the database
		#	with the given sequence number
		# Returns: nothing
		# Assumes: nothing
		# Effects: adds a record to VOC_Term and records to
		#	VOC_Synonym and VOC_Text as needed
		# Throws: propagates all exceptions
		# Notes: 'record' must contain values for the following
		#	fieldnames- term, abbreviation, status, definition,
		#	synonyms, accID, otherIDs

		self.max_term_key = self.max_term_key + 1
		self.log.writeline ('------ Term: %s ------' % record['term'])

		# add record to VOC_Term:

		vocloadlib.nl_sqlog (INSERT_TERM % \
					(self.max_term_key,
					self.vocab_key,
					vocloadlib.escapeDoubleQuotes (
						record['term']),
					vocloadlib.escapeDoubleQuotes (
						record['abbreviation']),
					termSeqNum,
					record['status'] == 'obsolete'),
				self.log)

		# add records as needed to VOC_Text:

		defSeqNum = 0	# sequence number for definition chunks
		for chunk in vocloadlib.splitBySize(record['definition'],255):
			defSeqNum = defSeqNum + 1
			vocloadlib.nl_sqlog (INSERT_TEXT % \
					(self.max_term_key,
					defSeqNum,
					vocloadlib.escapeDoubleQuotes(chunk)),
				self.log)

		# add records as needed to VOC_Synonym:

		synonyms = string.split (record['synonyms'], '|')
		for synonym in synonyms:
			if synonym:
				self.max_synonym_key = self.max_synonym_key +1
				vocloadlib.nl_sqlog (INSERT_SYNONYM % \
						(self.max_synonym_key,
						self.max_term_key,
						vocloadlib.escapeDoubleQuotes(
							synonym)),
					self.log)

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
		# at 0 in the event that getMax() returns None.

		self.max_accession_key = max (0, vocloadlib.getMax (
			'_Accession_key', 'ACC_Accession'))

		# add the primary ID, if there is one.  If the logical DB is
		# non-MGI, then it is the preferred ID.

		if record['accID']:
			self.addAccID (record['accID'], self.logicalDBkey > 1)

		# add the secondary IDs, if there are any:

		otherIDs = string.strip (record['otherIDs'])
		if otherIDs:
			for id in string.split (otherIDs, '|'):
				self.addAccID (id)
		return

	def addAccID (self,
		accID,		# string; accession ID to add
		preferred = 0	# boolean (0/1); is this the object's
				#	preferred ID?
		):
		# Purpose: adds 'accID' as an accession ID for the currently
		#	loading term.
		# Returns: nothing
		# Assumes: called only by self.addTerm()
		# Effects: adds a record to ACC_Accession in the database
		# Throws: propagates any exceptions raised by vocloadlib's
		#	nl_sqlog() function

		self.max_accession_key = self.max_accession_key + 1
		prefixPart, numericPart = accessionlib.split_accnum (accID)

		vocloadlib.nl_sqlog (INSERT_ACCESSION % \
				(self.max_accession_key, 
				accID,
				prefixPart,
				numericPart,
				self.logicalDBkey,
				self.max_term_key,
				self.mgitype_key,
				self.isPrivate,
				preferred),
			self.log)
		return

	def goIncremental (self):
		# Purpose: placeholder method for when we do get around to
		#	implementing incremental loads
		# Returns: ?
		# Assumes: ?
		# Effects: ?
		# Throws: currently always throws error with a message
		#	stating that incremental loads have not been
		#	implemented.

		raise error, 'Incremental loads for terms have not been implemented'
		return

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
