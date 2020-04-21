#!/bin/sh

#
# Program: runSimpleIncLoad.sh
#
# Purpose:
#
# 	Script for Executing a Simple Incremental Load
# 
# Usage:
#
#	runSimpleIncLoad.sh [configuration file]
#
# History:
#
#	lec	04/13/2005
#	- new
#

RCD_FILE=simple.rcd
export RCD_FILE

LOAD_PROGRAM=simpleLoad.py
export LOAD_PROGRAM

cd ${VOCLOAD}
. ${VOCLOAD}/VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}
executeExtra $1
archive
finishUp

