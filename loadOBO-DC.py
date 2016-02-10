#!/usr/local/bin/python

#
# Purpose
#
#	Convert the disease-cluster OBO file to
#	a Synonym-input file (to be used by loadSynonym.sh/py)
#
# Input:
#	The DC-OBO file
#	
#	[Term]
#	=> id: OMIM:615031
#	name: SPASTIC PARAPLEGIA 49, AUTOSOMAL RECESSIVE
#	=> is_a: DC:0000410 ! Spastic paraplegia
#
#	[Term]
#	id: MESH:C537832
#	name: Macular dystrophy, atypical vitelliform
#	=> alt_id: OMIM:153840
#	=> is_a: DC:0000263 ! Macular Dystrophy
#
#	we are only interested in:
#		"id: OMIM:" / "is_a: DC:" for that OMIM id
#		"alt_id: OMIM:" / "is_a: DC:" for that OMIM id
#
# Outpuf:
#	A file in the format for loadSynonym.py
#
#	tab-delimited file:
#		omim id
#		'disease cluster' : name of the disease-cluster synonym type
#		disease-cluster name : from the DC-OBO input file
# History
#
# 12/23/2015	lec
#	- TR11947/change diff2/ignore secondary ids
#

import sys 
import os
import db

# save list to check for duplicates
omimList = set([])

# save list of terms only
omimAllList = set([])

def createSynonymFile():
	#
	# translate the DC-OBO file into a loadSynonym-input file
	#

	global omimList, omimAllList

	outFile = open(os.environ['DCLUSTERSYN_FILE'], 'w')

	omimID = ''
	synonym = ''

	for line in inFile.readlines():
	
		# looking for OMIM id
		if line.find('id: OMIM:') >= 0:
			omimID = line[:-1].split(':')[2].strip()
			omimAllList.add(omimID)

		# ignore obsolete

		if len(omimID) > 0 and line.find('is_obsolete: true') >= 0:
			omimAllList.remove(omimID)
			continue

		# look for cluster-name associated with the most recent OMIM id
		if line.find('is_a: DC:') >= 0:

			synonym = line[:-1].split('!')[1].strip()
	
			# skip
			if synonym == 'Disease Cluster':
				continue

			# skip duplicates
			if (omimID, synonym) in omimList:
				continue

			outFile.write(omimID + '\tdisease cluster\t' + synonym + '\n')
			omimList.add((omimID, synonym))

	outFile.close()
	return 0

def createDiffFile():
	#
	# 1) OMIM terms that exist in MGI but do *not* exists in the OBO-DC file
	# 2) OMIM terms that exist in the OBO-DC file but do *not* exist in MGI
	#

	global omimAllList

	mgiList1 = {}
	mgiList2 = {}

	fp1 = open(os.environ['DCLUSTERDIFF1_FILE'], 'w')
	fp2 = open(os.environ['DCLUSTERDIFF2_FILE'], 'w')

	# check all preferred
	results = db.sql('''
		select a.accID, t.term, a.preferred
		from VOC_Term t, ACC_Accession a 
		where t._Vocab_key = 44
		and t.isObsolete = 0
		and t._Term_key = a._Object_key
		and a._MGIType_key = 13
		and a.preferred = 1
		''', 'auto')

	for r in results:
		mgiList1.setdefault(r['accID'], []).append(r['term'])

	# check all preferred/not preferred
	results = db.sql('''
		select a.accID, t.term, a.preferred
		from VOC_Term t, ACC_Accession a 
		where t._Vocab_key = 44
		and t.isObsolete = 0
		and t._Term_key = a._Object_key
		and a._MGIType_key = 13
		''', 'auto')

	for r in results:
		mgiList2.setdefault(r['accID'], []).append(r['term'])

	# OMIM.clusters.diff1 - OMIM ids in MGI but not in OBO-Disease-Cluster file
	for accID in mgiList1:
		if accID not in omimAllList:
			# write file in OBO-format
			fp1.write('[Term]\n')
			fp1.write('id: OMIM:' + accID + '\n')
			fp1.write('name: ' + mgiList1[accID][0] + '\n')
			fp1.write('is_a: DC:0000138 ! Disease Cluster\n\n')

	# OMIM.clusters.diff2 - OMIM ids in OBO-Disease-Cluster file but not in MGI 
	for accID in omimAllList:
		if accID not in mgiList2:
			fp2.write(accID + '\n')

	fp1.close()
	fp2.close()

	return 0

#
# main
#


inFile = open(os.environ['DCLUSTER_FILE'], 'r')

if createSynonymFile() > 0:
	sys.exit(1)

if createDiffFile() > 0:
	sys.exit(1)

inFile.close()

sys.exit(0)

