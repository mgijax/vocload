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
#	OMIM term
#	OMIM ID
#	Abbreviation
#	Definition
#	Comment
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

inFileName = os.environ['OMIM_FILE']
outFileName = os.environ['DATA_FILE']

def convertTerm(term):

    # capitialize all words
    newTerm = string.capwords(term)

    # get rid of double ;;
    newTerm = regsub.gsub(';;', '', newTerm)

    #
    # capitalize any word after certain punctuation
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

	# -@

	elif newTerm[i] == '-' and newTerm[i+1] == '@':
	    newnewTerm = newnewTerm + newTerm[i]

	# capitalize the word after any of these punctuation...

	elif newTerm[i] in ['-', '/', '@']:
	    newnewTerm = newnewTerm + newTerm[i]
	    capNextTerm = 1

        else:
	    newnewTerm = newnewTerm + newTerm[i]
	    
    newTerm = newnewTerm

    # lowercase certain words
    # uppercase certain words (roman numerals, etc.)

    tokens = string.split(newTerm, ' ')
    newTokens = []
    for t in tokens:
        if t in ['And', 'Or', 'But', 'With', 'Without', 'Of', 'The', 'At', 'In', 'To', 'On', 'For']:
            newTokens.append(string.lower(t))
        elif t in ['Ii', 'Ii;', 'Ii,', 'Iii', 'Iii;', 'I/Iix', 'Ii/Iii,', 'Iiia', 'Iiia;', 'Iiib', 'Iiic', 'Iiid', 'Iv', 'Iv;', 'Iv,', 'Iva', 'Ivb', 'Vi', 'Vii' , 'Vii;', 'Viii', 'x', 'Ia', 'Ib', 'Ic', 'Id', 'Ie', 'If', 'Ig', 'Ih', 'Ij', 'Ik', 'Il', 'Ix', 'Ia;', 'Ib;', 'Ic;', 'Ie;', 'If;', 'Ig;', 'Iia', 'Iia,', 'Iib', 'Iic', 'Iic,', 'Iid', 'Iid,', 'Iie', 'Ixc', 'Iia;', 'Iib;', 'Iic;', 'Iii;', 'Xx', 'Xy', 'Pa', 'Rh-Null', 'Uv', 'Rna', 'Rna,', 'Dna', 'Dna,', '1a;', '1b;', '1c;', '1d;', '1e;', '1f', '1f;', '1g;', '1h;', '1i;', '1j;', '1k;', '1l;', '1m;', '1n;', '2a', '2a;', '2a1;', '2a2', '2a2;', '2b', '2b;', '2b1', '2b1;', '2b2', '2b2;', '2d;', '2e', '2e;', '2f', '2f;', '2g;', '2h', '2h;', '2i', '2i;', '2j', '2j;', '2k', '2l', '3a;', '4a;', '4b1', '4b2', '4c', '4d;', '(2a)', '11b;', '5a,', '5b,', 'Xib,', 'C-Ii', 'Abo', 'Xg', 'Xh', 'Xm', 'Xp24', 'Xp37', 'Xp40', 'Atp', 'Atpaf2', 'Icam1', 'Cd3', 'Cd4', 'Cd4/Cd8', 'Cd59', 'Ceh10', 'Rd114']:
	    newTokens.append(string.upper(t))
        elif t in humanSymbol:
	    newTokens.append(string.upper(t))
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
    # things that don't fit into any of the above categories
    #

    newTerm = regsub.gsub('Abcd Syndrome', 'ABCD Syndrome', newTerm)
    newTerm = regsub.gsub('Adult Syndrome', 'ADULT Syndrome', newTerm)
    newTerm = regsub.gsub('Fg Syndrome', 'FG Syndrome', newTerm)
    newTerm = regsub.gsub('Acth Deficiency', 'ACTH Deficiency', newTerm)
    newTerm = regsub.gsub('Uv-', 'UV-', newTerm)
    newTerm = regsub.gsub('-Coa', '-CoA', newTerm)
    newTerm = regsub.gsub('Coq-', 'CoQ-', newTerm)
    newTerm = regsub.gsub('Syndrome Vib', 'Syndrome VIb', newTerm)
    newTerm = regsub.gsub('Group--Abh', 'Group--ABH', newTerm)
    newTerm = regsub.gsub('Group--Abo', 'Group--ABO', newTerm)
    newTerm = regsub.gsub('Group--Lke', 'Group--LKE', newTerm)
    newTerm = regsub.gsub('Group--Mn', 'Group--MN', newTerm)
    newTerm = regsub.gsub('Group--Ok', 'Group--OK', newTerm)
    newTerm = regsub.gsub('Group--Ss', 'Group--SS', newTerm)
    newTerm = regsub.gsub('Group--Ul', 'Group--UL', newTerm)
    newTerm = regsub.gsub('Group--Yt', 'Group--YT', newTerm)
    newTerm = regsub.gsub('Oncogene Trk', 'Oncogene TRK', newTerm)
    newTerm = regsub.gsub('Atp-Binding', 'ATP-Binding', newTerm)
    newTerm = regsub.gsub('-Like', '-like', newTerm)

    return newTerm

#
# Main
#

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
		
mim = ''
term = ''
continueTerm = 0

humanSymbol = []
results = db.sql('select symbol from MRK_Marker where _Organism_key = 2', 'auto')
for r in results:
    humanSymbol.append(r['symbol'])

line = inFile.readline()
while line:

    line = line[:-1]

    # this means we've found a new term

    if string.find(line, '*FIELD* NO') == 0:

	# print previous term
	if len(term) > 0:
            outFile.write(convertTerm(term) + DELIM + mim + DELIM + DELIM + DELIM + CRT)

        line = inFile.readline()
	mim = string.strip(line)
	term = ''
	continueTerm = 0

    # the term itself

    elif string.find(line, '*FIELD* TI') == 0:

        line = inFile.readline()
        line = line[:-1]
	tokens = string.split(line, ' ')

	# we're only interested in disease terms
	# exclude all other entries

#	if tokens[0][0] in ['*', '+', '^']:
	if tokens[0][0] in ['*', '^']:
	    continue

	# the first token is a repeat of the MIM id, so ignore it

	term = term + string.join(tokens[1:], ' ')

	if string.find(line, ';') < 0:
	    continueTerm = 1

    elif continueTerm:

	# next line may be a continuation of the term
	# or synonyms.  ignore synonyms (for now)

	if string.find(line, ';') >= 0 or \
	   string.find(line, '*') == 0 or \
	   string.find(line, 'INCLUDED') >= 0:
	    continueTerm = 0
	else:
	    term = term + ' ' + line

    line = inFile.readline()

if len(term) > 0:
    outFile.write(convertTerm(term) + DELIM + mim + DELIM + DELIM + DELIM + CRT)

