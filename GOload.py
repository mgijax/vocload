#!/usr/local/bin/python

'''
#
# History
#
# 03/21/2006 lec
#	- TR 5677; preProcessText vs. preProcessOBO
#
# 04/02/2003 lec
#	- TR 4564; added support for comments (getComment())
#
# 08/26/2002 lec
#	- TR 3809 (adding support for processing Phenotype vocabulary in GO format)
#	- added call to govocab.initializeRegExps (os.environ['ACC_PREFIX'])
#	- modified setID() to : self.name = os.environ['VOCAB_NAME']
#
'''

import sys
import os
import string

import loadWrapper
import GOVocabText

def textEdgeType (char):
        if char == '%':
                return 'is-a'
        else:                   # char == '<'
                return 'part-of'

class GO_Wrapper (loadWrapper.LoadWrapper):
        USAGE = '''%s [-f|-i][-n][-l <file>] <RcdFile>
        -f | -i : full load or incremental load? (default is full)
        -n      : use no-load option (log changes, but don't execute them)
        -l      : name of the log file to create (default is stderr only)
        RcdFile : name of the RcdFile-formatted configuration file to read
''' % sys.argv[0]

        NUM_ARGS = 1

	term_fp = None	# output Term File

        def preProcess (self):

                self.term_fp = open (os.environ['TERM_FILE'], 'w')

		fileFormat = os.environ['ONTOLOGY_FILE_FORMAT']

		if fileFormat == 'Text':
			self.preProcessText()
		else:
			self.preProcessOBO()

                self.term_fp.close()

		return

	def preProcessText(self):

                defs_file = os.environ['DEFS_FILE']

                for (key, dag) in self.config.items():

                        self.log.writeline ('Pre-processing %s to create %s' % (dag['ONTOLOGY_FILE'], dag['LOAD_FILE']))

                        govocab = GOVocabText.GOVocabText ()
			govocab.initializeRegExps(os.environ['ACC_PREFIX'])
                        govocab.buildVocab(defs_file, dag['ONTOLOGY_FILE'])

			self.writeDAGTerms(govocab, dag)

	def preProcessOBO(self):

                for (key, dag) in self.config.items():

                        self.log.writeline ('Pre-processing %s to create %s' % (dag['ONTOLOGY_FILE'], dag['LOAD_FILE']))

#                        govocab = GOVocabOBO.GOVocabOBO ()
#			govocab.initializeRegExps(os.environ['ACC_PREFIX'])
#                        govocab.buildVocabOBO(dag['ONTOLOGY_FILE'])

			self.writeDAGTerms(govocab, dag)

	def writeDAGTerms(self, govocab, dag):

		to_do = []	# [ (parent, [ (child, edge type), ... ]), ... ]
        	done = {}       # acc ID -> 1 if added already
        	obsolete = {}   # primary IDs of obs. terms

        	dag_fp = open (dag['LOAD_FILE'], 'w')

                to_do = [ ('', [(govocab.getRoot(), '') ] ) ]
		done = {}	# acc ID -> 1 if added already
		obsolete = {}	# primary IDs of obs. terms

                while to_do:

        		parent, children = to_do[0]
                	del to_do[0]

                	for child, edge_type in children:
                		childID = child.getId()

                 		# a child is obsolete if its parent is
                 		# obsolete or if its label is 'obsolete'.
                 		# otherwise, it's current.

                		if parent and obsolete.has_key(parent):
                        		status = 'obsolete'
                        		obsolete[childID] = 1
				elif string.find(child.getLabel(), 'obsolete') >= 0:
                        		status = 'obsolete'
                        		obsolete[childID] = 1
                		elif child.getLabel() == 'obsolete':
                        		status = 'obsolete'
                 			obsolete[childID] = 1
                        	else:
                        		status = 'current'

                        	if not done.has_key(childID):
                        		self.term_fp.write (loadWrapper.TERM_LINE % (child.getLabel(),
                        			childID,
                        			status,
                        			'',             # abbrev
                        			child.getDefinition(),
                        			child.getComment(),
                        			string.join (child.getSynonyms(), '|'), #'' ))
                        			string.join ( child.getSecondaryGOIDs(), '|' ))) # 2ndary IDs
                        		done[childID] = 1
                        		to_do.append ((childID, govocab.getChildrenOf(child)))

                        	if parent:
                        		dag_fp.write (loadWrapper.DAG_LINE % (childID, '', textEdgeType (edge_type), parent))
                        	else:
                        		# child is parent-less (root) node:
                        		dag_fp.write (loadWrapper.DAG_LINE % (childID, '', '', ''))

                dag_fp.close()
                return

        def setID (self):
                self.name = os.environ['VOCAB_NAME']
                return

if __name__ == '__main__':
        wrapper = GO_Wrapper (sys.argv[1:])
        wrapper.go()

