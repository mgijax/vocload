#!/bin/sh

#
# Program: runDAGFullNoLoad.sh
#
# Purpose:
#
# 	Script for Executing a DAG Full NoLoad
# 
# Usage:
#
#	runDAGFullNoLoad.sh [configuration file]
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

setUp $1 noload full
executePrograms ${LOAD_PROGRAM}
archive
finishUp

# $Log$
