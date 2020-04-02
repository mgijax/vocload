#!/bin/sh
#
#  loadHeader.sh
###########################################################################
#
#  Purpose:
#
#      Load the header file into the VOC_Header table and call the Python
#      script that uses this data to identify the header nodes in a DAG
#      for the given vocabulary.
#
#  Usage:
#
#      loadHeader.sh  ConfigFile  HeaderFile
#
#      where
#
#          ConfigFile is the name of the configuration file for the
#                     specific vocabulary load (e.g. MP.config).
#          HeaderFile is the full path name of the header file to load
#                     (e.g. /data/loads/mgi/vocload/runTimeMP/MP.header).
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - Header file - contains accession IDs for each header term
#
#  Outputs:
#
#      - Log file (${FULL_LOG_FILE})
#      - BCP log file (${BCP_LOG_FILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal error occurred
#
#  Assumes:  Nothing
#
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  03/17/2005  DBM  Initial development
#
###########################################################################

if [ $# -ne 2 ]
then
    echo "Usage:  $0  ConfigFile  HeaderFile"
    exit 1
fi
LOAD_CONFIG=$1
HEADER_FILE=$2

#
#  Source the configuration files to establish the environment.
#
cd `dirname $0`
. ${LOAD_CONFIG}
. ./Configuration

echo "**************************************************" >> ${FULL_LOG_FILE}
echo "Start header file processing: ${HEADER_FILE}" >> ${FULL_LOG_FILE}

#
#  Call the Python script.
#
echo "Start loadHeader.py" >> ${FULL_LOG_FILE}
${PYTHON} loadHeader.py ${HEADER_FILE} ${HEADER_ANNOT_TYPE_KEY} >> ${FULL_LOG_FILE}
echo "End loadHeader.py" >> ${FULL_LOG_FILE}

echo "End header file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
