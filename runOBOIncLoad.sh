#!/bin/sh

#
# Program: runOBOIncLoad.sh
#
# Purpose:
#
# 	Script for Executing an OBO Incremental Load
# 
# Usage:
#
#	runOBOIncLoad.sh [configuration file]
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
archive
finishUp
