#!/bin/sh

#
# Program: runSimpleFullLoad.sh
#
# Purpose:
#
# 	Script for Executing a Simple Full Load
# 
# Usage:
#
#	runSimpleFullLoad.sh [configuration file]
#
# History:
#
#	lec	03/26/2003
#	- new
#

RCD_FILE=simple.rcd
export RCD_FILE

LOAD_PROGRAM=simpleLoad.py
export LOAD_PROGRAM

cd `dirname $0`
. VOClib.config

setUp $1 load full
executePrograms ${LOAD_PROGRAM}
archive
finishUp

# $Log$
# Revision 1.1  2003/03/26 15:27:46  lec
# new
#
