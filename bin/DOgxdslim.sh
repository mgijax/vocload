#!/bin/sh

#
# Program: DOgxdslim.sh
#
# Purpose:
#
#   Configuration file for Disease Ontology loading into MGI_Set/MGI_SetMember table
#
# History:
#
# 10/03/2016	lec
#	- TR12427/Disease Ontology
#

. ${VOCLOAD}/DO.config

cd ${RUNTIME_DIR}

${SETLOAD}/setload.csh ${VOCLOAD}/DOgxdslim.config
STAT=$?
if [ ${STAT} -ne 0 ]
then
   exit 1
fi
exit 0
