#!/bin/sh

#
# Program: runOBOIncNoLoad.sh
#
# Purpose:
#
# 	Script for Executing an OBO Incremental NoLoad
# 
# Usage:
#
#	runOBOIncNoLoad.sh [configuration file]
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

setUp $1 noload incremental
executePrograms ${LOAD_PROGRAM}
archive
finishUp
