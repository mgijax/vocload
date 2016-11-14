#!/usr/local/bin/python

#
# Program: OMIMdeleteobsolete.py
#
# Purpose:
#
#	To delete obsolete OMIM terms
#
# History
#
#	11/11/2016	lec
#	- TR12427/Disease Ontology (DO)/added OMIMdeleteobsolete.py
#

import sys 
import os
import db

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

# Main
#

db.sql('''
select t._Term_key, t.term
into temporary table toDelete
from VOC_Term t
where t._Vocab_key = 44
and t.isObsolete = 1
and not exists (select 1 from VOC_Annot a
	where a._AnnotType_key in (1005, 1012, 1006, 1020, 1021, 1022)
	and a._Term_key = t._Term_key
	)
and not exists (select 1 from VOC_Annot a
	where a._AnnotType_key in (1018, 1024)
	and a._Object_key = t._Term_key
	)
''', None)

db.sql('create index idx_key on toDelete(_Term_key)')

results = db.sql('select * from toDelete', 'auto')
for r in results:
	print r

results = db.sql('select * from voc_term where _Vocab_key = 44 and isobsolete = 1', 'auto')
for r in results:
	print r

db.sql('delete from VOC_Term v using toDelete o where v._Term_key = o._Term_key', None)
db.commit()

