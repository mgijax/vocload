#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Split GO OBO file into one OBO file per "namespace".
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	gene_ontology.obo
#
# Output:
#
#	1.  component.obo
#	2.  function.obo
#	3.  process.obo
#
# Processing:
#
# History:
#
# lec	12/19/2005
#	- TR 5677
#
'''

import sys
import os
import string

# globals

TERMTAG = '[Term]'
TYPETAG = '[Typedef]'

oboFileName = os.environ['OBO_FILE']
compFileName = os.environ['OBO_COMPONENT']
funcFileName = os.environ['OBO_FUNCTION']
procFileName = os.environ['OBO_PROCESS']

oboFile = None
compFile = None
funcFile = None
procFile = None

def init():
    #
    # Purpose: initialize global variables, opens files, etc.
    # Returns:
    # Assumes:
    # Effects: 
    # Throws:
    #

    global oboFile, compFile, funcFile, procFile

    try:
	oboFile = open(oboFileName, 'r')
    except:
	print 'Could Not Open File %s' % (oboFileName)
	sys.exit(1)

    try:
	compFile = open(compFileName, 'w')
    except:
	print 'Could Not Create File %s' % (compFileName)
	sys.exit(1)

    try:
	funcFile = open(funcFileName, 'w')
    except:
	print 'Could Not Create File %s' % (funcFileName)
	sys.exit(1)

    try:
	procFile = open(procFileName, 'w')
    except:
	print 'Could Not Create File %s' % (procFileName)
	sys.exit(1)

def writeRecord(namespace, rec):
    #
    # Purpose: write record to appropriate file based on 'namespace'
    # Returns:
    # Assumes:
    # Effects: 
    # Throws:
    #

    if namespace == 'cellular_component':
	outFile = compFile
    elif namespace == 'molecular_function':
	outFile = funcFile
    elif namespace == 'biological_process':
	outFile = procFile

    outFile.write(rec)

def splitOBO():
    #
    # Purpose: split the OBO file into 3 (one per dag)
    # Returns:
    # Assumes:
    # Effects: 
    # Throws:
    #

    rec = ''

    line = oboFile.readline()
    while line:

	if len(line) == 0:
	    line = oboFile.readline()
	    continue

	if string.find(line, TYPETAG) == 0:
	    # read until EOF or new term found
	    line = oboFile.readline()
	    while line:
		if string.find(line, TERMTAG) == 0:
		    break
	        line = oboFile.readline()
            continue

        # new term

        if string.find(line, TERMTAG) == 0:

	    # print previous record
	    if len(rec) > 0:
	        writeRecord(namespace, rec)

	    rec = line

	elif len(rec) > 0:

	    tokens = string.split(line, ':')
	    if tokens[0] == 'namespace':
	        namespace = string.strip(tokens[1])
	    rec = rec + line

        line = oboFile.readline()

    oboFile.close()

    # print last record
    writeRecord(namespace, rec)

#
# Main
#

init()
splitOBO()

