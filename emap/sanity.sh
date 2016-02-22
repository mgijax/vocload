#!/bin/sh
#
#  sanity.sh
###########################################################################
#
#  Purpose:
#
#      This script runs 
#	1. sanity.py - performs non well-formed obo checks and checks 
#            proprietary to an EMAPA obo file
#
#  Usage:
#
#      sanity.sh  filename  
#
#      where
#          filename = path to the input file
#
#  Env Vars:
#
#      See the configuration file
#
#  Inputs:
#	EMAPA obo file
#
#  Outputs:
#
#      - report of duplicate ids in the input
#	- report of inValid theiler stage values
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
#      This script will perform following steps:
#
#      ) Validate the arguments to the script.
#      ) Source the configuration files to establish the environment.
#      ) Verify that the input file exists.
#      ) create report 
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
#  11/12/2013  sc  Initial development
#
###########################################################################

CURRENTDIR=`pwd`

CONFIG=emapload.config
USAGE='Usage: sanity.sh filename'

#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG} ]
then
    . ${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# Make sure an input file was passed to the script.
#
if [ $# -eq 1 ]
then
    INPUT_FILE=$1
else
    echo ${USAGE}; exit 1
fi

#
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE}"
    exit 1
fi

#
# Initialize the dup file to make sure the current user can write to it
#
rm -f ${DUP_IDS_RPT}; > ${DUP_IDS_RPT}

#
# Find dup IDS
#

grep '^id:' ${INPUT_FILE} | cut -d' ' -f2 | sort | uniq -d  > ${DUP_IDS_RPT}

INPUT_FILE_DEFAULT=${INPUT_FILE}
export INPUT_FILE_DEFAULT

# run sanity.py
${EMAPLOAD}/bin/sanity.py
STAT=$?
exit ${STAT}
