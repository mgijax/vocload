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

cd `dirname $0`
. VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}
archive
finishUp

# $Log$
