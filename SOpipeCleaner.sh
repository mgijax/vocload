#!/bin/sh

#
# Program: SOpipeCleaner.sh
#
# Purpose:
#
#	The SO data file (OBO format) contains at least six terms with
#	definitions that contain pipes (|).  We use pipes to delimit our
#	data files for loading via bcp, so these cause problems.  This
#	script replaces the pipes in the data file with the string " or ",
#	as they are always separating two nucleotides, where one or the
#	other is contained in a sequence.
#
# Usage:
#
#	SOpipeCleaner.sh
#
# History:
#	
#	jsb	12/05/2018
#	- initial addition
#
if [ "${OBO_FILE}" != "" ]; then
	TEMP_FILE=${OBO_FILE}.tmp
	cat ${OBO_FILE} | sed 's/[|]/\&#124;/g' > ${TEMP_FILE}
	mv ${TEMP_FILE} ${OBO_FILE}
fi
