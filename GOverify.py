#!/usr/local/bin/python

#
# Program: GOverify.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Verify the GO files can be parsed
#
# Requirements Satisfied by This Program:
#
# Usage:
#
#	GOverify.py
#
# Envvars:
#
#	RUNTIME_DIR		the directory where the data files reside
#	VERIFY_LOG_FILE		the file to use for logging errors raised by this program
#	RCD_FILE		the name of the RCD config file
#
# Inputs:
#
#	None
#
# Outputs:
#
#	VERIFY_LOG_FILE
#
# Exit Codes:
#
#	0 if success
#	1 if failure
#
# Assumes:
#
#	the ontology files defined in the RCD_FILE exist in
#	the RUNTIME_DIR directory
#
# Bugs:
#
# Implementation:
#
#	for each ontology file defined in the RCD_FILE
#		if the file can be parsed
#			then no error
#		else 
#			raise error
#
#    Modules:
#
# Modification History
#
#	03/27/2003	lec
#	- converted from GOdownloader.py to just do the file verification
#	- generalized the code so that it can be used to verify any set
#	  of ontology files in GO format
#

import sys
import os
import GOVocab
import rcdlib

ParseError = 'Error parsing input file:  '
data_dir = os.environ['RUNTIME_DIR']
logFile = os.environ['VERIFY_LOG_FILE']
rcdFile = os.environ['RCD_FILE']

try:
    errLog = open(logFile, 'w')
    config = rcdlib.RcdFile(rcdFile, rcdlib.Rcd, 'NAME')

    for (key, dag) in config.items():
	fileName = dag['ONTOLOGY_FILE']
        fp = open(fileName, 'r')

        try:
            GO = GOVocab.GOVocab()
	    GO.initializeRegExps ("GO")
            dag = GO.parseGOfile(fp)
            fp.close()
            del dag
        except:
            fp.close()
            raise ParseError, fileName

except ParseError, message:
    errLog.write(ParseError + message + '\n')
    sys.exit(1)

except:
    errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
    sys.exit(1)

errLog.write(sys.argv[0] + ' completed successfully.\n')
errLog.close()
sys.exit(0)
