#!/bin/sh
#
#  $Header$
#  $Name$
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
#  Implementation:
#
#      This script will perform following steps to identify the header
#      nodes for a vocabulary:
#
#      1) Truncate the VOC_Header table in the RADAR database.
#      2) Use bcp to load the header file into the VOC_Header table.
#      3) Call the loadHeader.py script to identify the header nodes.
#      4) Call the VOC_processAnnotHeaderAll stored procedure to
#         re-evaluate the headers for all of the existing MP/Genotype
#         annotations.
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
#  Truncate the VOC_Header table in the RADAR database to remove any
#  current records.
#
echo "Truncate VOC_Header table" >> ${FULL_LOG_FILE}
cat - <<EOSQL | isql -S${DBSERVER} -U${DBUSER} -P`cat ${DBPASSWORD_FILE}` >> ${FULL_LOG_FILE}

use ${RADAR_DATABASE}
go

truncate table VOC_Header
go

checkpoint
go

quit
EOSQL

#
#  Load the VOC_Header table from the header file using bcp.
#
echo "Load the header file into the VOC_Header table" >> ${FULL_LOG_FILE}
cat ${DBPASSWORD_FILE} | bcp ${RADAR_DATABASE}..VOC_Header in ${HEADER_FILE} -c -t\\t -S${DBSERVER} -U${DBUSER} >> ${BCP_LOG_FILE}

#
#  Call the Python script.
#
echo "Start loadHeader.py" >> ${FULL_LOG_FILE}
loadHeader.py >> ${FULL_LOG_FILE}
echo "End loadHeader.py" >> ${FULL_LOG_FILE}

#
#  Execute the VOC_processAnnotHeaderAll stored procedure.
#
if [ "${HEADER_ANNOT_TYPE_KEY}" != "" ]
then
    echo "Execute VOC_processAnnotHeaderAll procedure: (AnnotType key: ${HEADER_ANNOT_TYPE_KEY})" >> ${FULL_LOG_FILE}

cat - <<EOSQL | isql -S${DBSERVER} -U${DBUSER} -P`cat ${DBPASSWORD_FILE}` >> ${FULL_LOG_FILE}

use ${DATABASE}
go

exec VOC_processAnnotHeaderAll ${HEADER_ANNOT_TYPE_KEY}
go

checkpoint
go

quit
EOSQL

fi

echo "End header file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
