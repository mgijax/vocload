#!/bin/sh
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
#  Call the Python script.
#
echo "Start loadSynonym.py" >> ${FULL_LOG_FILE}
loadSynonym.py ${SYNONYM_FILE} >> ${FULL_LOG_FILE}
echo "End loadSynonym.py" >> ${FULL_LOG_FILE}

echo "End synonym file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
