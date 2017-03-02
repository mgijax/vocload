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
# 03/02/2017	lec
#	- TR12540/do not call this from OMIM.config
#	the OMIM annotations have been removed from the database, so this query is obsolete
#
#	perhaps we may want to re-write this to use the OMIM->DO translation
#

import sys 
import os
import db

# Main
#

db.sql('''
select t._Term_key, t.term
into temporary table toDelete
from VOC_Term t
where t._Vocab_key = 44
and t.isObsolete = 1
and not exists (select 1 from VOC_Annot a
	where a._AnnotType_key in (1005, 1012, 1006)
	and a._Term_key = t._Term_key
	)
and not exists (select 1 from VOC_Annot a
	where a._AnnotType_key in (1018)
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

