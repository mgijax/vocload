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
. VOClib.config

setUp $1 noload incremental
executePrograms ${LOAD_PROGRAM}
#archive
#finishUp

# $Log$
# Revision 1.1  2003/03/26 19:55:43  lec
# added more run scripts
#
