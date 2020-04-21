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
. ${VOCLOAD}/VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}
executeExtra $1
archive
finishUp
