#!/bin/sh
#
#  $Header$
#  $Name$
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
#  Truncate the VOC_DAGSort table in the RADAR database to remove any
#  current records.
#
echo "Truncate VOC_DAGSort table" >> ${FULL_LOG_FILE}
cat - <<EOSQL | isql -S${DBSERVER} -U${DBUSER} -P`cat ${DBPASSWORD_FILE}` >> ${FULL_LOG_FILE}

use ${RADAR_DATABASE}
go

truncate table VOC_DAGSort
go

checkpoint
go

quit
EOSQL

#
#  Call the Python script.
#
echo "Start loadTopSort.py" >> ${FULL_LOG_FILE}
loadTopSort.py >> ${FULL_LOG_FILE}
echo "End loadTopSort.py" >> ${FULL_LOG_FILE}

#
#  Load the VOC_DAGSort table from the DAG sort bcp file.
#
echo "Load VOC_DAGSort table with sort order" >> ${FULL_LOG_FILE}
cat ${DBPASSWORD_FILE} | bcp ${RADAR_DATABASE}..VOC_DAGSort in ${VOC_DAG_SORT_BCP_FILE} -c -t\\t -S${DBSERVER} -U${DBUSER} >> ${BCP_LOG_FILE}

#
#  Update the VOC_Term table using the VOC_DAGSort table to establish
#  the topological sort order for each term in the vocabulary.
#
echo "Update VOC_Term table to apply sort order" >> ${FULL_LOG_FILE}
cat - <<EOSQL | isql -S${DBSERVER} -U${DBUSER} -P`cat ${DBPASSWORD_FILE}` >> ${FULL_LOG_FILE}

use ${DATABASE}
go

update VOC_Term
set sequenceNum = s.sequenceNum
from VOC_Term t,
     VOC_Vocab v,
     ${RADAR_DATABASE}..VOC_DAGSort s
where t._Term_key = s._Term_key and
      t._Vocab_key = v._Vocab_key and
      v.name = "${VOCAB_NAME}"
go

checkpoint
go

quit
EOSQL

echo "End topological sort ordering" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
