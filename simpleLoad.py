#!/usr/local/bin/python

import sys
import os

import vocloadlib
import loadWrapper
import tempfile

class IP_Wrapper (loadWrapper.LoadWrapper):
	def preProcess (self):
		datafile = vocloadlib.readTabFile (self.inputFile,
			[ 'term', 'abbrev', 'definition', 'blank' ])

		self.loadfile = self.config.getConstant('TERM_FILE')
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
	wrapper = IP_Wrapper (sys.argv[1:])
	wrapper.go()
