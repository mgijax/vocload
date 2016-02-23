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

#
# add new terms
# obsoletes w/no annotations
# stage range change

cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $LOG

select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 91;
select count(*) from VOC_Term_EMAPS;
select count(*) from DAG_Closure where _dag_key between 14 and 42;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key between 14 and 42;

select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 90;
select count(*) from VOC_Term_EMAPA;
select count(*) from DAG_Closure where _dag_key = 13;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key = 13;

--truncate table mgd.VOC_Term_EMAPA;
--delete EMAPS
delete from VOC_Term where _Vocab_key = 91;

--truncate table mgd.VOC_Term_EMAPS;

EOSQL

-- use "production" obo file
# /data/loads/lec/mgi/vocload/emap/input/EMAPA.obo
${VOCLOAD}/emap/emapload.sh

cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $LOG

-- should be 0
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 170 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 91;
select count(*) from VOC_Term_EMAPS;
select count(*) from DAG_Closure where _dag_key between 14 and 42;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key between 14 and 42;

-- should not be 0
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 1;
select count(*) from ACC_Accession where _mgitype_key = 13 and _logicaldb_key = 169 and preferred = 0;
select count(*) from VOC_Term where _Vocab_key = 90;
select count(*) from VOC_Term_EMAPA;
select count(*) from DAG_Closure where _dag_key = 13;
select count(d.*) from DAG_Node d, DAG_DAG dd where d._dag_key = dd._dag_key and dd._mgitype_key = 13 and dd._dag_key = 13;

EOSQL
date |tee -a $LOG

