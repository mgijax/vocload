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

CONFIG_FILE=$1
export CONFIG_FILE

cd `dirname $0`
. VOClib.config

setUp ${CONFIG_FILE} load full
executePrograms ${LOAD_PROGRAM}
archive
finishUp

# $Log$
