#!/usr/local/bin/python

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

