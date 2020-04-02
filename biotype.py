
'''
#
# Purpose:
#
#	Translate file into tab-delimited format for simpleLoad.py
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	see bioptype_ensembl.config, biotype_ncbi.config
#
# Output:
#
#	biotype_??.txt; a tab-delimited file of:
#
#	1. biotype term
#	2. biotype id (none)
#	3. Status (current)
#	4. Abbreviation (none)
#	5. Definition (none)
#	6. Comment (none)
#	7. Synonyms (none)
#	8. Secondary IDs (none)
#
# Processing:
#
# History:
#
'''

import sys
import os
import string

#globals

DELIM = '\t'
CRT = '\n'
status = 'current'

inFileName = os.environ['BIOTYPE_FILE']
outFileName = os.environ['DATA_FILE']

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
                
for line in inFile.readlines():

        tokens = line[:-1].split(DELIM)

        try:
                term = tokens[1]
                outFile.write(term + DELIM + DELIM + status + DELIM + DELIM + DELIM + DELIM + DELIM + CRT)
        except:
                pass
