#!/bin/sh

#
# Program: runGOLoad.sh
#
# Purpose:
#
# Main Wrapper Script for Downloading Ontology files and generating GO Terms and GO DAG
# 
# Usage:
#
#	runGOLoad.sh [load|noload] [full|incremental]
#
# History:
#
#	lec	03/25/2003
#	- use new Configuration and GO.config files
#

die()
{
   echo $1
   cat $FULL_LOG_FILE | mailx -s "GO Load Catastrophic FAILURE" $MAINTAINER 
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

godownload()
{
   GO_DOWNLOADER_PROGRAM=GOdownloader.py
   GO_DOWNLOADER_PROGRAM_CALL="./GOdownloader.py"

   writePgmExecutionHeaders $GO_DOWNLOADER_PROGRAM
   echo $GO_DOWNLOADER_PROGRAM_CALL                 >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1

   msg=`$GO_DOWNLOADER_PROGRAM_CALL`
   rc=$?
   writePgmLogFile $GO_DOWNLOADER_PROGRAM, $GO_DOWNLOADER_LOG_FILE
   case $rc in
     $FAILURE)
        ERROR_MSG="GOdownloader.py FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                >> $FULL_LOG_FILE 2>&1
        echo "$0:GOdownloader.py Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="GOdownloader.py Was Successful - No Errors Encountered"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                >> $FULL_LOG_FILE 2>&1;;
   esac

   GO_DOWNLOADER_ERROR_MSG=$ERROR_MSG
   cat $GO_DOWNLOADER_LOG_FILE               >> $FULL_LOG_FILE 2>&1
}

JOB_SUCCESSFUL="false"

# change to directory where this file resides
cd `dirname $0`
. GO.config
createDir $RUNTIME_DIR
createDir $ARCHIVE_DIR

rm -rf $FULL_LOG_FILE $MAIL_FILE_NAME $GO_LOAD_LOG_FILE
touch $FULL_LOG_FILE $MAIL_FILE_NAME $GO_LOAD_LOG_FILE

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

#############################################################
# 1. Run GOdownloader.py program to get latest ontology files
#############################################################
#godownload

######################################################
# 2. Run GOload.py program
######################################################
GO_LOAD_PROGRAM=GOload.py
GO_LOAD_PROGRAM_CALL="${GO_LOAD_PROGRAM} $LOAD_FLAG $MODE_FLAG -l $GO_LOAD_LOG_FILE ${RCD_FILE}"

writePgmExecutionHeaders $GO_LOAD_PROGRAM
echo $GO_LOAD_PROGRAM_CALL                       >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1

msg=`$GO_LOAD_PROGRAM_CALL 2>&1`
rc=$?

writePgmLogFile $GO_LOAD_PROGRAM, $GO_LOAD_LOG_FILE

case $rc in
     $FAILURE)
        ERROR_MSG="${GO_LOAD_PROGRAM} FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:${GO_LOAD_PROGRAM} Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="${GO_LOAD_PROGRAM} Was Successful - No Errors Encountered"
        JOB_SUCCESSFUL="true"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1;;
esac
cat $GO_LOAD_LOG_FILE                      >> $FULL_LOG_FILE 2>&1
GO_LOAD_ERROR_MSG=$ERROR_MSG

######################################################
# 3. Remove annotations to obsoleted terms
######################################################
GOremoveannot.py -S$DBSERVER -D$DATABASE -U$DBUSER -P$DBPASSWORD_FILE

######################################################
# 4. Finally, archive the files
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
   SUBJECT="GO Load Successful"
else
   SUBJECT="GO Load Failed"
fi
echo $SUBJECT

echo "Run Summary:"                                                                  > $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo "GO Downloader Completion Status:   $GO_DOWNLOADER_ERROR_MSG"                  >> $MAIL_FILE_NAME
echo "****************************************************************************" >> $MAIL_FILE_NAME
echo "GO Load Program Completion Status: $GO_LOAD_ERROR_MSG"                        >> $MAIL_FILE_NAME
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
# Revision 1.26  2003/03/25 17:39:33  lec
# new Configuration files
#
# Revision 1.25  2003/03/25 17:13:52  lec
# new Configuration files
#
# Revision 1.24  2003/03/25 17:12:58  lec
# new Configuration files
#
# Revision 1.23  2003/03/25 15:48:16  lec
# new configuration files
#
# Revision 1.22  2003/03/25 14:59:30  lec
# new configuration files/names
#
# Revision 1.21  2003/03/25 14:50:20  lec
# new Configuraiton files
#
# Revision 1.20  2003/03/25 14:23:56  lec
# new Configuration files
#
# Revision 1.19  2003/03/25 13:31:04  lec
# new Configuration files
#

