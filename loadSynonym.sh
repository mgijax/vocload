#!/bin/sh
#
#  $Header$
#  $Name$
#
#  loadSynonym.sh
###########################################################################
#
#  Purpose:
#
#      Load the synonym file into the VOC_Synonym table and call the Python
#      script that uses this data to add synonym for the given terms.
#
#  Usage:
#
#      loadSynonym.sh  ConfigFile  SynonymFile
#
#      where
#
#          ConfigFile is the name of the configuration file for the
#                     specific vocabulary load (e.g. MP.config).
#          SynonymFile is the full path name of the synonym file to load
#                      (e.g. /data/loads/mgi/vocload/runTimeMP/MP.synonym).
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - Synonym file - contains accession IDs for each term, along with
#                       a synonym type and synonym to be added for the term
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
#      This script will perform following steps to add the synonyms for the
#      given terms:
#
#      1) Truncate the VOC_Synonym table in the RADAR database.
#      2) Use bcp to load the synonym file into the VOC_Synonym table.
#      3) Call the loadSynonym.py script to add the synonyms for the terms.
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
    echo "Usage:  $0  ConfigFile  SynonymFile"
    exit 1
fi
LOAD_CONFIG=$1
SYNONYM_FILE=$2

#
#  Source the configuration files to establish the environment.
#
cd `dirname $0`
. ${LOAD_CONFIG}
. ./Configuration

echo "**************************************************" >> ${FULL_LOG_FILE}
echo "Start synonym file processing: ${SYNONYM_FILE}" >> ${FULL_LOG_FILE}

#
#  Truncate the VOC_Synonym table in the RADAR database to remove any
#  current records.
#
echo "Truncate VOC_Synonym table" >> ${FULL_LOG_FILE}
cat - <<EOSQL | isql -S${DBSERVER} -U${DBUSER} -P`cat ${DBPASSWORD_FILE}` >> ${FULL_LOG_FILE}

use ${RADAR_DATABASE}
go

truncate table VOC_Synonym
go

checkpoint
go

quit
EOSQL

#
#  Load the VOC_Synonym table from the synonym file using bcp.
#
echo "Load the synonym file into the VOC_Synonym table" >> ${FULL_LOG_FILE}
cat ${DBPASSWORD_FILE} | bcp ${RADAR_DATABASE}..VOC_Synonym in ${SYNONYM_FILE} -c -t\\t -S${DBSERVER} -U${DBUSER} >> ${BCP_LOG_FILE}

#
#  Call the Python script.
#
echo "Start loadSynonym.py" >> ${FULL_LOG_FILE}
loadSynonym.py >> ${FULL_LOG_FILE}
echo "End loadSynonym.py" >> ${FULL_LOG_FILE}

echo "End synonym file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
