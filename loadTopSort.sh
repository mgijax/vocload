#!/bin/sh
#
#  loadTopSort.sh
###########################################################################
#
#  Purpose:
#
#      Call the Python script to determine the topological sort order for
#      a vocabulary and update the VOC_Term table to set the sort order
#      for each term.
#
#  Usage:
#
#      loadTopSort.sh  ConfigFile
#
#      where
#
#          ConfigFile is the name of the configuration file for the
#                     specific vocabulary load (e.g. MP.config).
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:  None
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
#      1) Truncate the VOC_DAGSort table in the RADAR database.
#      2) Call the loadTopSort.py script to generate the topological sort
#         order for the vocabulary and create a bcp file identifying the
#         sort order for each term.
#      3) Use bcp to load the VOC_DAGSort table.
#      4) Update the VOC_Term.sequenceNum attribute using the term key
#         and sequence number in the VOC_DAGSort table.
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
#  03/23/2005  DBM  Initial development
#
###########################################################################

if [ $# -ne 1 ]
then
    echo "Usage:  $0  ConfigFile"
    exit 1
fi
LOAD_CONFIG=$1

#
#  Source the configuration files to establish the environment.
#
cd `dirname $0`
. ${LOAD_CONFIG}
. ./Configuration

echo "**************************************************" >> ${FULL_LOG_FILE}
echo "Start topological sort ordering" >> ${FULL_LOG_FILE}

#
#  Call the Python script.
#
echo "Start loadTopSort.py" >> ${FULL_LOG_FILE}
loadTopSort.py >> ${FULL_LOG_FILE}
echo "End loadTopSort.py" >> ${FULL_LOG_FILE}

echo "End topological sort ordering" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
