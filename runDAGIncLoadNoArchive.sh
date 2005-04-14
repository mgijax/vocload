#!/bin/sh

#
# Program: runDAGIncLoadNoArchive.sh
#
# Purpose:
#
# 	Script for Executing a DAG Incremental Load w/ no Archiving
# 
# Usage:
#
#	runDAGIncLoadNoArchive.sh [configuration file]
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

if [ "${TOPOLOGICAL_SORT}" = "true" ]
then
    loadTopSort.sh $1
fi

finishUp

