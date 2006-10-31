#!/bin/sh

#
# Program: runOBOIncLoadNoArchive.sh
#
# Purpose:
#
# 	Script for Executing an OBO Incremental Load w/ no Archiving
# 
# Usage:
#
#	runOBOIncLoadNoArchive.sh [configuration file]
#
# History:
#
#	dbm	10/25/2006
#	- new
#

LOAD_PROGRAM="loadOBO.py"
export LOAD_PROGRAM

cd `dirname $0`
. VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}
executeExtra $1
finishUp
