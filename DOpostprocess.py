#!/usr/local/bin/python

'''
#
# DOpostprocess.py
#
# 1: process susceptibility terms
#
# 2: sanity check DO slim
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

#
# process susceptibility terms
#
# Input:
# ${OBO_FILE}
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
def processSusceptibility():

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
    return 0

#
# sanity check the DO slim terms
#
# if a DO slim term T is a desendant of another slim term S, then
#     . report T
#     . delete T from the DO slim set
#
def processSlim():

    dosanityFileName = os.environ['DO_SLIM_SANITYCHECK_FILE']
    dosanityFile = open(dosanityFileName, 'w')

    DELETE_SLIM = 'delete from MGI_SetMember where _Set_key = 1048 and _SetMember_key = %s'
    SPACE = ' '
    
    dosanityFile.write('\n\nDO slim terms that are decendents of another DO slim term\n\n')
    dosanityFile.write('descendent_term' + 35*SPACE + 'another_slim_term\n')
    dosanityFile.write('---------------' + 35*SPACE + '-----------------\n\n')

    results = db.sql('''
               select tt.term as descendent_term, ss.term as another_slim_term, t._SetMember_key
               from MGI_SetMember t, DAG_Closure dc, MGI_SetMember s, VOC_Term tt, VOC_Term ss
               where t._Set_key = 1048
               and t._Object_key = dc._DescendentObject_key
               and dc._AncestorObject_key = s._Object_key
               and s._Set_key = 1048
               and t._Object_key != s._Object_key
               and t._Object_key = tt._Term_key
               and s._Object_key = ss._Term_key
       ''', 'auto')

    for r in results:
	dosanityFile.write('%-50s %-50s\n' % (r['descendent_term'], r['another_slim_term']))
	deleteSQL = DELETE_SLIM % (r['_SetMember_key'])
	#dosanityFile.write(deleteSQL + '\n\n')
        db.sql(deleteSQL, None)

    dosanityFile.close()
    db.commit()
    return 0

#
# main
#

if processSusceptibility() != 0:
    sys.exit(1)

if processSlim() != 0:
    sys.exit(1)

sys.exit(0)

