#!/bin/sh

#
# Program: OMIMpost.sh
#
# Purpose:
#
#   Configuration file for Disease Ontology loading into MGI_Set/MGI_SetMember table
#
# History:
#
# 09/28/2020	lec
#

. ${VOCLOAD}/OMIM.config

cd ${VOCLOAD}/bin
${PYTHON} OMIMtermcheck.py
STAT=$?
if [ ${STAT} -ne 0 ]
then
   exit 1
fi
exit 0
