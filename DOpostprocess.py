#!/usr/local/bin/python

'''
#
# DOpostprocess.py
#
# Input:
#
# ${OBO_FILE}
#
# What it does:
#
# if the OMIM id has a 'omim_susceptibilty' relationship with the DO term
# then, add OMIM id as a secondar id of the DO term
#
# example:
#
# [Term]
# id: OMIM:000000
# name: omim_susceptibilty
# 
# [Term]
# id: OMIM:608907
# name: Alzheimer's disease 9
# is_a: OMIM:000000 ! omim_susceptibilty
# relationship: RO:0003304 DOID:10652 ! Alzheimers disease
#
# History
#
# 12/07/2016	lec
#	- TR12427/Disease Ontology (DO) project
#
'''

import sys 
import os
import db
import accessionlib
import loadlib

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

# do formatted file
doFileName = None
# do file pointer
doFile = None

# insert statement
INSERT_ACCESSION = '''insert into ACC_Accession 
	values ((select max(_Accession_key) + 1 from ACC_Accession), 
		'%s', '%s', %s, 15, %s, 13, 0, 0)
'''

doFileName = os.environ['OBO_FILE']
doFile = open(doFileName, 'r')

omimIdValue = 'id: OMIM:'
relValue = 'relationship: RO:0003304'
skipValue = 'OMIM:000000'
foundOMIM = 0

for line in doFile.readlines():

    # find [Term]
    # find relationship: RO:0003304

    if line == '[Term]':
        foundOMIM = 0

    elif line[:9] == omimIdValue:
        omimId = line[4:-1]
	if omimId == skipValue:
	    continue
	foundOMIM = 1

    elif foundOMIM and line[:24] == relValue:

        tokens = line[25:-1].split(' ')
	doId = tokens[0]

        prefixPart, numericPart = accessionlib.split_accnum(omimId)
        objectKey = loadlib.verifyObject(doId, 13, None, None, None)
        addSQL = INSERT_ACCESSION % (omimId, prefixPart, numericPart, objectKey)
        db.sql(addSQL, None)

    else:
        continue

doFile.close()
db.commit()
sys.exit(0)

