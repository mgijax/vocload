#!/bin/sh

#
# Program: runDAGFullLoad.sh
#
# Purpose:
#
# 	Script for Executing a DAG Full Load
# 
# Usage:
#
#	runDAGFullLoad.sh [configuration file]
#
# History:
#
#	lec	03/26/2003
#	- new
#

LOAD_PROGRAM="GOload.py"
export LOAD_PROGRAM

cd ${VOCLOAD}
. ${VOCLOAD}/VOClib.config

setUp $1 load full
executePrograms ${LOAD_PROGRAM}
archive
finishUp
