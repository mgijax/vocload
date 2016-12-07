#!/usr/local/bin/python

'''
#
# DOpostprocess.py
#
# Input:
#
# ${OBO_FILE}
#
# Output:
#
# ACC_Accession input file
#
# to associated OMIM ids with DO ids
# that appear in
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

# do text formatted file
doAccFileName = None
# do text file pointer
doAccFile = None

# insert statement
INSERT_ACCESSION = '''insert into ACC_Accession 
	values ((select max(_Accession_key) + 1 from ACC_Accession), 
		'%s', '%s', %s, 15, %s, 13, 0, 0)
'''

doLookup = {}

def processDO():

    doFileName = os.environ['OBO_FILE']
    doAccFileName = os.environ['DO_ACC_FILE']
    doFile = open(doFileName, 'r')
    doAccFile = open(doAccFileName, 'w')

    idValue = 'id: '
    doIdValue = 'id: OMIM:'
    relValue = 'relationship: RO:0003304'
    foundOMIM = 0

    for line in doFile.readlines():

        # find [Term]
        # find relationship: RO:0003304

        if line == '[Term]':
	    foundOMIM = 0

        elif line[:9] == doIdValue:
            omimId = line[4:-1]
	    if omimId == 'OMIM:000000':
	        continue
	    foundOMIM = 1

        elif foundOMIM and line[:24] == relValue:

            tokens = line[25:-1].split(' ')
	    doId = tokens[0]

            prefixPart, numericPart = accessionlib.split_accnum(omimId)
            objectKey = loadlib.verifyObject(doId, 13, None, None, None)

            addSQL = INSERT_ACCESSION % (omimId, prefixPart, numericPart, objectKey)
	    print addSQL
            db.sql(addSQL, None)

            if doId not in doLookup:
                doLookup[doId] = []
            doLookup[doId].append(omimId)

        else:
            continue

    for d in doLookup:
        doAccFile.write(d + '\t' + doLookup[d][0] + '\n')

    doFile.close()
    doAccFile.close()

    db.commit()

    return doLookup

if __name__ == '__main__':

    doLookup = processDO()

    print 'rows:', len(doLookup)

    for d in doLookup:
        print d, doLookup[d]

