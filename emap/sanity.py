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
#	INVALID_TS_RPT
#       MISSING_FIELD_RPT
#       INVALID_ID_RPT
#       MIN_TERMS_RPT
#       UNDEFINED_PARENT_RPT
#       ALT_IS_PRIMARY_RPT
#       OBS_IS_PARENT_RPT
#       OBS_WITH_RELATIONSHIP_RPT
#	OBO_FILE_VERSION
#	TERM_IN_DB_NOTIN_INPUT_RPT
#	STANZA_HAS_TAB_RPT'
#
#  We may want to create one error file and one warning file and
#  instead of 10 different output files.
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

# output files - these files are used by emapload.py which is responsible
# for reporting these errors
invalidTSFile = os.environ['INVALID_TS_RPT']
missingFieldFile = os.environ['MISSING_FIELD_RPT']
invalidIdFile = os.environ['INVALID_ID_RPT']
minTermsFile = os.environ['MIN_TERMS_RPT']
undefinedParentFile = os.environ['UNDEFINED_PARENT_RPT']
altIsPrimaryFile = os.environ['ALT_IS_PRIMARY_RPT']
obsIsParentFile = os.environ['OBS_IS_PARENT_RPT']
obsWithRelationshipFile = os.environ['OBS_WITH_RELATIONSHIP_RPT']
inDbNotInInputFile = os.environ['TERM_IN_DB_NOTIN_INPUT_RPT']
stanzaHasTabFile = os.environ['STANZA_HAS_TAB_RPT']

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

    global fpInvalidTS, fpMissingField, fpInvalidId, fpMinTerms, fpObo
    global fpUndefinedParent, fpAltIsPrimary, fpObsIsParent
    global fpObsWithRelationship, fpInDbNotInInput, fpStanzaHasTab
    try:
        fpInvalidTS = open(invalidTSFile, 'w')
    except:
        print 'Preprocess cannot open invalid TS file: %s' % invalidTSFile
        sys.exit(1)

    try:
        fpMissingField = open(missingFieldFile, 'w')
    except:
        print 'Preprocess cannot open missing field file: %s' % missingFieldFile
        sys.exit(1)

    try:
        fpInvalidId = open(invalidIdFile, 'w')
    except:
        print 'Preprocess cannot open invalid id file: %s' % invalidIdFile
        sys.exit(1)

    try:
        fpMinTerms = open(minTermsFile, 'w')
    except:
        print 'Preprocess cannot open minimum term file: %s' % minTermsFile
        sys.exit(1)

    try:
	fpObo = open(oboFile, 'r')
    except:
	print 'Preprocess cannot open obo file: %s' % oboFile
	sys.exit(1)

    try:
	fpUndefinedParent = open(undefinedParentFile, 'w')
    except:
	print 'Preprocess cannot open undefined parent file: %s' % \
	    undefinedParentFile
	sys.exit(1)

    try:
        fpAltIsPrimary	 = open(altIsPrimaryFile, 'w')
    except:
        print 'Preprocess cannot open alt id is primary file: %s' % \
	    altIsPrimaryFile
        sys.exit(1)

    try:
        fpObsIsParent   = open(obsIsParentFile, 'w')
    except:
        print 'Preprocess cannot open obsolete is parent file: %s' % \
	    obsIsParentFile
        sys.exit(1)

    try:
        fpObsWithRelationship   = open(obsWithRelationshipFile, 'w')
    except:
        print 'Preprocess cannot open obsolete with relationship file: %s' % \
	    obsWithRelationshipFile
        sys.exit(1)

    try:
        fpInDbNotInInput = open(inDbNotInInputFile, 'w')
    except:
        print 'Preprocess cannot open obsolete with relationship file: %s' % \
            inDbNotInInputFile
        sys.exit(1)
    try:
        fpStanzaHasTab = open(stanzaHasTabFile, 'w')
    except:
        print 'Preprocess cannot open stanza with tab file: %s' % \
            stanzaHasTabFile
        sys.exit(1)

    return

def closeFiles ():
    # Purpose: Close all input and output files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    global fpInvalidTS, fpMissingField, fpInvalidId, fpMinTerms, fpObo
    global fpUndefinedParent, fpAltIsPrimary, fpObsIsParent
    global fpObsWithRelationship
 
    fpInvalidTS.close()
    fpMissingField.close()
    fpInvalidId.close()
    fpMinTerms.close()
    fpObo.close()
    fpUndefinedParent.close()
    fpAltIsPrimary.close()
    fpObsIsParent.close()
    fpObsWithRelationship.close()
    fpInDbNotInInput.close()
    fpStanzaHasTab.close()
    return

def getDbTermIds():
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
	    if hasName and currentStanzaDict['name'] == ['']:
		hasNameValue = 0
	    msg = ''
	    if not hasId or not hasName or not hasIdValue or not hasNameValue:
	 	if not hasId:
		    msg = 'Stanza missing id field:%s' % CRT
		elif not hasName:
		     msg = 'Stanza missing name field:%s' % CRT
		elif not hasIdValue:
		    msg = 'Stanza missing id value:%s' % CRT
		elif not hasNameValue:
		    msg = 'Stanza missing name value%s' % CRT
		fpMissingField.write(msg)
		for key in currentStanzaDict.keys():
		    fpMissingField.write('%s:%s%s' % \
			(key, currentStanzaDict[key], CRT))
		fpMissingField.write(CRT)

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
		    fpStanzaHasTab.write("%s has tab on line: '%s'%s" % (label, entry, CRT))
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
			    fpInvalidTS.write('%s: %s%s' % (label, ts, CRT))
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
	fpMinTerms.write('%sWARNING: %s contains %s terms which is fewer than the minimum allowed %s terms%s%s' % (CRT, oboFile, stanzaCtr, MINTERMS, CRT, CRT))

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
	     fpUndefinedParent.write('%s%s' % (u, CRT))

    # check for alt_id's that are also primary
    altIsPrimarySet = termIdSet.intersection(set(altIdList))
    if len(altIsPrimarySet):
	for a in altIsPrimarySet:
	    fpAltIsPrimary.write('%s%s' % (a, CRT))

    # check for obsolete IDs that are parents of primary terms
    obsIsParentSet = parentIdSet.intersection(set(obsoleteIdList))
    
    if len(obsIsParentSet):
	for o in obsIsParentSet:
	    fpObsIsParent.write('%s%s' % (o, CRT))
    if len(obsWithRelationshipList):
	for o in obsWithRelationshipList:
	    fpObsWithRelationship.write('%s%s' % (o, CRT))

    # check for ids in the database, but not in the input file
    # also check alt Ids in the input file
    inFileSet = set(termIdList).union(set(altIdList))
    inDbSet = set(dbTermIdDict.keys())
    inDbNotInFileSet = inDbSet.difference(inFileSet)
    numNotInFile = len(inDbNotInFileSet)
    if numNotInFile:
	fpInDbNotInInput.write('EMAPA IDs in the database and not in the input file%s%s' % (CRT, CRT))
	for id in inDbNotInFileSet:
	    term = dbTermIdDict[id]
	    entry = '%s%s%s' % (id, TAB, term)
	    fpInDbNotInInput.write(entry + CRT)

    # Report, on the command line, the number of terms in the obo file as a
    # convenience to the curator running the sanity checks
    print '%sThere are %s Anatomical Structure terms in %s%s' % \
	(CRT, stanzaCtr, oboFile, CRT)

#####################
#
# Main
#
#####################
checkArgs()
openFiles()
getDbTermIds()
doSanityChecks()
closeFiles()

sys.exit(0)

