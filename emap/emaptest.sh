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
 
${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_oboonly_test.txt
mv emapFatalQC.rpt emapFatalQC.oboonly.rpt
mv emapWarningQC.rpt emapWarningQC.oboonly.rpt

${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_nonoboonly_test.txt
mv emapFatalQC.rpt emapFatalQC.nonoboonly.rpt
mv emapWarningQC.rpt emapWarningQC.nonoboonly.rpt

${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_withannotations_test.txt
mv emapFatalQC.rpt emapFatalQC.withannotations.rpt
mv emapWarningQC.rpt emapWarningQC.withannotations.rpt

${VOCLOAD}/emap/runEmapQC /data/loads/lec/mgi/vocload/emap/input/EMAPA_truncatedfile_test.txt
mv emapFatalQC.rpt emapFatalQC.truncatefile.rpt
mv emapWarningQC.rpt emapWarningQC.truncatefile.rpt

#cd ${QCRPTS}
#cd /home/lec/mgi/qcreports_db-trunk
#. ./Configuration
#cd mgd
#GXD_EMAPA_Terms.py
#GXD_EMAPS_Terms.py

cat - <<EOSQL | ${PG_DBUTILS}/bin/doisql.csh $0 | tee -a $LOG
EOSQL

date |tee -a $LOG

