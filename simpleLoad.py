#!/usr/local/bin/python

# $HEADER$
# $NAME$

#
# Program: simpleLoad.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To load a simple, non-strucuted vocabulary into MGI VOC tables
#
# Requirements Satisfied by This Program:
#
# Usage:
#
# Envvars:
#
# Inputs:
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

import sys
import os

import vocloadlib
import loadWrapper
import tempfile

class SimpleVoc_Wrapper (loadWrapper.LoadWrapper):
	def preProcess (self):
		datafile = vocloadlib.readTabFile (self.inputFile,
			[ 'term', 'abbrev', 'definition', 'blank' ])

		self.loadfile = os.environ['TERM_FILE']
		fp = open (self.loadfile, 'w')

		for row in datafile:
			fp.write (loadWrapper.TERM_LINE % (
				row['term'],
				'',			# acc ID
				'current',
				row['abbrev'],
				row['definition'],
				'',			# synonyms
				''			# secondary IDs
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

