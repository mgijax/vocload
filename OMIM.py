#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Translate OMIM file (mim_title) into tab-delimited format for simpleLoad.py
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	/data/downloads/ftp.ncbi...
#
# Output:
#
#	OMIM.tab; a tab-delimited file of:
#
#	OMIM term
#	OMIM ID
#	Abbreviation
#	Definition
#
# Processing:
#
# History:
#
# lec	03/25/2003
#	- created
#
'''

import sys
import os
import string
import regsub

#globals

DELIM = '\t'
CRT = '\n'

inFileName = os.environ['OMIM_FILE']
outFileName = os.environ['DATA_FILE']

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
		
for line in inFile.readlines():

	tokens = string.split(line[:-1], ' : ')
	mim = tokens[0][1:]
	term = tokens[1]
	outFile.write(term + DELIM + mim + DELIM + DELIM + CRT)

