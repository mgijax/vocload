#!/bin/sh

#
# Program: runOBOFullLoad.sh
#
# Purpose:
#
# 	Script for Executing an OBO Full Load
# 
# Usage:
#
#	runOBOFullLoad.sh [configuration file]
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

setUp $1 load full
executePrograms ${LOAD_PROGRAM}
executeExtra $1
archive
finishUp
