#!/usr/local/bin/python

# $Header$
# $Name$

#
# Program: simpleLoad.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To load a simple, non-structured vocabulary into MGI VOC tables
#
# Requirements Satisfied by This Program:
#
# Usage:
#
# Envvars:
#
# Inputs:
#
#	Tab-delimited file with these columns:
#
#	term
#	accession id
#	status
#	abbreviation
#	definition
#	comment
#	synonyms (|-delimited)
#	secondary ids (|-delimited)
#
#	accession id, abbreviation, definition, comment, synonyms secondary ids can be blank
#
# Outputs:
#
# Exit Codes:
#
# Assumes:
#
# Bugs:
#
# Implementation:
#
#    Modules:
#
# Modification History
#
# 04/29/2005	lec
#	- OMIM, added support for status
#
# 04/03/2003	lec
#	- TR 4564; added support for comments
#

import sys
import os

import vocloadlib
import loadWrapper
import tempfile

class SimpleVoc_Wrapper (loadWrapper.LoadWrapper):
	def preProcess (self):
		datafile = vocloadlib.readTabFile (self.inputFile,
			[ 'term', 'id', 'status', 'abbrev', 'definition' , 'comment', 'synonyms', 'secondaryids' ])

		self.loadfile = os.environ['TERM_FILE']
		fp = open (self.loadfile, 'w')

		for row in datafile:
			fp.write (loadWrapper.TERM_LINE % (
				row['term'],
				row['id'],
				row['status'],
				row['abbrev'],
				row['definition'],
				row['comment'],
				row['synonyms'],
				row['secondaryids']
			        ))	
		fp.close()
		return

	def postProcess (self):
		os.remove (self.loadfile)
		return

	def setID (self):
		self.name = os.environ['VOCAB_NAME']
		return

if __name__ == '__main__':
	wrapper = SimpleVoc_Wrapper (sys.argv[1:])
	wrapper.go()

# $Log$
# Revision 1.8  2005/04/29 12:31:32  lec
# OMIM
#
# Revision 1.7  2003/04/18 14:46:07  lec
# MGI 2.96
#
# Revision 1.6  2003/04/02 18:54:49  lec
# TR 4564
#
# Revision 1.5  2003/04/02 13:28:53  lec
# TR 4564
#
# Revision 1.4  2003/03/25 19:01:24  lec
# new Configuration files
#
# Revision 1.3  2003/03/25 18:41:12  lec
# new Configuration files
#

