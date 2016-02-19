#!/usr/local/bin/python
#
#  sanity.py
###########################################################################
#
#  Purpose:
#
#	Performs sanity checks on non well-formed obo file and proprietary 
#          checks to an EMAPA obo file - these checks would cause the Ontology 
#	   module to throw an exception, so we do them here
#
#  Env Vars:
#	TS_START
#	TS_END
#	MIN_TERMS_EXPECTED 
#	INPUT_FILE_DEFAULT
#	OBO_FILE_VERSION
#	QC_ERROR_RPT
#	QC_WARNING_RPT
#
#  Inputs:
#
#	EMAPA.obo
#
#  Outputs:
#
#      - Nine intermediate sanity check reports, these individual intermediate 
#	 reports will be read by emapload.py and reported, along with the sanity
#	 checks it runs, in a single report
#	    
#  Exit Codes:
#
#      0:  Successful completion
#      1:  If can not open input/output files or if incorrect usage
#
#  Assumes:
#	
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      3) Open the input/output files.
#      4) Generate the intermediate sanity check reports.
#      5) Close the input/output files.
#
#  Notes:  None
#
# History
#
# 02/19/2016	lec
#	- TR12223/gxd anatomy II/add some more sanity checks
#
###########################################################################

import sys
import os
import string
import Set
import db

#
#  CONSTANTS
#
TAB = '\t'
CRT = '\n'
USAGE = 'sanity.py'

# The obo version expected by the load 
expectedVersion = os.environ['OBO_FILE_VERSION']

# 1 if we have found the string 'format-version'
foundVersion = 0

# valid Theiler Stages
TSSTART = int(os.environ['TS_START'])
TSEND = int(os.environ['TS_END'])

# minimum number of terms expected in the input file
MINTERMS = int(os.environ['MIN_TERMS_EXPECTED'])

#
#  GLOBALS
#

# input file
oboFile = os.environ['INPUT_FILE_DEFAULT']

invalidTS = 'EMAPA IDs with invalid Theiler stages'
missingField = 'Missing Field'
invalidId = 'Invalid EMAPA IDs'
minTerms = 'Minimum Terms (%s)' % (MINTERMS)
undefinedParent = 'Undefined parent IDs'
altIsPrimary = 'Alt_ids that are also primary'
obsIsParent = 'Obsolete Ids that are also parents'
obsWithRelationship = 'Obsolete Ids that have parent or TS relationships'
stanzaHasTab = 'Stanzas with embedded tabs'
inDbNotInInput = 'In database, not in input'

# output files - these files are used by emapload.py which is responsible
# for reporting these errors
errorFile = os.environ['QC_ERROR_RPT']
warningFile = os.environ['QC_WARNING_RPT']

# dict representing all anatomical structure stanzas in the obo file
# Looks like 
#   {integerKey: {field1Name:field1Value, ... fieldnName:fieldnValue}, ...}
allStanzasDict = {}

# these two lists used to determine any parent ids that don't exist as terms
# list of all EMAPA term ids in the input file
termIdList = []

# list of all EMAPA parent ids
parentIdList = []

# EMAPA term ids in the database and their terms {EMAPAID:term, ...}
dbTermIdDict = {}

# list of all EMAPA alt_ids used to determine if they are also primary ids
altIdList = []

# list of all EMAPA obsolete ids used to check if they parents of primary terms
obsoleteIdList = []

# list of obsolete ids with parents or TS relationships
obsWithRelationshipList = []

# the list of all valid Theiler Stages
validTSList = []
for ts in range(TSSTART, TSEND + 1):
	validTSList.append(ts)

def checkArgs ():
    # Purpose: Validate the arguments to the script.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    if len(sys.argv) != 1:
        print USAGE
        sys.exit(1)

    return

def openFiles ():
    # Purpose: Open all input and output files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables.
    # Throws: Nothing

    global fpObo
    global fpError, fpWarning

    try:
        fpObo = open(oboFile, 'r')
    except:
        print 'Preprocess cannot open obo file: %s' % oboFile
        sys.exit(1)

    try:
        fpError = open(errorFile, 'w')
    except:
        print 'Preprocess cannot open error file: %s' % errorFile
        sys.exit(1)

    try:
        fpWarning = open(warningFile, 'w')
    except:
        print 'Preprocess cannot open warning file: %s' % warningFile
        sys.exit(1)

    fpError.write('You must fix all errors in this report and run the QC script again\n\n')

    return

def closeFiles ():
    # Purpose: Close all input and output files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    global fpObo
    global fpError, fpWarning
 
    fpObo.close()
    fpError.close()
    fpWarning.close()

    return

def getDbTermIds():
    # Purpose: load all emapa id/term into dbTermIdDict
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    global dbTermIdDict

    results = db.sql('''select a.accId, t.term
	from ACC_Accession a, VOC_Term t
	where a._LogicalDB_key = 169
	and a._MGIType_key = 13
	and a._Object_key = t._Term_key''', 'auto')

    for r in results:
	dbTermIdDict[r['accId']] = r['term']

    return

def doSanityChecks( ):
    # Purpose: Run a set of sanity checks on an obo file
    # Returns: Nothing
    # Assumes: obo file and sanity report files have been opened
    # Effects: alters global variables
    # Throws: Nothing

    global allStanzasDict, foundVersion
   
    # incremental key to our dictionary of stanzas, the global allStanzasDict 
    # we use an incremental key rather than, say the EMAPA id, as the id could
    # be misssing
    keyCtr = 1

    # flag indicating we have found the first stanza i.e. we are beyond the
    # header
    foundStanza = 0
    
    # flag indicating we are within a stanza
    inStanza = 0

    # represents data from the current stanza we are parsing
    currentStanzaDict = {}

    #
    # parse the obo file into a data structure
    #
    for line in fpObo.readlines():
	# we use this to find lines with tabs
	lineNoCRT = string.strip(line, CRT)

	# we use this to evaluate the stanza attributes
	lineStripped = string.strip(line)

	if string.find(lineStripped, 'format-version') != -1:
	    foundVersion = 1
	    lineList = string.split(lineStripped, ':')
	    version = string.strip(lineList[1])

	    # exit if the version is not the one we expect
	    if version != expectedVersion:
		closeFiles()
		sys.exit(2)

	if lineStripped == '[Term]':
	    foundStanza = 1
	    inStanza = 1
	    continue
	if lineStripped == '':
	    inStanza = 0
	if foundStanza == 1:
	    # if we're within a stanza store the field name and its value
	    # in the currentStanzaDict
	    if inStanza == 1:
		i = string.find(lineStripped, ':')
		tabIndex = string.find(lineNoCRT, TAB)
		if tabIndex > -1:
		    if not currentStanzaDict.has_key('tab'):
			currentStanzaDict['tab'] = []
		    currentStanzaDict['tab'].append(lineNoCRT)
		fieldName = lineStripped[0:i]
		value = lineStripped[i+1:].strip()
		if fieldName not in currentStanzaDict.keys():
		    currentStanzaDict[fieldName] = []
		currentStanzaDict[fieldName].append(value)
	    else: # add the current stanza to the dict of all obo stanzas
		allStanzasDict[keyCtr] = currentStanzaDict
		currentStanzaDict = {}
		keyCtr += 1

    #
    # iterate through all the stanzas in the obo stanza data structure
    #

    # current count of anatomical structure stanzas looked at in allStanzasDict
    stanzaCtr = 0
    for s in allStanzasDict.keys():
	currentStanzaDict = allStanzasDict[s]

	# skip the stanza if not in the anatomical structure namespace
	if currentStanzaDict.has_key('namespace') and \
	        currentStanzaDict['namespace'][0] == 'anatomical_structure':
	    stanzaCtr += 1

	    # check for existence of id and name field
	    # and existence of id and name value
	    hasId = currentStanzaDict.has_key('id')
	    hasName = currentStanzaDict.has_key('name')
	    hasIdValue = 1
	    hasNameValue = 1
	    if hasId and currentStanzaDict['id'] == ['']:
		hasIdValue = 0
	    if hasName and currentStanzaDict.has_key('name') == ['']:
		hasNameValue = 0
	    msg = ''
	    if not (hasId and hasName and hasIdValue and hasNameValue):
	 	if not hasId:
		    msg = 'Stanza missing id field%s' % (TAB)
		elif not hasName:
		    msg = 'Stanza missing name field%s' % (TAB)
		elif not hasIdValue:
		    msg = 'Stanza missing id value%s' % (TAB)
		elif not hasNameValue:
		    msg = 'Stanza missing name value%s' % (TAB)
		for key in currentStanzaDict.keys():
		    fpError.write('%s%s%s%s%s%s%s\n' % (missingField, TAB, msg, TAB, key, TAB, currentStanzaDict[key]))

	    # check for proper EMAPA id format
	    id = ''
	    if hasId:
		id = currentStanzaDict['id'][0]
		termIdList.append(id)
		# check for missing ':', bad prefix (EMAPA), bad suffix
		# (5 integers)
		missingColon = 0
		badPrefix = 0
		badSuffix = 0

		i = string.find(id, ':')
		if i == -1:
		    missingColon = 1
		else:    
		    prefix = id[0:i]
		    if prefix != 'EMAPA':
			badPrefix = 1
		    suffix = id[i+1:].strip()
		    try:
			x = int(suffix)
		    except:
			badSuffix = 1
		    if len(suffix) != 5 and suffix != '0':
			badSuffix = 1
		# blank id is reported elsewhere
		if (missingColon or badPrefix or badSuffix) and id != '':
		    fpInvalidId.write('%s%s' % (id, CRT))
	    
            # check for existence of tab
            if currentStanzaDict.has_key('tab'):
		linesWithTabList = currentStanzaDict['tab']
		# get some info to report if TAB found. Use id if
		# it exists, otherwise name - default is empty string
		label = ''
		if hasId:
		    label = currentStanzaDict['id'][0]
		elif hasName:
		    label = currentStanzaDict['name'][0]
		for entry in linesWithTabList:
		    fpError.write("%s%s%s has tab on line: '%s'\n" % (stanzaHasTab, TAB, label, entry))
	    # look at all 'relationship' fields
	    if currentStanzaDict.has_key('relationship'):
		rList = currentStanzaDict['relationship']
		for r in rList:
		    # check for valid Theiler stage value
		    if string.find(r, 'starts_at') != -1 or \
			    string.find(r, 'ends_at') != -1:
			# e.g. 'ends_at TS01' - ts='01'
			ts = string.split(r)[1][2:]
			# if 'starts_at TS' - ts=''
			if ts != '':
			    ts = int(ts)

			# get some info to report if TS is invalid, use id if
			# it exists, otherwise name - default is empty string
			label = ''
			if hasId:
			    label = currentStanzaDict['id'][0]
			elif hasName:
			    label = currentStanzaDict['name'][0]
			if ts not in validTSList:
			    fpError.write('%s%s%s%s%s\n' % (invalidTS, TAB, label, TAB, ts))
		    # add to list of pids for undefined undefined parent check
	   	    # e.g. 'part_of EMAPA:25765' 
		    elif string.find(r, 'is_a') != -1 or \
			    string.find(r, 'part_of') != -1:
			parentIdList.append(string.strip(string.split(r)[1]))

	    # look for alt_id's
	    if currentStanzaDict.has_key('alt_id'):
		aList = currentStanzaDict['alt_id']
		for a in aList:
		    altIdList.append(a)

	    # look for obsolete ids
	    if currentStanzaDict.has_key('is_obsolete'):
		obsoleteIdList.append(id)
		if currentStanzaDict.has_key('relationship'):
		    obsWithRelationshipList.append(id)
		
    # report if number of anatomical dictionary stanzas in obo file is less than
    # the configured minimum value
    if stanzaCtr < MINTERMS:
	fpWarning.write('%s%s%s contains %s terms\n' % (minTerms, TAB, oboFile, stanzaCtr))

    # exit if the 'format-version' field not present in the obo file
    if foundVersion == 0:
	closeFiles()
	sys.exit(2)

    # check for undefined parents
    termIdSet = set(termIdList)
    parentIdSet = set(parentIdList)
    undefinedSet = parentIdSet.difference(termIdSet)

    if len(undefinedSet):
	for u in undefinedSet:
	     fpError.write('%s%s%s\n' % (undefinedParent, TAB, u))

    # check for alt_id's that are also primary
    altIsPrimarySet = termIdSet.intersection(set(altIdList))
    if len(altIsPrimarySet):
	for a in altIsPrimarySet:
	    fpError.write('%s%s%s\n' % (altIsPrimary, TAB, a))

    # check for obsolete IDs that are parents of primary terms
    obsIsParentSet = parentIdSet.intersection(set(obsoleteIdList))
    
    if len(obsIsParentSet):
	for o in obsIsParentSet:
	    fpError.write('%s%s%s\n' % (obsIsParent, TAB, o))
    if len(obsWithRelationshipList):
	for o in obsWithRelationshipList:
	    fpError.write('%s%s%s\n' % (obsWithRelationship, TAB, o))

    # check for ids in the database, but not in the input file
    # also check alt Ids in the input file
    inFileSet = set(termIdList).union(set(altIdList))
    inDbSet = set(dbTermIdDict.keys())
    inDbNotInFileSet = inDbSet.difference(inFileSet)
    numNotInFile = len(inDbNotInFileSet)
    if numNotInFile:
	fpError.write('%s%sEMAPA IDs in the database and not in the input file\n' % (inDbNotInInput, TAB))
	for id in inDbNotInFileSet:
	    term = dbTermIdDict[id]
	    entry = '%s%s%s' % (id, TAB, term)
	    fpError.write('%s%sentry\n' % (inDbNotInInput, TAB))

    # Report, on the command line, the number of terms in the obo file as a
    # convenience to the curator running the sanity checks
    print '%sThere are %s EMAPA terms in %s%s' % (CRT, stanzaCtr, oboFile, CRT)

#####################
#
# Main
#
#####################

# check the arguments to this script
checkArgs()

# open input/output files
openFiles()

# load existing emapa id/term that are in database
getDbTermIds()

# run sanity checks
doSanityChecks()

# close all input/output files
closeFiles()

sys.exit(0)

