#!/bin/sh

#
# Program: runDAGIncLoad.sh
#
# Purpose:
#
# 	Script for Executing a DAG Incremental Load
# 
# Usage:
#
#	runDAGIncLoad.sh [configuration file]
#
# History:
#
#	lec	03/26/2003
#	- new
#

LOAD_PROGRAM="GOload.py"
export LOAD_PROGRAM

cd `dirname $0`
. VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}

if [ "${HEADER_FILE}" != "" ]
then
    loadHeader.sh $1 ${HEADER_FILE}
fi

if [ "${NOTE_FILE}" != "" ]
then
    loadNote.sh $1 ${NOTE_FILE}
fi

if [ "${SYNONYM_FILE}" != "" ]
then
    loadSynonym.sh $1 ${SYNONYM_FILE}
fi

archive
finishUp

# $Log$
# Revision 1.2  2003/03/26 16:02:16  lec
# continuing to factor out common tasks/variables
#
# Revision 1.1  2003/03/26 16:00:12  lec
# continuing to factor out common tasks/variables
#
