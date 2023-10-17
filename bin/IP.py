#
# Purpose:
#
#	Translate InterPro file (names.dat) into tab-delimited format for simpleLoad.py
#
# Assumes:
#
# Side Effects:
#
# Input:
#
#	/data/downloads/ftp.ebi.ac.uk/pub/databases/interpro/names.dat
#
# Output:
#
#	interpro.tab; a tab-delimited file of:
#
#	1. IP term
#	2. IP ID
#	3. Status
#	4. Abbreviation (none)
#	5. Definition (none)
#	6. Comment (none)
#	7. Synonyms (none)
#	8. Seconrdary IDs (none)
#

import sys
import os

DELIM = '\t'
CRT = '\n'
status = 'current'

inFileName = os.environ['IP_FILE']
outFileName = os.environ['DATA_FILE']

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
                
for line in inFile.readlines():
        accID = line[:9]
        term = line[10:-1]
        outFile.write(term + DELIM + accID + DELIM + status + DELIM + DELIM + DELIM + DELIM + DELIM + CRT)
