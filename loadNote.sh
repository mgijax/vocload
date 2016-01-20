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
#  Call the Python script.
#
echo "Start loadNote.py" >> ${FULL_LOG_FILE}
loadNote.py ${NOTE_FILE} >> ${FULL_LOG_FILE}
echo "End loadNote.py" >> ${FULL_LOG_FILE}

echo "End note file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0
