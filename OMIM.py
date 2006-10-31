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
#       OMIM.translation
#	OMIM.special
#	OMIM.exclude
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
import re
import db
import reportlib

# globals

DELIM = '\t'
CRT = '\n'
TERMTYPE = 'T'
PLACEHOLDERTERM = 'OMIM'

activeStatus = 'current'
obsoleteStatus = 'obsolete'
synonymType = 'exact'

omimNew = {}		# OMIM Id:Term that are in the new input file
omimMGI = {}		# OMIM records (id/term) that are currently in MGI
secondaryIds = {}	# OMIM Ids and their secondary Ids (id:list of secondary ids)
excludedIds = []	# OMIM Ids that are to be excluded (skipped)
mimTermToMGI = {}	# TERMTYPE + OMIM ID + OMIM Term:MGI Term
mimWordToMGI = {}	# bad word:good word

def cacheExistingIds():
    #
    # Purpose: cache existing MIM ids so we can detect obsoleted vs. current terms
    # Returns:
    # Assumes:
    # Effects: populates global omimMGI dictionary
    # Throws:
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
    # Purpose: cache all secondary ids (those that have been "MOVED TO")
    # Returns:
    # Assumes:
    # Effects: populates global secondaryIds, omimNew dictionaries
    # Throws:
    #

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
		omimNew[sid] = PLACEHOLDERTERM

        line = inFile.readline()

    inFile.close()

def cacheTranslations():
    #
    # Purpose: cache Term Translations
    # Returns:
    # Assumes:
    # Effects: populates global mimTermToMGI and mimWordToMGI dictionaries
    # Throws:
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

def cacheExcluded():
    #
    # Purpose: cache all excluded ids
    # Returns:
    # Assumes:
    # Effects: populates global excludedIds
    # Throws:
    #

    global excludedIds

    excludedFile = open(excludedFileName, 'r')
    line = excludedFile.readline()
    while line:
        line = line[:-1]
	tokens = string.split(line, '\t')
	id = tokens[0]
	excludedIds.append(id)
        line = excludedFile.readline()
    excludedFile.close()

def convertTerm(mim, term):
    #
    # Purpose: convert OMIM term to MGI-case
    # Parameter: mim, the OMIM id (string)
    # Parameter: term, the OMIM term (string)
    # Returns: the converted term (string)
    # Assumes:
    # Effects: 
    # Throws:
    #

    #
    # mimTermToMGI translations
    #

    translationKey = TERMTYPE + mim + term
    if mimTermToMGI.has_key(translationKey):
	newTerm = mimTermToMGI[translationKey]
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

	elif newTerm[i] in ["-", "/", "@"]:
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
    newTerm = re.sub('@', '', newTerm)

    return newTerm

def writeOMIM(term, mim, synonyms):
    #
    # Purpose: writes OMIM term to MGI-format file
    # Parameter: term, the OMIM Term (string)
    # Parameter: mim, the OMIM ID (string)
    # Parameter: synonyms, the list of synonyms for the OMIM Term (list)
    # Returns:
    # Assumes:
    # Effects: populates global omimNew dictionary
    # Throws:
    #


    global omimNew

    outFile.write(convertTerm(mim, term) + DELIM + mim + DELIM + activeStatus + DELIM + DELIM + DELIM + DELIM + DELIM)
    if secondaryIds.has_key(mim):
	outFile.write(string.join(secondaryIds[mim], '|'))
    outFile.write(CRT)

    for s in synonyms:
	s = string.strip(s)
	if len(s) > 0:
	    synFile.write(mim + DELIM + synonymType + DELIM + convertTerm(mim, s) + CRT)

    # cache the new OMIM ID/Term

    omimNew[mim] = term

def processOMIM():
    #
    # Purpose: process the OMIM input file
    # Returns:
    # Assumes:
    # Effects: 
    # Throws:
    #

    #
    # process each OMIM that we want to load as a vocabulary term
    #

    mim = ''
    term = ''
    synonym = ''
    potentialsynonyms = []
    synonyms = []

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
	    synonym = ''
	    potentialsynonyms = []
	    synonyms = []

        # the term itself

        elif string.find(line, '*FIELD* TI') == 0:

	    # the next line has the data

            line = inFile.readline()
	    tokens = string.split(line[:-1], ' ')

	    # we're only interested in disease terms
	    # exclude all other entries

	    if tokens[0][0] in ['*', '^']:
	        continue

	    # if the term is in our excluded file, we don't want it

	    if mim in excludedIds:
		continue

	    # if the term has been removed, we don't want it
            if string.find(line, ' REMOVED FROM DATABASE') > 0:
		continue

	    # the first token is a repeat of the MIM id, so ignore it

	    term = term + string.join(tokens[1:], ' ')

	    # keep reading until the next field indicator or ; or ;; or an INCLUDE is found, 
	    # signifying the synonyms section

            line = inFile.readline()
	    line = line[:-1]

	    while string.find(term, ';') < 0 \
	    		and string.find(line, ';;') < 0 \
			and string.find(line, '*FIELD* TX') < 0 \
			and string.find(line, '*FIELD* MN') < 0 \
			and string.find(line, 'INCLUDED') < 0:

	        term = term + ' ' + line
                line = inFile.readline()
	        line = line[:-1]

	    #
	    # read all potential synonyms into one string, then split on ;;
	    # exclude any strings that contain "INCLUDE".
	    #

	    while string.find(line, '*FIELD* TX') < 0 and string.find(line, '*FIELD* MN') < 0:
		synonym = synonym + line + ' '
                line = inFile.readline()
	        line = line[:-1]

	    if len(synonym) > 0:
                potentialsynonyms = string.split(synonym, ';;')
		for s in potentialsynonyms:
	            if string.find(s, 'INCLUDED') < 0:
			synonyms.append(s)

        line = inFile.readline()

    inFile.close()

    if len(term) > 0:
        writeOMIM(term, mim, synonyms)

    #
    # Now create records for obsoleted terms...those in omimMGI but not in omimNew
    #

    for m in omimMGI.keys():
        if not omimNew.has_key(m):
            outFile.write(omimMGI[m] + DELIM + m + DELIM + obsoleteStatus + DELIM + DELIM + DELIM + DELIM + DELIM + CRT)

def processQC1():
    #
    # Purpose: 
    # Returns:
    # Assumes:
    # Effects:
    # Throws:
    #

    qc1Title = 'OMIM Terms in the OMIM.translation file that do not exist in the new OMIM file'
    qc1FileName = os.environ['QC1_FILE']
    qc1File = reportlib.init(qc1FileName, title = qc1Title, outputdir = os.environ['RUNTIME_DIR'])

    transTermFile = open(transTermFileName, 'r')
    for line in transTermFile.readlines():
	tokens = string.split(line[:-1], '\t')
	termType = tokens[0]
	mim = tokens[1]
	mimTerm = tokens[2]

	if termType != TERMTYPE:
	    continue

	if omimNew.has_key(mim):
	    if omimNew[mim] != mimTerm:
		qc1File.write(mim + DELIM + mimTerm + DELIM + omimMGI[mim] + CRT)

    transTermFile.close()
    reportlib.finish_nonps(qc1File)

def processQC2():
    #
    # Purpose: 
    # Returns:
    # Assumes:
    # Effects:
    # Throws:
    #

    qc2Title = 'OMIM IDs in the OMIM.translation file that do not exist in the new OMIM file'
    qc2FileName = os.environ['QC2_FILE']
    qc2File = reportlib.init(qc2FileName, title = qc2Title, outputdir = os.environ['RUNTIME_DIR'])

    transTermFile = open(transTermFileName, 'r')
    for line in transTermFile.readlines():
	tokens = string.split(line[:-1], '\t')
	mim = tokens[1]
	mimTerm = tokens[2]

	if not omimNew.has_key(mim):
	    qc2File.write(mim + DELIM + mimTerm + CRT)

    transTermFile.close()
    reportlib.finish_nonps(qc2File)

#
# Main
#

inFileName = os.environ['OMIM_FILE']
outFileName = os.environ['DATA_FILE']
synFileName = os.environ['SYNONYM_FILE']
transTermFileName = os.environ['TRANSTERM_FILE']
transWordFileName = os.environ['TRANSWORD_FILE']
excludedFileName = os.environ['EXCLUDE_FILE']

outFile = open(outFileName, 'w')
synFile = open(synFileName, 'w')

cacheExistingIds()
cacheSecondaryIds()
cacheTranslations()
cacheExcluded()
processOMIM()
processQC1()
processQC2()

outFile.close()
synFile.close()

