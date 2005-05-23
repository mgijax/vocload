#!/usr/local/bin/python

'''
#
# Purpose:
#
#	Translate OMIM file into tab-delimited format for simpleLoad.py
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	omim.txt
#
# Output:
#
#	OMIM.tab; a tab-delimited file of:
#
#	1. OMIM term
#	2. OMIM ID
#	3. Status
#	4. Abbreviation (none)
#	5. Definition (none)
#	6. Comment (none)
#	7. Synonyms (none, using OMIM.synonym)
#	8. Secondary Ids
#
# Processing:
#
# History:
#
# lec	04/13/2005
#	- TR 3853, OMIM
#
'''

import sys
import os
import string
import regsub
import db

#globals

DELIM = '\t'
CRT = '\n'
TERMTYPE = 'T'

activeStatus = 'current'
obsoleteStatus = 'obsolete'
synonymType = 'exact'

omimNew = []		# OMIM ids that are in the new input file
omimMGI = {}		# OMIM records (id/term) that are currently in MGI
secondaryIds = {}
mimTermToMGI = {}	# TERMTYPE + OMIM ID + OMIM Term/MGI Term
mimWordToMGI = {}	# bad word/good word

def cacheExistingIds():

    #
    # cache existing MIM ids so we can detect obsoleted vs. current terms
    #

    global omimMGI

    results = db.sql('select a.accID, t.term ' + \
	'from ACC_Accession a, VOC_Term t ' + \
	'where a._LogicalDB_key = %s ' % (os.environ['LOGICALDB_KEY']) + \
	'and a._MGIType_key = 13 ' + \
	'and a._Object_key = t._Term_key', 'auto')
    for r in results:
        omimMGI[r['accID']] = r['term']

def cacheSecondaryIds():

    #
    # cache all secondary ids (those that have been "MOVED TO")
    #

    global omimNew
    global secondaryIds

    inFile = open(inFileName, 'r')
    line = inFile.readline()
    while line:
        line = line[:-1]

	# this term has been moved and is now a secondary id of another term

        if string.find(line, ' MOVED TO') > 0:
	    tokens = string.split(line, ' ')

	    if tokens[0][0] == '^' and tokens[1] == 'MOVED':
	        key = tokens[3]	# the mim id of the term this id is a secondary of...
	        sid = tokens[0][1:] # the secondary id
	        if not secondaryIds.has_key(key):
	            secondaryIds[key] = []
	        secondaryIds[key].append(sid)
	        omimNew.append(sid)

        line = inFile.readline()

    inFile.close()

def cacheTranslations():

    #
    # cache Term Translations
    #

    global mimTermToMGI, mimWordToMGI

    transTermFile = open(transTermFileName, 'r')
    for line in transTermFile.readlines():
	tokens = string.split(line[:-1], '\t')
	termType = tokens[0]
	mim = tokens[1]
	mimTerm = tokens[2]
	mgiTerm = tokens[3]
	mimTermToMGI[termType + mim + mimTerm] = mgiTerm
    transTermFile.close()

    transWordFile = open(transWordFileName, 'r')
    for line in transWordFile.readlines():
	tokens = string.split(line[:-1], '\t')
	mimWord = tokens[0]
	mgiWord = tokens[1]
	mimWordToMGI[mimWord] = mgiWord
    transWordFile.close()

def convertTerm(mim, term):

    #
    # mimTermToMGI translations
    #

    if mimTermToMGI.has_key(TERMTYPE + mim + term):
	newTerm = mimTermToMGI[TERMTYPE + mim + term]
	return newTerm

    # capitialize all words
    newTerm = string.capwords(term)

    #
    # capitalize any word after certain punctuation ("--", "-", "/")
    #

    newnewTerm = ''
    capNextTerm = 0
    for i in range(len(newTerm)):

	if i == 0 or capNextTerm:
	    newnewTerm = newnewTerm + string.capitalize(newTerm[i])
	    capNextTerm = 0

	# double-dash

	elif newTerm[i] == '-' and newTerm[i+1] == '-':
	    newnewTerm = newnewTerm + newTerm[i]

	# capitalize the word after any of these punctuation...

	elif newTerm[i] in ['-', '/']:
	    newnewTerm = newnewTerm + newTerm[i]
	    capNextTerm = 1

        else:
	    newnewTerm = newnewTerm + newTerm[i]
	    
    newTerm = newnewTerm

    #
    # substitute words in the mimWordToMGI dictionary
    #

    tokens = string.split(newTerm, ' ')
    newTokens = []
    for t in tokens:
        if mimWordToMGI.has_key(t):
            newTokens.append(mimWordToMGI[t])
	else:
	    newTokens.append(t)
    newTerm = string.join(newTokens, ' ')

    # fully capitilize any word after the ; because this is the human gene

    tokens = string.split(newTerm, '; ')
    newTokens = []
    newTokens.append(tokens[0])
    for t in tokens[1:]:
	newTokens.append(string.upper(t))
    newTerm = string.join(newTokens, '; ')

    #
    # get rid of the @ character
    #
    newTerm = regsub.gsub('@', '', newTerm)

    return newTerm

def writeOMIM(term, mim, synonyms):

    global omimNew

    outFile.write(convertTerm(mim, term) + DELIM + mim + DELIM + activeStatus + DELIM + DELIM + DELIM + DELIM + DELIM)
    if secondaryIds.has_key(mim):
	outFile.write(string.join(secondaryIds[mim], '|'))
    outFile.write(CRT)

    for s in synonyms:
	newSyn = regsub.gsub(';;', '', s)
	synFile.write(mim + DELIM + synonymType + DELIM + convertTerm(mim, newSyn) + CRT)

    omimNew.append(mim)

def processOMIM():

    #
    # process each OMIM that we want to load as a vocabulary term
    #

    mim = ''
    term = ''
    synonyms = []
    continueTerm = 0
    continueSynonym = 1

    inFile = open(inFileName, 'r')
    line = inFile.readline()
    while line:

        line = line[:-1]

        # this means we've found a new term

        if string.find(line, '*FIELD* NO') == 0:

	    # print previous term
	    if len(term) > 0:
	        writeOMIM(term, mim, synonyms)

            line = inFile.readline()
	    mim = string.strip(line)
	    term = ''
	    synonyms = []
	    continueTerm = 0
	    continueSynonym = 1

        # the term itself

        elif string.find(line, '*FIELD* TI') == 0:

            line = inFile.readline()
            line = line[:-1]
	    tokens = string.split(line, ' ')

	    # we're only interested in disease terms
	    # exclude all other entries

	    if tokens[0][0] in ['*', '^']:
	        continue

	    # the first token is a repeat of the MIM id, so ignore it

	    term = term + string.join(tokens[1:], ' ')

	    if string.find(line, ';') < 0:
	        continueTerm = 1

        elif string.find(line, '*FIELD* TX') == 0 or string.find(line, '*FIELD* MN') == 0:
	    continueTerm = 0
	    continueSynonym = 0

        elif continueTerm:

	    # next line may be a continuation of the term or synonym.

	    if string.find(line, ';') >= 0 or \
	       string.find(line, '*') == 0:
	        continueTerm = 0
	        if continueSynonym and string.find(line, 'INCLUDED') < 0:
	            synonyms.append(line)

	    else:
	        term = term + ' ' + line

        elif continueSynonym:
	    if string.find(line, 'INCLUDED') < 0:
	        synonyms.append(line)

        line = inFile.readline()
    inFile.close()

    if len(term) > 0:
        writeOMIM(term, mim, synonyms)

    #
    # Now create records for obsoleted terms...those in omimMGI but not in omimNew
    #

    for m in omimMGI.keys():
        if m not in omimNew:
            outFile.write(omimMGI[m] + DELIM + m + DELIM + obsoleteStatus + DELIM + DELIM + DELIM + DELIM + DELIM + CRT)

#
# Main
#

inFileName = os.environ['OMIM_FILE']
outFileName = os.environ['DATA_FILE']
synFileName = os.environ['SYNONYM_FILE']
transTermFileName = os.environ['TRANSTERM_FILE']
transWordFileName = os.environ['TRANSWORD_FILE']

outFile = open(outFileName, 'w')
synFile = open(synFileName, 'w')

cacheExistingIds()
cacheSecondaryIds()
cacheTranslations()
processOMIM()

outFile.close()
synFile.close()

