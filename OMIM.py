#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Translate OMIM file (mim_title) into tab-delimited format for VOC load
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	mim_title
#	(ftp.ncbi.nih.gov/repository/OMIM/mim_title)
#
# Output:
#
#	omim.in
#
#	mim id
#	term
#
# Processing:
#
# History:
#
# lec	02/04/2003
#	- created
#
'''

import sys
import os
import string

#globals

DELIM = '\t'
CRT = '\n'

omimFileName = 'mim_title'
outFileName= 'omim.tab'

omimFile = open(omimFileName, 'r')
outFile = open(outFileName, 'w')
		
for line in omimFile.readlines():

	tokens = string.split(line[:-1], ' : ')
	mim = tokens[0][1:]
	term = tokens[1]
	outFile.write(mim + DELIM + term + CRT)

