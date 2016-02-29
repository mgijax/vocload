#!/bin/sh -f

if [ "${MGICONFIG}" = "" ]
then
    MGICONFIG=/usr/local/mgi/live/mgiconfig
    export MGICONFIG
fi

. ${MGICONFIG}/master.config.sh

LOG=$0.log
rm -rf $LOG
touch $LOG
 
PRELOG=$0.prelog
rm -rf $PRELOG
touch $PRELOG
 
POSTLOG=$0.postlog
rm -rf $POSTLOG
touch $POSTLOG
 
date | tee -a $LOG
 
#echo 'some sanity checking tests...'
#${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_oboonly_test.txt
#mv emapFatalQC.rpt emapFatalQC.oboonly.rpt
#mv emapWarningQC.rpt emapWarningQC.oboonly.rpt
#${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_nonoboonly_test.txt
#mv emapFatalQC.rpt emapFatalQC.nonoboonly.rpt
#mv emapWarningQC.rpt emapWarningQC.nonoboonly.rpt
#${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_withannotations_test.txt
#mv emapFatalQC.rpt emapFatalQC.withannotations.rpt
#mv emapWarningQC.rpt emapWarningQC.withannotations.rpt
#${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_truncatedfile_test.txt
#mv emapFatalQC.rpt emapFatalQC.truncatefile.rpt
#mv emapWarningQC.rpt emapWarningQC.truncatefile.rpt
#exit 0

runQuery ()
{
cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0

select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 90 and isObsolete = 0;
select count(*) from VOC_Term where _Vocab_key = 90 and isObsolete = 1;
select count(*) from VOC_Term_EMAPA;
select count(*) from DAG_Closure where _dag_key = 13;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key = 13;

select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 91 and isObsolete = 0;
select count(*) from VOC_Term where _Vocab_key = 91 and isObsolete = 1;
select count(*) from VOC_Term_EMAPS;
select count(*) from DAG_Closure where _dag_key between 14 and 42;
select count(d.*) from DAG_Node d, DAG_DAG dd 
where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key between 14 and 42;

select distinct creation_date from VOC_Term_EMAPA;
select distinct creation_date from VOC_Term_EMAPS;
select distinct creation_date from DAG_Node where _dag_key between 13 and 42;

--
-- EMAPA_sto79.obo
--

(
select a.accID, ta.term as EMAPA, st.startStage, st.endStage
from ACC_Accession a, VOC_Term ta, VOC_Term_EMAPA st
where a.accid in ('EMAPA:16032', 'EMAPA:16033')
and a._MGIType_key = 13
and a._Object_key = ta._Term_key
and ta._Term_key = st._Term_key
union
select a.accID, s.synonym, st.startStage, st.endStage
from ACC_Accession a, MGI_Synonym s, VOC_Term_EMAPA st
where a.accid in ('EMAPA:16032', 'EMAPA:16033')
and a._MGIType_key = 13
and a._Object_key = s._Object_key
and s._MGIType_key = 13
and a._Object_key = st._Term_key
)
order by accID
;

--
-- EMAPA_passsanitycheck_test.txt
--

-- test 1: new EMAPA term
-- test 2: obsolete EMAPA term that is not used in an Assay annotation
-- test 3: stage change
-- test 4: EMAPA merge if EMAPA is not used in an Assay annotation
-- EMAPA:36675 : new (part_of EMAPA:35162,EMAPA:35862)
-- EMAPA:35909 : obsolete
-- EMAPA:35182 : start was TS27, now TS17
-- EMAPA:16097 : end was TS26, now TS11
-- EMAPA:18220 : alt_id for EMAPA:18219

--select a.accID, ta.term as EMAPA, ta.isObsolete
--from ACC_Accession a, VOC_Term ta
--where a.accid in ('EMAPA:36675', 'EMAPA:35162', 'EMAPA:35862', 
	--'EMAPA:35909', 'EMAPA:35182', 'EMAPA:16097', 'EMAPA:18219', 'EMAPA:18220')
--and a._MGIType_key = 13
--and a._Object_key = ta._Term_key
--order by a.accID
--;

-- EMAPA:35909 : should not appear
-- EMAPA:18220 : alt_id for EMAPA:18219

--select a.accID, ta.term as EMAPA, emaps._Stage_key, emapa.startStage, emapa.endStage
--from ACC_Accession a, VOC_Term ta, VOC_Term_EMAPA emapa, VOC_Term_EMAPS emaps, VOC_Term ts
--where a.accid in ('EMAPA:36675', 'EMAPA:35162', 'EMAPA:35862', 
	--'EMAPA:35909', 'EMAPA:35182', 'EMAPA:16097', 'EMAPA:18219', 'EMAPA:18220')
--and a._MGIType_key = 13
--and a._Object_key = ta._Term_key
--and ta._Term_key = emapa._Term_key
--and emapa._Term_key = emaps._EMAPA_Term_key
--and emaps._Term_key = ts._Term_key
--order by a.accID, emaps._Stage_key
--;

EOSQL
}

cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $LOG

--are there terms in the DAG that are not in the VOC_Term any more?

select d.*
from DAG_Node d
where d._dag_key = 13
and not exists (select 1 from VOC_Term t where d._object_key = t._term_key)
;

select d.*
from DAG_Node d
where d._dag_key between 14 and 42
and not exists (select 1 from VOC_Term t where d._object_key = t._term_key)
;

EOSQL

# use "production" obo file
# /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo

echo '######'
echo 'test 1 : obsoletes added' | tee -a $LOG
cp /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo.bak /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo
runQuery | tee -a $PRELOG
${VOCLOAD}/emap/emapload.sh | tee -a $LOG
runQuery | tee -a $POSTLOG
echo 'pre-emapload, post-emapload counts should differ by number of obsolete terms' | tee -a $LOG
echo '*****'
echo 'DIFF emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG
echo 'DIFF should show that obsoletes are now added to EMAPA (90), but not EMAPS (91)'
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emapa /data/loads/lec/mgi/vocload/emap/test1
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emaps /data/loads/lec/mgi/vocload/emap/test1
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term.s.bcp /data/loads/lec/mgi/vocload/emap/test1
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPA.bcp /data/loads/lec/mgi/vocload/emap/test1
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPS.bcp /data/loads/lec/mgi/vocload/emap/test1
cp /data/loads/lec/mgi/vocload/emap/output/MGI_Synonym.s.bcp /data/loads/lec/mgi/vocload/emap/test1

echo '######'
echo 'test 2 : use same EMAPA.obo file : no changes' | tee -a $LOG
runQuery | tee -a $PRELOG
${VOCLOAD}/emap/emapload.sh | tee -a $LOG
runQuery | tee -a $POSTLOG
echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG
echo '*****'
echo 'DIFF emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG
echo 'DIFF should show no changes'
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emapa /data/loads/lec/mgi/vocload/emap/test2
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emaps /data/loads/lec/mgi/vocload/emap/test2
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term.s.bcp /data/loads/lec/mgi/vocload/emap/test2
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPA.bcp /data/loads/lec/mgi/vocload/emap/test2
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPS.bcp /data/loads/lec/mgi/vocload/emap/test2
cp /data/loads/lec/mgi/vocload/emap/output/MGI_Synonym.s.bcp /data/loads/lec/mgi/vocload/emap/test2

echo '######'
echo 'test 3 : use same EMAPA.obo file : delete all EMAPA terms that have no annotations' | tee -a $LOG
echo 'this will test the adding of new terms'
runQuery | tee -a $PRELOG
cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $LOG
CREATE TEMP TABLE tmp_delete
AS (select _Term_key
from VOC_Term t
where t._Vocab_key = 90
and not exists (select 1 from GXD_ISResultStructure s where t._Term_key = s._EMAPA_Term_key)
and not exists (select 1 from GXD_GelLaneStructure s where t._Term_key = s._EMAPA_Term_key)
)
;
DELETE FROM VOC_Term
USING tmp_delete
WHERE tmp_delete._Term_key = VOC_Term._Term_key
;
EOSQL
${VOCLOAD}/emap/emapload.sh | tee -a $LOG
runQuery | tee -a $POSTLOG
echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG
echo '*****'
echo 'DIFF emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG
echo 'DIFF should show changes due to adding new terms'
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emapa /data/loads/lec/mgi/vocload/emap/test3
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emaps /data/loads/lec/mgi/vocload/emap/test3
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term.s.bcp /data/loads/lec/mgi/vocload/emap/test3
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPA.bcp /data/loads/lec/mgi/vocload/emap/test3
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPS.bcp /data/loads/lec/mgi/vocload/emap/test3
cp /data/loads/lec/mgi/vocload/emap/output/MGI_Synonym.s.bcp /data/loads/lec/mgi/vocload/emap/test3

echo '######'
echo 'test 4 : EMAPA_sto79.txt' | tee -a $LOG
cp /data/loads/lec/mgi/vocload/emap/input/EMAPA_sto79.txt /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo
runQuery | tee -a $PRELOG
${VOCLOAD}/emap/emapload.sh | tee -a $LOG
runQuery | tee -a $POSTLOG
echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG
echo '*****'
echo 'DIFF emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG
echo 'DIFF should show no changes'
date |tee -a $LOG
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emapa /data/loads/lec/mgi/vocload/emap/test4
cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emaps /data/loads/lec/mgi/vocload/emap/test4
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term.s.bcp /data/loads/lec/mgi/vocload/emap/test4
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPA.bcp /data/loads/lec/mgi/vocload/emap/test4
cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPS.bcp /data/loads/lec/mgi/vocload/emap/test4
cp /data/loads/lec/mgi/vocload/emap/output/MGI_Synonym.s.bcp /data/loads/lec/mgi/vocload/emap/test4

#echo '######'
#echo 'test 5 : EMAPA_passsanitycheck_test.txt' | tee -a $LOG
#cp /data/loads/lec/mgi/vocload/emap/input/EMAPA_passsanitycheck_test.txt /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo
#runQuery | tee -a $PRELOG
#${VOCLOAD}/emap/emapload.sh | tee -a $LOG
#runQuery | tee -a $POSTLOG
#echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG
#echo '*****'
#echo 'DIFF emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
#diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG
#echo 'DIFF should show no changes'
#date |tee -a $LOG
#cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emapa /data/loads/lec/mgi/vocload/emap/test5
#cp /data/loads/lec/mgi/vocload/emap/output/Termfile.emaps /data/loads/lec/mgi/vocload/emap/test5
#cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term.s.bcp /data/loads/lec/mgi/vocload/emap/test5
#cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPA.bcp /data/loads/lec/mgi/vocload/emap/test5
#cp /data/loads/lec/mgi/vocload/emap/output/VOC_Term_EMAPS.bcp /data/loads/lec/mgi/vocload/emap/test5
#cp /data/loads/lec/mgi/vocload/emap/output/MGI_Synonym.s.bcp /data/loads/lec/mgi/vocload/emap/test5

