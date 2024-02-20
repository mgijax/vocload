#
# Purpose:
#
#	Translate GlyGen file into tab-delimited format for simpleLoad.py
#
# Input:
#
#	/data/downloads/data.glygen.org/ln2data/releases/data/current/reviewed/protein_glygen_mgi_xref_mapping.tsv
#
#       1. uniprotkb_ac
#       2. mgi_id  
#       3. glycosylation_annotation        
#       4. url
#
# Output:
#
#	GlyGen.tab; a tab-delimited file of:
#
#	1. GlyGen term  : 3
#	2. UniProt ID   : 1
#	3. Status       : current
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

inFileName = os.environ['GLYGEN_FILE']
outFileName = os.environ['DATA_FILE']

inFile = open(inFileName, 'r')
outFile = open(outFileName, 'w')
                
for line in inFile.readlines():

        tokens = line[:-1].split(DELIM)

        accID = tokens[0]
        mgiID = tokens[1]
        term = tokens[2]

        if accID == "uniprotkb_ac":
                continue

        # add sanity checks

        outFile.write(term + DELIM + accID + DELIM + status + DELIM + DELIM + DELIM + DELIM + DELIM + CRT)
