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

#cd ${QCRPTS}
#cd /home/lec/mgi/qcreports_db-trunk
#. ./Configuration
#cd mgd
#GXD_EMAPA_Terms.py
#GXD_EMAPS_Terms.py

runQuery ()
{
cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0

select count(*) from ACC_Accession where _mgitype_key = 13 and _prelogicaldb_key = 169 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _prelogicaldb_key = 169 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 90;
select count(*) from VOC_Term_EMAPA;
select count(*) from DAG_Closure where _dag_key = 13;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key = 13;

select count(*) from ACC_Accession where _mgitype_key = 13 and _prelogicaldb_key = 170 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _prelogicaldb_key = 170 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 91;
select count(*) from VOC_Term_EMAPS;
select count(*) from DAG_Closure where _dag_key between 14 and 42;
select count(d.*) from DAG_Node d, DAG_DAG dd 
where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key between 14 and 42;

EOSQL
}

# use "production" obo file
# /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo
echo 'test 1 : no changes' | tee -a $LOG
runQuery | tee -a $PRELOG
${VOCLOAD}/emap/emapload.sh | tee -a $LOG
runQuery | tee -a $POSTLOG
echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG
echo 'diff emaptest.sh.postlog emaptest.sh.prelog' | tee -a $LOG
diff emaptest.sh.postlog emaptest.sh.prelog | tee -a $LOG

#echo 'test 2 : use same EMAPA.obo file, delete all EMAPA terms that do not have Assay annotations' | tee -a $LOG
#cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $PRELOG
#CREATE TEMP TABLE tmp_delete
#AS (select _Term_key
#from VOC_Term t
#where t._Vocab_key = 90
#and not exists (select 1 from GXD_ISResultStructure s where t._Term_key = s._EMAPA_Term_key)
#and not exists (select 1 from GXD_GelLaneStructure s where t._Term_key = s._EMAPA_Term_key)
#)
#;
#DELETE FROM VOC_Term
#USING tmp_delete
#WHERE tmp_delete._Term_key = VOC_Term._Term_key
#;
#EOSQL
#runQuery | tee -a $PRELOG
#${VOCLOAD}/emap/emapload.sh | tee -a $LOG
#runQuery | tee -a $POSTLOG
#echo 'pre-emapload, post-emapload counts should be equal' | tee -a $LOG

date |tee -a $LOG

