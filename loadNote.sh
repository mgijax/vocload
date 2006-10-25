#!/bin/sh
#
#  loadNote.sh
###########################################################################
#
#  Purpose:
#
#      Load the note file into the VOC_Note table and call the Python
#      script that uses this data to add notes for the given terms.
#
#  Usage:
#
#      loadNote.sh  ConfigFile  NoteFile
#
#      where
#
#          ConfigFile is the name of the configuration file for the
#                     specific vocabulary load (e.g. MP.config).
#          NoteFile is the full path name of the note file to load
#                   (e.g. /data/loads/mgi/vocload/runTimeMP/MP.note).
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - Note file - contains accession IDs for each term, along with
#                    a note type and note to be added for the term
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
#  Assumes:
#
#      This script assumes that a note is not greater than 255 bytes, so it
#      can be loaded into the note column of the VOC_Note table.
#
#  Implementation:
#
#      This script will perform following steps to add the notes for the
#      given terms:
#
#      1) Truncate the VOC_Note table in the RADAR database.
#      2) Use bcp to load the note file into the VOC_Note table.
#      3) Call the loadNote.py script to add the notes for the terms.
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
    echo "Usage:  $0  ConfigFile  NoteFile"
    exit 1
fi
LOAD_CONFIG=$1
NOTE_FILE=$2

#
#  Source the configuration files to establish the environment.
#
cd `dirname $0`
. ${LOAD_CONFIG}
. ./Configuration

echo "**************************************************" >> ${FULL_LOG_FILE}
echo "Start note file processing: ${NOTE_FILE}" >> ${FULL_LOG_FILE}

#
#  Truncate the VOC_Note table in the RADAR database to remove any
#  current records.
#
echo "Truncate VOC_Note table" >> ${FULL_LOG_FILE}
cat - <<EOSQL | isql -S${RADAR_DBSERVER} -U${RADAR_DBUSER} -P`cat ${RADAR_DBPASSWORDFILE}` >> ${FULL_LOG_FILE}

use ${RADAR_DBNAME}
go

truncate table VOC_Note
go

checkpoint
go

quit
EOSQL

#
#  Load the VOC_Note table from the note file using bcp.
#
echo "Load the note file into the VOC_Note table" >> ${FULL_LOG_FILE}
cat ${RADAR_DBPASSWORDFILE} | bcp ${RADAR_DBNAME}..VOC_Note in ${NOTE_FILE} -c -t\\t -S${RADAR_DBSERVER} -U${RADAR_DBUSER} >> ${BCP_LOG_FILE}

#
#  Call the Python script.
#
echo "Start loadNote.py" >> ${FULL_LOG_FILE}
loadNote.py >> ${FULL_LOG_FILE}
echo "End loadNote.py" >> ${FULL_LOG_FILE}

echo "End note file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
