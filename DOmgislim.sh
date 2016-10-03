#!/bin/sh

#
# Program: DOmgislim.sh
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

${SETLOAD}/setload.csh ${VOCLOAD}/DOmgislim.config

