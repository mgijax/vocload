#!/usr/local/bin/python

# Name: vocloadlib.py
# Purpose: provides standard functions for use throughout the vocabulary load
#	product (including the DAG load as well)
# On Import: Following the importation of this module, you should make sure
#	to call the setupSql() function to ensure you're looking at the right
#	database.

import sys		# standard Python modules
import time
import types
import regsub

import db		# MGI-written Python modules

###--- Exceptions ---###

error = 'vocloadlib.error'	# exception raised in this module, values:

unknown_dag = 'unknown DAG name "%s"'
unknown_dag_key = 'unknown DAG key "%s"'
unknown_vocab = 'unknown vocabulary name "%s"'
unknown_vocab_key = 'unknown vocabulary key "%s"'

###--- Globals ---###

VOCABULARY_TERM_TYPE = 13	# default _MGIType_key for vocab terms
NOT_SPECIFIED = -1		# traditional 'n.s.' for vocabs
NO_LOAD = 0			# boolean (0/1); are we in a no-load state?
				#	(log SQL, but don't run it)

###--- Functions ---###

def setupSql (server,	# string; name of database server
	database,	# string; name of database
	username,	# string; user with full permissions on database
	password	# string; password for 'username'
	):
	# Purpose: initialize the 'db' module to use the desired database
	#	login information
	# Returns: nothing
	# Assumes: the parameters are all valid
	# Effects: initializes the 'db' module with the given login info, and
	#	tells it to use one connection (rather than a separate
	#	connection for each sql() call)
	# Throws: nothing

	db.set_sqlLogin (username, password, server, database)
	db.useOneConnection = 1
	return

def sql (
	commands	# string of SQL, or list of SQL strings
	):
	# Purpose: wrapper over the db.sql() function, so we don't need to
	#	specify 'auto' with each call.
	# Returns: as db.sql(), returns:
	#	list of dictionaries of 'commands' is a string
	#	list of lists of dictionaries if 'commands' is a list
	# Assumes: setupSql() has been invoked appropriately
	# Effects: queries the database
	# Throws: propagates any exceptions raised by db.sql()

	return db.sql (commands, 'auto')

def sqlog (
	commands,	# string of SQL, or list of SQL strings
	log		# Log.Log object to which to log the 'commands'
	):
	# Purpose: write the given 'commands' to the given 'log', then execute
	#	those SQL 'commands'
	# Returns: see sql()
	# Assumes: see sql()
	# Effects: writes to 'log', sends 'commands' to database
	# Throws: propagates any exceptions raised by db.sql()

	log.writeline (commands)
	return sql (commands)

def setNoload (
	on = 1		# boolean (0/1); turn no-load on (1) or off (0)?
	):
	# Purpose: set/unset the global NO_LOAD flag to indicate whether we
	#	are running in a no-load state
	# Returns: nothing
	# Assumes: nothing
	# Effects: alters the global NO_LOAD
	# Throws: nothing

	global NO_LOAD

	NO_LOAD = on
	return

def nl_sqlog (
	commands,	# string of SQL, or list of SQL strings
	log		# Log.Log object to which to log the 'commands'
	):
	# Purpose: write the given 'commands' to the given 'log'.  If we are
	#	not in a no-load state, then execute those SQL 'commands'.
	# Returns: see sql()
	# Assumes: see sql()
	# Effects: writes to 'log', may send 'commands' to database
	# Throws: propagates any exceptions raised by db.sql()
	# Notes: This is the no-load version of sqlog(), hence the "nl_"
	#	prefix.  It will check the no-load flag before executing
	#	the SQL.

	log.writeline (commands)
	if not NO_LOAD:
		return sql (commands)
	return []


def setVocabMGITypeKey (
	key		# integer; _MGIType_key for vocabulary terms
	):
	# Purpose: set the global VOCABULARY_TERM_TYPE value to be a new
	#	value.  should correspond to the correct _MGIType_key in
	#	ACC_MGIType
	# Returns: nothing
	# Assumes: nothing
	# Effects: alters VOCABULARY_TERM_TYPE
	# Throws: nothing

	global VOCABULARY_TERM_TYPE

	VOCABULARY_TERM_TYPE = key
	return

def anyTermsCrossReferenced (
	vocab_key		# integer; corresponds to VOC_Vocab._Vocab_key
	):
	# Purpose: determine if any terms in the vocabulary identified by
	#	'vocab_key' are cross-referenced from the VOC_Evidence and/or
	#	VOC_Annot tables
	# Returns: boolean (0/1) indicating whether any such cross-refs exist
	# Assumes: see sql()
	# Effects: queries the database
	# Throws: propagates any exceptions raised by sql()

	results = sql ( [
			'''select ct = count(1)
			from VOC_Term vt, VOC_Evidence ve
			where vt._Vocab_key = %d
				and vt._Term_key = ve._EvidenceTerm_key
			''' % vocab_key,

			'''select ct = count(1)
			from VOC_Term vt, VOC_Annot va
			where vt._Vocab_key = %d
				and vt._Term_key = va._Term_key
			''' % vocab_key,
			])
	return results[0][0]['ct'] + results[1][0]['ct'] > 0

def timestamp (
	label = 'Current time:'		# string; preface to the timestamp
	):
	# Purpose: return a timestamp including the given 'label' followed by
	#	the current date and time in the format mm/dd/yyyy hh:mm:ss
	# Returns: string
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing

	return '%s %s' % \
		(label,
		time.strftime ("%m/%d/%Y %H:%M:%S",
			time.localtime (time.time())))

def getDagName (
	dag		# integer; corresponds to DAG_DAG._DAG_key
	):
	# Purpose: return the name of the DAG identified by 'dag'
	# Returns: string
	# Assumes: nothing
	# Effects: queries the database
	# Throws: 1. error if the given 'dag' is not in the database;
	#	2. propagates any exceptions raised by sql()

	result = sql ('select name from DAG_DAG where _DAG_key = %d' % dag)
	if len(result) != 1:
		raise error, unknown_dag_key % dag
	return result[0]['name']

def getDagKey (
	dag,		# string; corresponds to DAG_DAG.name
	vocab = None	# string vocab name or integer vocab key
	):
	# Purpose: return the _DAG_key for the given 'dag' name
	# Returns: integer
	# Assumes: nothing
	# Effects: queries the database
	# Throws: 1. error if the given 'dag' is not in the database;
	#	2. propagates any exceptions raised by sql()
	# Notes: Since the DAG_DAG.name field is does not require unique
	#	values, we may also need to know which 'vocab' it relates to.

	if vocab:
		if type(vocab) == types.StringType:
			vocab = getVocabKey (vocab)
		result = sql ('''select dd._DAG_key
				from DAG_DAG dd, VOC_VocabDAG vvd
				where dd._DAG_key = vvd._DAG_key
					and vvd._Vocab_key = %d
					and dd.name = "%s"''' % (vocab, dag))
	else:
		result = sql ('''select _DAG_key
				from DAG_DAG
				where name = "%s"''' % dag)
	if len(result) != 1:
		raise error, unknown_dag % dag
	return result[0]['_DAG_key']

def getVocabName (
	vocab		# integer; key corresponding to VOC_Vocab._Vocab_key
	):
	# Purpose: return the vocabulary name for the given 'vocab' key
	# Returns: string
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions raised by getVocabAttributes()

	return getVocabAttributes (vocab)[3]

def getVocabKey (
	vocab		# string; vocab name from VOC_Vocab.name
	):
	# Purpose: return the vocabulary key for the given 'vocab' name
	# Returns: integer
	# Assumes: nothing
	# Effects: queries the database
	# Throws: 1. error if the given 'vocab' is not in the database
	#	2. propagates any exceptions raised by sql()

	result = sql ('select _Vocab_key from VOC_Vocab where name = "%s"' % \
		vocab)
	if len(result) != 1:
		raise error, unknown_vocab % vocab
	return result[0]['_Vocab_key']

def checkVocabKey (
	vocab_key	# integer; key for vocabulary, as VOC_Vocab._Vocab_key
	):
	# Purpose: check that 'vocab_key' exists in the database
	# Returns: nothing
	# Assumes: nothing
	# Effects: queries the database
	# Throws: 1. raises TypeError if 'vocab_key' is not an integer
	#	2. propogates 'error' if 'vocab_key' is not in VOC_Vocab
	#	3. also propagates any other exceptions raised by
	#		getVocabAttributes()

	if type(vocab_key) != types.IntegerType:
		raise TypeError, 'Integer vocab key expected'

	# We use this function to retrieve basic info about the vocab, but we
	# don't need to do anything with it.  (We're just seeing that it
	# exists, and letting the exceptions propagate if it doesn't.)

	getVocabAttributes (vocab_key)
	return

def isSimple (
	vocab	# integer vocabulary key or string vocabulary name
	):
	# Purpose: determine if 'vocab' is a simple vocabulary or a DAG
	# Returns: boolean (0/1); returns 1 if 'vocab' is a simple vocabulary
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions from getVocabAttributes()

	return getVocabAttributes (vocab)[0]

def isPrivate (
	vocab	# integer vocabulary key or string vocabulary name
	):
	# Purpose: determine if 'vocab' is private
	# Returns: boolean (0/1); returns 1 if 'vocab' is private
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions from getVocabAttributes()

	return getVocabAttributes (vocab)[1]

def countTerms (
	vocab	# integer vocabulary key or string vocabulary name
	):
	# Purpose: count the number of terms in the given 'vocab'
	# Returns: integer; count of the terms
	# Assumes: 'vocab' exists in the database
	# Effects: queries the database
	# Throws: propagates any exceptions from sql()

	if type(vocab) == types.StringType:
		vocab = getVocabKey (vocab)
	result = sql ('''select ct = count(1)
			from VOC_Term
			where _Vocab_key = %d''' % vocab)
	return result[0]['ct']

def countNodes (
	dag,		# integer DAG key or string DAG name
	vocab = None	# integer vocab key or string vocab name; required if
			# 'dag' is the name of the DAG
	):
	# Purpose: count the number of nodes in the given 'dag'
	# Returns: integer; count of the nodes
	# Assumes: 'dag' exists in the database
	# Effects: queries the database
	# Throws: propagates any exceptions from sql()
	# Notes: Because DAG names are not required to be unique, we also need
	#	the associated vocab to uniquely identify a DAG when given
	#	a DAG name.

	if type(dag) == types.StringType:
		dag = getDagKey (dag, vocab)
	result = sql ('''select ct = count(1)
			from DAG_Node
			where _DAG_key = %d''' % dag)
	return result[0]['ct']

def getTerms (
	vocab	# integer vocabulary key or string vocabulary name
	):
	# Purpose: retrieve the terms for the given 'vocab' and their
	#	respective attributes
	# Returns: dbTable.RecordSet object
	# Assumes: 'vocab' exists in the database
	# Effects: queries the database
	# Throws: propagates exceptions from sql()
	# Notes: The RecordSet object returned contains dictionaries, each
	#	of which represents a term and its attributes.  The
	#	dictionaries may be accessed using the desired term's key.

	if type(vocab) == types.StringType:
		vocab = getVocabKey (vocab)
	[ voc_term, voc_text, voc_synonym ] = sql( [
		'''select *				-- basic term info
		from VOC_Term
		where _Vocab_key = %d''' % vocab,

		'''select vx.*				-- text for term
		from VOC_Text vx, VOC_Term vt
		where vt._Vocab_key = %d
			and vt._Term_key = vx._Term_key
		order by vx._Term_key, vx.sequenceNum''' % vocab,

		'''select vs.*				-- synonyms for term
		from VOC_Synonym vs, VOC_Term vt
		where vt._Vocab_key = %d
			and vt._Term_key = vs._Term_key
		order by vs.synonym''' % vocab,
		] )
	
	# build a dictionary of 'notes', mapping a term key to a string of
	# notes.  We take care to join multiple 255-character chunks into
	# one string.

	notes = {}
	for row in voc_text:
		term_key = row['_Term_key']
		if notes.has_key (term_key):
			notes[term_key] = notes[term_key] + row['note']
		else:
			notes[term_key] = row['note']

	# build a dictionary of 'synonyms', mapping a term key to a list of
	# strings (each of which is one synonym)

	synonyms = {}
	for row in voc_synonym:
		term_key = row['_Term_key']
		if not synonyms.has_key (term_key):
			synonyms[term_key] = []
		synonyms[term_key].append (row['synonym'])

	# Each dictionary in 'voc_term' represents one term and contains all
	# its basic attributes.  We step through the list to add any 'notes'
	# and 'synonyms' for each.

	for row in voc_term:
		term_key = row['_Term_key']
		if notes.has_key (term_key):
			row['notes'] = notes[term_key]
		else:
			row['notes'] = None
		if synonyms.has_key (term_key):
			row['synonyms'] = synonyms[term_key]
		else:
			row['synonyms'] = []

	# convert the list of dictionaries 'voc_term' into a RecordSet object
	# keyed by the _Term_key, and return it

	return dbTable.RecordSet (voc_term, '_Term_key')

def getLabels ():
	# Purpose: find the complete set of DAG labels from the database
	# Returns: dictionary mapping labels to their keys
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions from sql()

	result = sql ('select label, _Label_key from DAG_Label')
	labels = {}
	for row in result:
		labels[row['label']] = row['_Label_key']
	return labels

def getTermIDs (
	vocab		# integer vocabulary key or string vocabulary name
	):
	# Purpose: get a dictionary which maps from a primary accession ID
	#	to its associated term key
	# Returns: see Purpose
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions from sql()

	if type(vocab) == types.StringType:
		vocab = getVocabKey (vocab)
	result = sql ('''select acc.accID, vt._Term_key
			from VOC_Term vt, ACC_Accession acc
			where vt._Vocab_key = %d
				and acc._MGIType_key = %d
				and vt._Term_key = acc._Object_key
				and acc.preferred = 1''' % \
			(vocab, VOCABULARY_TERM_TYPE))
	ids = {}
	for row in result:
		ids[row['accID']] = row['_Term_key']
	return ids

def readTabFile (
	filename,	# string; path to a tab-delimited file to read
	fieldnames	# list of strings; each is the name of one field
	):
	# Purpose: read a tab-delimited file and convert each line to a
	#	dictionary mapping from fieldnames to values
	# Returns: list of dictionaries
	# Assumes: 'filename' is readable
	# Effects: reads 'filename'
	# Throws: 1. IOError if we cannot read from 'filename';
	#	2. error if a line has the wrong number of fields
	# Example: Consider the following tab-delimited file 'foo.txt':
	#		3	Joe	Smith
	#		5	Jane	Jones
	#	Then, readTabFile ('foo.txt', ['key', 'first', 'last' ])
	#	returns:
	#		[ { 'key' : 3, 'first' : 'Joe', 'last' : 'Smith' },
	#		  { 'key' : 5, 'first' : 'Jane', 'last' : 'Jones' } ]

	num_fields = len(fieldnames)
	lines = []
	fp = open (filename, 'r')
	line = fp.readline()
	while line:
		# note that we use line[:-1] to trim the trailing newline
		fields = regsub.split (line[:-1], '\t')

		if len(fields) != num_fields:
			raise error, bad_line

		# map each tab-delimited field to its corresponding fieldname
		i = 0
		dict = {}
		while i < num_fields:
			dict[fieldnames[i]] = fields[i]
			i = i + 1

		lines.append(dict)	# add to the list of dictionaries
		line = fp.readline()
	fp.close()
	return lines

def splitBySize (
	s,		# string; the string to be split
	size = 255	# integer; max number of characters per output string
	):
	# Purpose: break 's' into a list of strings containing at most 'size'
	#	characters
	# Returns: list of strings
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: string.join (splitBySize (s, n), '') == s, for all n

	len_s = len(s)
	parts = []
	i = 0
	while i < len_s:
		parts.append (s[i:i+size])
		i = i + size
	return parts

def getMax (
	fieldname,	# string; name of a field in 'table' in the database
	table		# string; name of a table in the database
	):
	# Purpose: return the maximum value of 'fieldname' in 'table'
	# Returns: depends on the datatype of 'fieldname' in 'table'; will be
	#	None if 'table' contains no records
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates all exceptions from sql()

	result = sql ('select mx=max(%s) from %s' % (fieldname, table))
	return result[0]['mx']

def getLogicalDBkey (
	vocab		# integer vocabulary key or string vocabulary name
	):
	# Purpose: retrieve the logical database key (_LogicalDB_key) for
	#	the given 'vocab'
	# Returns: integer
	# Assumes: nothing
	# Effects: queries the database
	# Throws: propagates any exceptions from getVocabAttributes()

	return getVocabAttributes (vocab)[2]

def escapeDoubleQuotes (
	s		# string in which to duplicate any double-quotes
	):
	# Purpose: duplicate any double-quotes (") which appear in s
	# Returns: string
	# Assumes: nothing
	# Effects: nothing
	# Throws: nothing
	# Notes: This function is used to prepare strings to be sent as part
	#	of a SQL command to Sybase.  We delimit string fields for
	#	sybase using double-quotes, so if the string contains any
	#	double-quotes, we need to duplicate them.

	return regsub.gsub ('"', '""', s)

def deleteVocabTerms (
	vocab_key,	# integer; vocabulary key from VOC_Vocab._Vocab_key
	log = None	# Log.Log object; where to log the deletions
	):
	# Purpose: delete all terms for the given vocabulary key, and any
	#	associated attributes (like text blocks and synonyms)
	# Returns: nothing
	# Assumes: setupSql() has been called appropriately
	# Effects: removes records from VOC_Term, VOC_Text, and VOC_Synonym
	# Throws: propagates any exceptions from sqlog() or sql()
	# Notes: Due to the firing of triggers when we delete from the main
	#	table (VOC_Term), the sybase log was filling up quickly.  To
	#	circumvent the triggers, we will delete from tables
	#	individually here.  Also, we need to check that we are not in
	#	a no-load state before calling the sql() function.

	deletes = [
		'''delete from VOC_Text where _Term_key in
		(select _Term_key from VOC_Term where _Vocab_key = %d)''' % \
			vocab_key,

		'''delete from VOC_Synonym where _Term_key in
		(select _Term_key from VOC_Term where _Vocab_key = %d)''' % \
			vocab_key,

		'delete from VOC_Term where _Vocab_key = %d' % vocab_key,
		]
	for delete in deletes:
		if log:
			nl_sqlog (delete, log)
		elif not NO_LOAD:
			sql (delete)
	return

def deleteDagComponents (
	dag_key,	# integer; DAG key from DAG_DAG._DAG_key
	log = None	# Log.Log object; where to log the deletions
	):
	# Purpose: delete all components of the DAG with the given key,
	#	including its nodes, terms, and closure.  (but not its actual
	#	DAG_DAG entry)
	# Returns: nothing
	# Assumes: setupSql() has been called appropriately
	# Effects: removes records from DAG_Node, DAG_Edge, and DAG_Closure
	# Throws: propagates any exceptions from sqlog() or sql()
	# Notes: Due to the firing of triggers when we delete from the main
	#	table (DAG_Node), the sybase log was filling up quickly.  To
	#	circumvent the triggers, we will delete from tables
	#	individually here.  We need to be sure to check the no-load
	#	option before calling sql().

	deletes = [
		'delete from DAG_Edge where _DAG_key = %d' % dag_key,
		'delete from DAG_Closure where _DAG_key = %d' % dag_key,
		'delete from DAG_Node where _DAG_key = %d' % dag_key,
		]
	for delete in deletes:
		if log:
			nl_sqlog (delete, log)
		elif not NO_LOAD:
			sql (delete)
	return

def truncateTransactionLog (
	database,		# string; name of the database
	log = None		# Log.Log object; where to log the command
	):
	# Purpose: truncate the transaction log for the given database
	# Returns: nothing
	# Assumes: nothing
	# Effects: see Purpose, does not save the log's contents to a file
	# Throws: propagates any exceptions from sql()
	# Notes: We do not dump the transaction log if running in no-load
	#	mode.

	cmd = 'dump transaction %s with truncate_only' % database
	if log:
		nl_sqlog (cmd, log)
	elif not NOLOAD:
		sql (cmd)
	return

###--- Private Functions ---###

vocab_info_cache = {}	# used as a cache for 'getVocabAttributes()' function

def getVocabAttributes (
	vocab		# integer vocabulary key or string vocabulary name
	):
	# PRIVATE FUNCTION
	#
	# Purpose: retrieve some basic info for the given 'vocab'
	# Returns: tuple containing: (boolean isSimple, boolean isPrivate,
	#	integer _LogicalDB_key, string name, integer vocab key)
	# Assumes: 'vocab' exists in the database
	# Effects: queries the database
	# Throws: 1. propagates any exceptions from sql();
	#	2. raises 'error' if 'vocab' is not in the database

	global vocab_info_cache

	if type(vocab) == types.StringType:	# ensure we work w/ the key
		vocab = getVocabKey (vocab)

	# get it from the database if it's not in the cache already

	if not vocab_info_cache.has_key (vocab):
		result = sql('''select isSimple, isPrivate, _LogicalDB_key,
					_Vocab_key, name
				from VOC_Vocab
				where _Vocab_key = %d''' % vocab)
		if len(result) != 1:
			raise error, unknown_vocab_key % vocab
		r = result[0]

		# store resulting info in the cache

		vocab_info_cache[vocab] = (r['isSimple'], r['isPrivate'],
			r['_LogicalDB_key'], r['name'], r['_Vocab_key'])

	return vocab_info_cache[vocab]
