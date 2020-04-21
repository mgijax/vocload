#!/bin/sh

#
# Program: runDAGIncNoLoad.sh
#
# Purpose:
#
# 	Script for Executing a DAG Incremental NoLoad
# 
# Usage:
#
#	runDAGIncNoLoad.sh [configuration file]
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

setUp $1 noload incremental
executePrograms ${LOAD_PROGRAM}
archive
finishUp
