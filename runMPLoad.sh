#!/bin/sh

#
# Program: runMPLoad.sh
#
# Purpose:
#
# Main Wrapper Script for Processing MP Terms and DAGs
# 
# Usage:
#
#	runMPLoad.sh [load|noload] [full|incremental]
#
# History:
#
#	lec	03/25/2003
#	- use new Configuration and MP.config files
#

installOntologyFiles()
{
  if test ! -f ${RUNTIME_DIR}/${TRONTFILE}
  then
      ln -s ${TRDIR}/${TRONTFILE} ${RUNTIME_DIR}
  fi

  if test ! -f ${RUNTIME_DIR}/${TRDEFSFILE}
  then
      ln -s ${TRDIR}/${TRDEFSFILE} ${RUNTIME_DIR}
  fi
}

die()
{
   echo $1
   cat $FULL_LOG_FILE | mailx -s "Mammalian Phenotype Load Catastrophic FAILURE" $MAINTAINER 
   exit $FAILURE
}

createDir()
{
   if [ ! -d $1 ]
   then
      echo "...creating data directory $1"
      mkdir $1
   fi
}

writePgmExecutionHeaders()
{
   echo "Running $1 Program..."
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "Running $1 Program..."                     >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "Program call:"                             >> $FULL_LOG_FILE 2>&1
}

writePgmLogFile()
{
   echo "$1 Log File:"                              >> $FULL_LOG_FILE 2>&1
   cat $2                                           >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
}

JOB_SUCCESSFUL="false"

# change to directory where this file resides
cd `dirname $0`
. MP.config
createDir $RUNTIME_DIR
createDir $ARCHIVE_DIR
installOntologyFiles
echo "Job Started: `date`"
echo "Job Started: `date`"                          > $FULL_LOG_FILE 2>&1
echo "Directory is: `pwd`"
#################################################################################
# Check Usage and options
#################################################################################
USAGE_STRING="Incorrect Usage\nCorrect Usage: $0 [load|noload] [full|incremental] \nExample: $0 load incremental"

if [ $# -ne 2 ] 
then
   die "$USAGE_STRING"
fi

echo "*****************************************" >> $FULL_LOG_FILE 2>&1
case $1 in
   load) LOAD_FLAG=""        
   echo  "DATABASE LOAD STATUS is LOAD" >> $FULL_LOG_FILE 2>&1
   ;;
   noload) LOAD_FLAG=-n      
   echo  "DATABASE LOAD STATUS is NO LOAD" >> $FULL_LOG_FILE 2>&1
   ;;
   *) die "$USAGE_STRING"    ;;
esac
case $2 in
   incremental) MODE_FLAG=-i ;;
   full) MODE_FLAG=-f        ;;
   *) die "$USAGE_STRING"    ;;
esac
echo  "MODE STATUS is $2" >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1

######################################################
# 1. Run GOload.py program
######################################################
MP_LOAD_PROGRAM=GOload.py
MP_LOAD_PROGRAM_CALL="${MP_LOAD_PROGRAM} $LOAD_FLAG $MODE_FLAG -l $MP_LOAD_LOG_FILE ${RCD_FILE}"

writePgmExecutionHeaders $MP_LOAD_PROGRAM
echo $MP_LOAD_PROGRAM_CALL                       >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1

msg=`$MP_LOAD_PROGRAM_CALL 2>&1`
rc=$?

writePgmLogFile $MP_LOAD_PROGRAM, $MP_LOAD_LOG_FILE

case $rc in
     $FAILURE)
        ERROR_MSG="${MP_LOAD_PROGRAM} FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:${MP_LOAD_PROGRAM} Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="${MP_LOAD_PROGRAM} Was Successful - No Errors Encountered"
        JOB_SUCCESSFUL="true"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1;;
esac
cat $MP_LOAD_LOG_FILE                      >> $FULL_LOG_FILE 2>&1
MP_LOAD_ERROR_MSG=$ERROR_MSG

######################################################
# 2. Finally, archive the files
######################################################
# We are using "jar" rather than "tar", because jar compressed
# the files to 6 times smaller than tar and its syntax is 
# identical to tar
# We are archiving everything at this point since this is the
# first release of the software and, for that reason it might
# be helpful to archive everything in case of problems; however,
# we might want to be more selective in the future.  We will
# also need an archival clean-up routine in the future as well
JAR_PROGRAM=jar
JAR_PROGRAM_CALL="jar cvf $ARCHIVE_FILE_NAME $RUNTIME_DIR/*"

writePgmExecutionHeaders $JAR_PROGRAM
echo $JAR_PROGRAM_CALL                           >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1
msg=`$JAR_PROGRAM_CALL  2>&1`
rc=$?
case $rc in
     $FAILURE)
        ERROR_MSG="JAR Failed!!!! - Check Archive"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:JAR Ouput is: $msg"       >> $FULL_LOG_FILE 2>&1;;

     $SUCCESS)
        ERROR_MSG="JAR Was Successful - No Errors Encountered"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1;;
   
     *)
        ERROR_MSG="JAR Had Warnings!!!  Archive"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:JAR Ouput is: $msg"       >> $FULL_LOG_FILE 2>&1;;

esac
JAR_PROGRAM_ERROR_MSG=$ERROR_MSG
######################################################
# 4. Notify Job Completion
######################################################
if test $JOB_SUCCESSFUL = "true"
then
   SUBJECT="Mammalian Phenotype Load Successful"
else
   SUBJECT="Mammalian Phenotype Load Failed"
fi
echo $SUBJECT

echo "Run Summary:"                                                                  > $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo "Mammalian Phenotype Downloader Completion Status:   $MP_DOWNLOADER_ERROR_MSG" >> $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo "Mammalian Phenotype Load Program Completion Status: $MP_LOAD_ERROR_MSG"       >> $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo "Archive Program Completion Status: $JAR_PROGRAM_ERROR_MSG"                    >> $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo ""   >> $MAIL_FILE_NAME
echo ""   >> $MAIL_FILE_NAME
echo ""   >> $MAIL_FILE_NAME
echo "Full Log File is as follows:"                                                 >> $MAIL_FILE_NAME
echo "************************************************************************"     >> $MAIL_FILE_NAME
echo "************************************************************************"     >> $MAIL_FILE_NAME


echo "Job Complete: `date`"
echo "Job Complete: `date`"                                                         >> $FULL_LOG_FILE 2>&1

cat $MAIL_FILE_NAME $FULL_LOG_FILE | mailx -s "$SUBJECT" $MAINTAINER 

# $Log$
# Revision 1.6  2003/03/25 17:39:34  lec
# new Configuration files
#

