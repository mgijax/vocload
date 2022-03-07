#!/bin/sh 

#
# This script is a wrapper around the process that loads EMAPA/EMAPS
# vocabularies
#
#     emapload.sh 
#
# HISTORY
#
#  04/19/17 - delete old fatal and warning reports before running
#	emapload.py, we don't want old ones hanging around
#
cd `dirname $0`

CONFIG=emapload.config
USAGE='Usage: emapload.sh'

LOG=emapload.log
rm -rf ${LOG}

#
#  Verify the argument(s) to the shell script.
#
if [ $# -ne 0 ]
then
    echo ${USAGE} | tee -a ${LOG}
    exit 1
fi

#
# verify & source the configuration file
#

if [ ! -r ${CONFIG} ]
then
    echo "Cannot read configuration file: ${CONFIG}"
    exit 1
fi

. ${CONFIG}

echo "PG_DBSERVER: ${PG_DBSERVER}"
echo "PG_DBNAME: ${PG_DBNAME}"
# this is a live run, set LIVE_RUN accordingly
LIVE_RUN=1; export LIVE_RUN

# remove any old QC reports
if [ -f ${QC_RPT}} ]
then
    rm ${QC_RPT}
fi

if [ -f ${QC_WARN_RPT}} ]
then
    rm ${QC_WARN_RPT}
fi

#
#  Source the DLA library functions.
#

if [ "${DLAJOBSTREAMFUNC}" != "" ]
then
    if [ -r ${DLAJOBSTREAMFUNC} ]
    then
        . ${DLAJOBSTREAMFUNC}
    else
        echo "Cannot source DLA functions script: ${DLAJOBSTREAMFUNC}" | tee -a ${LOG}
        exit 1
    fi
else
    echo "Environment variable DLAJOBSTREAMFUNC has not been defined." | tee -a ${LOG}
    exit 1
fi

#
# verify input file exists and is readable
#
if [ ! -r ${INPUT_FILE_DEFAULT} ]
then
    # set STAT for endJobStream.py
    STAT=1
    checkStatus ${STAT} "Cannot read from input file: ${INPUT_FILE_DEFAULT}"
fi

#
# remove certain relationships from input file
# TR13273
# develops_from
# directly_develops_from
# develops_from_part_of
# has_developmental_contribution_from
#
TEMP_FILE=${INPUT_FILE_DEFAULT}.tmp
cat ${INPUT_FILE_DEFAULT} | sed '/relationship: develops_from/d' > ${TEMP_FILE}
mv ${TEMP_FILE} ${INPUT_FILE_DEFAULT}
cat ${INPUT_FILE_DEFAULT} | sed '/relationship: directly_develops_from/d' > ${TEMP_FILE}
mv ${TEMP_FILE} ${INPUT_FILE_DEFAULT}
cat ${INPUT_FILE_DEFAULT} | sed '/relationship: develops_from_part_of/d' > ${TEMP_FILE}
mv ${TEMP_FILE} ${INPUT_FILE_DEFAULT}
cat ${INPUT_FILE_DEFAULT} | sed '/relationship: has_developmental_contribution_from/d' > ${TEMP_FILE}
mv ${TEMP_FILE} ${INPUT_FILE_DEFAULT}

#
# createArchive including OUTPUTDIR, startLog, getConfigEnv
# sets "JOBKEY"
preload ${OUTPUTDIR}

#
# rm all files/dirs from OUTPUTDIR
#
cleanDir ${OUTPUTDIR}

#
# There should be a "lastrun" file in the input directory that was created
# the last time the load was run for this input file. If this file exists
# and is more recent than the input file, the load does not need to be run.
#
LASTRUN_FILE=${INPUTDIR}/lastrun
if [ -f ${LASTRUN_FILE} ]
then
    if test ${LASTRUN_FILE} -nt ${INPUT_FILE_DEFAULT}
    then

        echo "Input file has not been updated - skipping load" | tee -a ${LOG_PROC}
        # set STAT for shutdown
        STAT=0
        echo 'shutting down'
        shutDown
        exit 0
    fi
fi

# Run sanity checker
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Run sanity checks"  | tee -a ${LOG_DIAG}
${VOCLOAD}/emap/sanity.sh ${INPUT_FILE_DEFAULT}
STAT=$?
if [ ${STAT} -eq 2 ]
then
    checkStatus ${STAT} "\nInvalid OBO format ${INPUT_FILE_DEFAULT}. Version ${OBO_FILE_VERSION} expected\n"
    # run postload cleanup and email logs
    shutDown
fi

#
# run the load
#
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Run emapload.py"  | tee -a ${LOG_DIAG}
${PG_MGD_DBSCHEMADIR}/key/VOC_Term_drop.object
${PYTHON} ${VOCLOAD}/emap/emapload.py  
STAT=$?
if [ ${STAT} = 2 ]
then
    checkStatus ${STAT} "Sanity errors detected. See ${QC_RPT}" 
else
    checkStatus ${STAT} "${VOCLOAD}/emap/emapload.py"
fi
${PG_MGD_DBSCHEMADIR}/key/VOC_Term_create.object

#
# set permissions
#

echo ${LOGDIR}
echo ${OUTPUTDIR}
case `whoami` in
    mgiadmin)
	chmod 775 ${LOGDIR}/*
        chgrp mgi ${LOGDIR}/*
        chmod 775 ${OUTPUTDIR}/*
        chgrp mgi ${OUTPUTDIR}/*
        chmod 775 ${RPTDIR}/*
        chgrp mgi ${RPTDIR}/*
        chmod 664 ${INPUT_FILE_DEFAULT}
        chgrp mgi ${INPUT_FILE_DEFAULT}
        ;;
esac

#
# Archive a copy of the input file, adding a timestamp suffix.
#
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Archive input file" | tee -a ${LOG_DIAG}
TIMESTAMP=`date '+%Y%m%d.%H%M'`
ARC_FILE=`basename ${INPUT_FILE_DEFAULT}`.${TIMESTAMP}
cp -p ${INPUT_FILE_DEFAULT} ${ARCHIVEDIR}/${ARC_FILE}

#
# Touch the "lastrun" file to note when the load was run.
#
if [ ${STAT} = 0 ]
then
    touch ${LASTRUN_FILE}
fi

# Run the emap slim load
echo "" >> ${LOG_DIAG}
date >> ${LOG_DIAG}
echo "Running the EMAP SLIM load" | tee -a ${LOG_DIAG}

rm ${SLIM_LASTRUN}
${SLIMTERMLOAD}/bin/slimtermload.sh emapslimload.config
# run postload cleanup and email logs
shutDown

