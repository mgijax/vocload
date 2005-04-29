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
. VOClib.config

setUp $1 load incremental
executePrograms ${LOAD_PROGRAM}
executeExtra $1
archive
finishUp

# $Log$
# Revision 1.3  2005/04/13 17:35:43  lec
# vocload-3-2-0-1
#
# Revision 1.2.4.2  2005/03/23 16:21:50  dbm
# Added topological sort
#
# Revision 1.2.4.1  2005/03/17 15:04:33  dbm
# Added header, note and synonym support; Migrate synonyms to MGI_Synonym
#
# Revision 1.2  2003/03/26 16:02:16  lec
# continuing to factor out common tasks/variables
#
# Revision 1.1  2003/03/26 16:00:12  lec
# continuing to factor out common tasks/variables
#
