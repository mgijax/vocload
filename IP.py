#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Translate InterPro file (names.dat) into tab-delimited format for simpleLoad.py
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	/data/downloads/ftp.ebi.ac.uk/pub/databases/interpro/names.dat
#
# Output:
#
#	interpro.tab; a tab-delimited file of:
#
#	IP term
#	IP ID
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

inFileName = os.environ['IP_FILE']
outFileName = os.environ['DATA_FILE']

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
		
for line in inFile.readlines():

	accID = line[:9]
	term = line[10:-1]
	outFile.write(term + DELIM + accID + DELIM + DELIM + CRT)

