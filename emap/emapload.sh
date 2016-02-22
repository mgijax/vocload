#!/bin/sh 

#
# This script is a wrapper around the process that loads EMAPA/EMAPS
# vocabularies
#
#
#     emapload.sh 
#

cd `dirname $0`/..

CONFIG_LOAD=`pwd`/emap/emapload.config
USAGE='Usage: emapload.sh'

LOG=`pwd`/emap/emapload.log
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

if [ ! -r ${CONFIG_LOAD} ]
then
    echo "Cannot read configuration file: ${CONFIG_LOAD}"
    exit 1
fi

. ${CONFIG_LOAD}

echo "MGD_DBSERVER: ${MGD_DBSERVER}"
echo "MGD_DBNAME: ${MGD_DBNAME}"
# this is a live run, set LIVE_RUN accordingly
LIVE_RUN=1; export LIVE_RUN

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
#if [ -f ${LASTRUN_FILE} ]
#then
#    if test ${LASTRUN_FILE} -nt ${INPUT_FILE_DEFAULT}
#    then
#
#        echo "Input file has not been updated - skipping load" | tee -a ${LOG_PROC}
#        # set STAT for shutdown
#        STAT=0
#        echo 'shutting down'
#        shutDown
#        exit 0
#    fi
#fi

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
${VOCLOAD}/emap/emapload.py  
STAT=$?
if [ ${STAT} = 2 ]
then
    checkStatus ${STAT} "Sanity errors detected. See ${QC_RPT}" 
else
    checkStatus ${STAT} "${VOCLOAD}/emap/emapload.py"
fi

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
${VOCABBREVLOAD}/bin/vaload.sh emapslimload.config

# run postload cleanup and email logs

shutDown

