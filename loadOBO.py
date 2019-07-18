#!/usr/local/bin/python
#
#  loadOBO.py
###########################################################################
#
#  Purpose:
#
#      To load a vocabulary using an OBO format input file.
#
#  Usage:
#
#      loadOBO.py [-n] [-f|-i] [-l <log file>] <RcdFile>
#
#      where
#          -n is the "no load" option
#
#          -f is the option to do a full load
#
#          -i is the option to do an incremental load
#
#          -l is the option that is followed by the log file name
#
#          RcdFile is the rcd file for the vocabulary
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - An OBO format input file
#
#  Outputs:
#
#      - Log file
#      - File of terms (Termfile)
#      - 1 or more DAG files (one for each namespace)
#      - Bcp files
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Use the OBOParser module to parse the input file and create
#         the Termfile and DAG file(s).
#
#      2) Invoke the loadVOC module to load the vocabulary.
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
#  10/25/2006  DBM  Initial development
#
###########################################################################

import sys 
import os
import re
import getopt

import rcdlib
import Log
import OBOParser
import vocloadlib
import loadVOC
import db

USAGE = 'Usage:  %s [-n] [-f|-i] [-l <log file>] <RcdFile>' % sys.argv[0]
TERM_ABBR = ''

# Purpose: Write a status to the log, close the log and exit.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def exit (status):
    if status == 0:
        log.writeline('OBO load completed successfully')
    else:
        log.writeline('OBO load failed')

    log.close()

    sys.exit(status)


# Purpose: Initialize global variables.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global validNamespace
    global validRelationshipType, validSynonymType

    # Create a list of namespaces from the RCD file.
    #
    validNamespace = []
    for (key, record) in config.items():
        validNamespace.append(record['NAME_SPACE'])

    # Get the relationship types and synonym types from the database to
    # use for validation.
    #
    cmds = []
    cmds.append('select label ' + \
                'from DAG_Label ' + \
                'where _Label_key > 0')

    cmds.append('select synonymType ' + \
                'from MGI_SynonymType ' + \
                'where _MGIType_key = 13 and ' + \
                      'allowOnlyOne = 0')

    results = db.sql(cmds, 'auto')

    # Create a list of valid relationship types.  Strip out any characters
    # that are non-alphanumeric to allow for a more accurate comparison to
    # values from the input file.
    # These are DAG_Label terms and can represent either a DAG_Edge label i.e.
    # relationship or a DAG_Node label i.e. description
    validRelationshipType = {}
    log.writeline('CODE loadOBO.py loading labels into lookup')
    for r in results[0]:
	log.writeline('CODE loadOBO.py label: %s' % r['label'])
        label = re.sub('[^a-zA-Z0-9]', '', r['label'])
	log.writeline('CODE loadOBO.py regsub label: %s' % label)
        validRelationshipType[label] = r['label']

    # Create a list of valid synonym types.
    #
    validSynonymType = []
    for r in results[1]:
        validSynonymType.append(r['synonymType'])


# Purpose: Open all the input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpOBO, fpValid, fpTerm, fpDAG
    global fpDOmgislim, fpDOgxdslim

    oboFile = os.environ['OBO_FILE']
    validFile = os.environ['VALIDATION_LOG_FILE']
    termFile = os.environ['TERM_FILE']

    # Open the OBO input file.
    #
    try:
        fpOBO = open(oboFile, 'r')
    except:
        log.writeline('Cannot open OBO file: ' + oboFile)
        exit(1)

    # Open the validation log.
    #
    try:
        fpValid = open(validFile, 'w')
    except:
        log.writeline('Cannot open validation log: ' + validFile)
        exit(1)

    # Open the Termfile.
    #
    try:
        fpTerm = open(termFile, 'w')
    except:
        log.writeline('Cannot open term file: ' + termFile)
        exit(1)

    log.writeline('OBO File = ' + oboFile)
    log.writeline('Termfile = ' + termFile)

    # Open a DAG file for each namespace.
    #
    fpDAG = {}
    for (key, record) in config.items():
        dagFile = record['LOAD_FILE']

        try:
            fpDAG[record['NAME_SPACE']] = open (dagFile, 'w')
        except:
            log.writeline('Cannot open DAG file: ' + dagFile)
            exit(1)

        log.writeline('DAG file = ' + dagFile)

    # Open the DO_MGI_slim file.
    #
    if vocabName == 'Disease Ontology':
        try:
            domgislimFile = os.environ['DO_MGI_SLIM_FILE']
            dogxdslimFile = os.environ['DO_GXD_SLIM_FILE']
            fpDOmgislim = open(domgislimFile, 'w')
            fpDOgxdslim = open(dogxdslimFile, 'w')
        except:
            log.writeline('Cannot open DO_MGI_slim/DO_GXD_slim files: ' + domgislimFile)
            exit(1)

# Purpose: Close all the input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():

    fpOBO.close()
    fpValid.close()
    fpTerm.close()

    for i in fpDAG.values():
        i.close()

    try:
        fpDOmgislim.close()
        fpDOgxdslim.close()
    except:
    	pass

# Purpose: Use an OBOParser object to get header/term attributes from the
#          OBO input file and use this information to create the Termfile
#          and DAG file(s).
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def parseOBOFile():
    global vocabName

    vocabName = os.environ['VOCAB_NAME']
    expectedVersion = os.environ['OBO_FILE_VERSION']
    dagRootID = os.environ['DAG_ROOT_ID']
    # default node label
    dag_child_label = ''

    # Open the input and output files.
    #
    openFiles()

    # If there is a root ID for the vocabulary, write it to each DAG file.
    # Even though the root term may be defined in the OBO input file, it
    # will not have any relationships defined, so it would not get added
    # to the DAG file when the term is process below.
    #
    if dagRootID:
	# ignore the 'real' root for Feature Relationship vocab
	if vocabName == 'Feature Relationship':
	    pass
	elif vocabName in ['Marker Category']:
	     fpDAG[validNamespace[0]].write(dagRootID + '\t' + 'show' + '\t' + '\t' + '\n') 
	else:
	    for i in validNamespace:
		fpDAG[i].write(dagRootID + '\t' + '\t' + '\t' + '\n')

    # If the GO vocabulary is being loaded, add the parent obsolete term to
    # the Termfile and associate it to the root ID in the obsolete DAG file.
    #
    if vocabName == 'GO':
        obsoleteTerm = os.environ['OBSOLETE_TERM']
        obsoleteID = os.environ['OBSOLETE_ID']
        obsoleteDefinition = os.environ['OBSOLETE_DEFINITION']
        obsoleteComment = os.environ['OBSOLETE_COMMENT']
        obsoleteNamespace = os.environ['OBSOLETE_NAMESPACE']

        fpTerm.write(obsoleteTerm + '\t' + obsoleteID + '\t' + \
                     'obsolete' + '\t' + TERM_ABBR + '\t' + \
                     obsoleteDefinition + '\t' + obsoleteComment + '\t' + \
                     '\t' + '\t' + '\n')

        fpDAG[obsoleteNamespace].write(obsoleteID + '\t' + '\t' + 'is-a' + \
                                       '\t' + dagRootID + '\n')

    log.writeline('Parse OBO file')

    # Create an OBO parser that will return attributes from the OBO
    # input file.
    #
    parser = OBOParser.Parser(fpOBO, log)

    # Get the header from the parser and save its attributes.
    #
    header = parser.getHeader()
    version = header.getVersion()
    defaultNamespace = header.getDefaultNamespace()

    # If the OBO input file does not have the expected version number,
    # write a validation message and terminate the load.
    #
    if version != expectedVersion:
        log.writeline('Invalid OBO format version: ' + version + \
                      ' (Expected: ' + expectedVersion + ')')
        closeFiles()
        return 1

    # Get the first term from the parser.
    #
    term = parser.nextTerm()

    # Process each term returned by the parser.
    #
    while term != None:

        # Get the attributes of the term.
        #
        termID = term.getTermID()
        name = term.getName()
        namespace = term.getNamespace()
        comment = term.getComment()
        definition = term.getDefinition()
        obsolete = term.getObsolete()
        altID = term.getAltID()
        relationship = term.getRelationship()
        relationshipType = term.getRelationshipType()
        synonym = term.getSynonym()
        synonymType = term.getSynonymType()
	subset = term.getSubset()
        isValid = 1

	if termID == dagRootID and vocabName == 'Feature Relationship':
	    # skip this term
	    term = parser.nextTerm()
	    continue
	    #isValid = 0

	#
	# for EMAPA/EMAPS
	#
	if vocabName == 'EMAPA' and namespace == '':
	    # skip this term
	    term = parser.nextTerm()
	    continue

	#
	# for Disease Ontology
	#
	if vocabName == 'Disease Ontology' and termID.find('DOID:') < 0:
	    # skip this term
	    term = parser.nextTerm()
	    continue

	#
        # Validate the namespace.  The namespace is used to determine which
        # DAG file to write to.  For the GO vocabulary, there are multiple
        # DAGs, so the namespace is required for each term.  For other
        # vocabularies (e.g. MP and MA), the namespace is not defined for
        # each term, so the default namespace from the header is used.
        #

        if vocabName == 'Cell Ontology':
	    namespace = 'cell'
        elif vocabName == 'Evidence Code Ontology':
	    namespace = 'eco'
        elif namespace != '':
            if namespace not in validNamespace:
                fpValid.write('(' + termID + ') Invalid namespace: ' + namespace + '\n')
                isValid = 0
        else:
            if vocabName == 'GO' or vocabName == 'Feature Relationship':
                log.writeline('Missing namespace for term: ' + termID)
                closeFiles()
                return 1
            else:
                namespace = defaultNamespace

	#
        # Validate the relationship type(s).  Strip out any characters that
        # are non-alphanumeric so they can be compared to the values from
        # the database.  This will allow a match on relationship types such
        # "is_a" vs "is-a".
        #
        if vocabName not in ('Cell Ontology'):
        	for r in relationshipType:
            		label = re.sub('[^a-zA-Z0-9]','',r)
            		if not validRelationshipType.has_key(label):
                		fpValid.write('(' + termID + ') Invalid relationship type: ' + r + '\n')
                		isValid = 0

        # Validate the synonym type(s).
        #
        for s in synonymType:
            if s.lower() not in validSynonymType:
                fpValid.write('(' + termID + ') Invalid synonym type: ' + s + '\n')
                isValid = 0

        # If this is the MCV, validate the subset aka Node Label; description of the Node
	dag_child_label = ''
	if vocabName == 'Marker Category' and len(subset) > 0:
	    if len(subset) > 1:
		fpValid.write('(%s) More than one MCV Node Label: \n' % (termID, subset))
                isValid = 0
	    else:
		l = subset[0]
	 	l = re.sub('[^a-zA-Z0-9]','',l)
		if not validRelationshipType.has_key(l):
		    fpValid.write('(%s) Invalid MCV Node Label: %s\n' % (termID, l))
		    isValid = 0
	    if isValid == 1:
		dag_child_label = validRelationshipType[l] 

        # If there are no validation errors, the term can be processed further.
        #
        if isValid:

            # Remove any tabs from the definition, so it does not mess up
            # the formatting of the Termfile.
            #
            definition = re.sub('\t', '', definition)

            # Determine what status to use in the Termfile.
	    # if symbol is obsolete, do not load synonyms (03/16/2017/TR12540)
            #
            if obsolete:
                status = 'obsolete'
	        includeSynonym = ''
		includeSynonymType = ''
            else:
                status = 'current'
		includeSynonym = '|'.join(synonym)
		includeSynonymType = '|'.join(synonymType)

	    if vocabName == 'Human Phenotype Ontology' and status == 'obsolete':
		term = parser.nextTerm()
		continue

            # Write the term information to the Termfile.
            #
            fpTerm.write(name + '\t' + \
                         termID + '\t' + \
                         status + '\t' + \
                         TERM_ABBR + '\t' + \
                         definition + '\t' + \
                         comment + '\t' + \
                         includeSynonym + '\t' + \
                         includeSynonymType + '\t' + \
                         '|'.join(altID) + '\n')

            # If the term name is the same as the namespace AND there is a
            # root ID, write a record to the DAG file that relates this
            # term to the root ID.
            #
            #log.writeline('parseOBOFile:term:' + str(termID) + '\n')
            #log.writeline('parseOBOFile:namespace:' + str(namespace) + '\n')
            #log.writeline('parseOBOFile:dagRootID:' + str(dagRootID) + '\n')

            if vocabName not in ('Cell Ontology'):
            	if name == namespace and dagRootID:
			if vocabName == 'Feature Relationship':
		    		fpDAG[namespace].write(termID + '\t' + '\t' + '\t' +'\n')
		    		term = parser.nextTerm()
		    		continue
			else:
                                #log.writeline('parseOBOFile:fpDAG:1\n')
		    		fpDAG[namespace].write(termID + '\t' + '\t' + 'is-a' + '\t' + dagRootID + '\n')

            	# Write to the DAG file.
                #log.writeline('parseOBOFile:relationships:' + str(len(relationship)) + '\n')
            	for i in range(len(relationship)):
                        #log.writeline('parseOBOFile:fpDAG:2\n')
                	fpDAG[namespace].write(termID + '\t' + \
		    	dag_child_label + '\t' + \
		    	validRelationshipType[re.sub('[^a-zA-Z0-9]','',relationshipType[i])] + '\t' + \
		    	relationship[i] + '\n')

            	# If it is an obsolete GO or term 
	    	# and not the root ID, write it to the obsolete DAG file.
            	#
            	if (vocabName == 'GO') and \
		    	status == 'obsolete' and termID != dagRootID:
                        #log.writeline('parseOBOFile:fpDAG[obsoleteNamespace]\n')
                	fpDAG[obsoleteNamespace].write(termID + '\t' + '\t' + 'is-a' + '\t' + obsoleteID + '\n')
	    #
	    # TR12427/Disease Ontology/subset DO_MGI_slim
	    #
	    if vocabName == 'Disease Ontology' and len(subset) > 0:
		for s in subset:
	    		if s == 'DO_MGI_slim':
	        		fpDOmgislim.write(termID + '\t\n')
	    		if s == 'DO_GXD_slim':
	        		fpDOgxdslim.write(termID + '\t\n')

#	else:
#	    print term.getTermID()
#	    print "isValid error"

        # Get the next term from the parser.
        #
        term = parser.nextTerm()

    closeFiles()
    return 0


#
#  MAIN
#

# Get the options that were passed to the script.
#
try:
    options, args = getopt.getopt(sys.argv[1:], 'nfil:')
except:
    print USAGE
    sys.exit(1)

# After getting the options, only the RCD file should be left in the
# argument list.
#
if len(args) > 1:
    print USAGE
    sys.exit(1)

rcdFile = args[0]

# Process the options to get the mode for the loadVOC module, the "noload"
# indicator and the log file.
#
noload = 0
for (option, value) in options:
    if option == '-f':
        mode = 'full'
    elif option == '-i':
        mode = 'incremental'
    elif option == '-n':
        vocloadlib.setNoload()
        noload = 1
    elif option == '-l':
        log = Log.Log (filename = value, toStderr = 0)
    else:
        pass

if not log:
    log = Log.Log(toStderr = 0)

# Create a configuration object from the RCD file.
#
config = rcdlib.RcdFile (rcdFile, rcdlib.Rcd, 'NAME')

# Perform initialization tasks.
#
initialize()

# Parse the OBO input file.
#
if parseOBOFile() != 0:
    exit(1)

# Invoke the loadVOC module to load the terms and build the DAG(s).
#
vocload = loadVOC.VOCLoad(config, mode, log)
vocload.go()

db.commit()

exit(0)
