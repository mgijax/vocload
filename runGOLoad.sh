#!/bin/sh

#
# Script for Downloading Ontology files and generating GO Terms and GO DAG
#

# Define return codes
SUCCESS=0
FAILURE=1

# NEED TO FIGURE THIS OUT!!! CONFIGURATION_FILE=
# Take out this hard code!!!!
# to work with configuration file
# GO_DIR="/usr/local/mgi/go_data/"
GO_DIR="/tmp/"

SYBASE=/opt/sybase
PYTHONPATH=/usr/local/mgi/lib/python
PATH=$PATH:.:/usr/bin:$SYBASE/bin
FULL_LOG_FILE=$GO_DIR"./log.txt"
TERM_FILE=$GO_DIR"Termfile"
MAINTAINER="tcw@informatics.jax.org"

export GO_DIR
export SYBASE
export PYTHONPATH
export PATH


die()
{
   echo $1
   exit $FAILURE
}

changeToRunDirectory()
{
   APPDIR=`dirname $0`
   if test $APPDIR != "."
   then
      cd "$APPDIR"
   fi
}

writePgmExecutionHeaders()
{
   echo "Running $1 Program..."
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "Running $1 Program..."                     >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo " Program call:"                            >> $FULL_LOG_FILE 2>&1
   echo $2                                          >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
}

writePgmLogFile()
{
   echo "$1 Log File:"                              >> $FULL_LOG_FILE 2>&1
   cat $2                                           >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
}

JOB_SUCCESSFUL="false"

# Source the applicable configuration file:
changeToRunDirectory
# Take out!!! modify to read config file
echo "Job Started: `date`"
echo "Job Started: `date`"                          > $FULL_LOG_FILE 2>&1
echo "Directory is: `pwd`"

#############################################################
# 1. Run godownloader.py program to get latest ontology files
#############################################################
GO_DOWNLOADER_PROGRAM=godownloader.py
GO_DOWNLOADER_PROGRAM_CALL="./godownloader.py"
GO_DOWNLODER_LOG_FILE="godownloader.log"

writePgmExecutionHeaders $GO_DOWNLOADER_PROGRAM, $GO_DOWNLOADER_PROGRAM_CALL

$GO_DOWNLOADER_PROGRAM_CALL
rc=$?
writePgmLogFile $GO_DOWNLOADER_PROGRAM, $GO_DOWNLODER_LOG_FILE
case $rc in
     $FAILURE)
        ERROR_MSG="goownloader.py FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG           >> $FULL_LOG_FILE 2>&1
        #echo "$0:godownloader.py Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="godownloader.py Was Successful - No Errors Encountered"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG  >> $FULL_LOG_FILE 2>&1;;
esac

GO_DOWNLOADER_ERROR_MSG=$ERROR_MSG

######################################################
# 2. Run go.load program
######################################################
GO_LOAD_PROGRAM=go.load
GO_LOAD_LOG_FILE="log.txt"
GO_LOAD_PROGRAM_CALL="go.load -l $GO_LOAD_LOG_FILE -f go.rcd"
# GO_LOAD_PROGRAM_CALL="./go.load -f -n -l goload.txt go.rcd"
# This is for Lori only!!!#######################
if [ -f $TERM_FILE ]
then
   echo "copying Termfile to backup"
   `mv -f $TERM_FILE $TERM_FILE.backup`
fi
#################################################
writePgmExecutionHeaders $GO_LOAD_PROGRAM, $GO_LOAD_PROGRAM_CALL

$GO_LOAD_PROGRAM_CALL 
rc=$?

writePgmLogFile $GO_LOAD_PROGRAM, $GO_LOAD_LOG_FILE

case $rc in
     $FAILURE)
        ERROR_MSG="go.load FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG           >> $FULL_LOG_FILE 2>&1
        #echo "$0:goload.py Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="go.load Was Successful - No Errors Encountered"
        JOB_SUCCESSFUL="true"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG  >> $FULL_LOG_FILE 2>&1;;
esac

# too big!! cat goload.txt                                >> $FULL_LOG_FILE 2>&1
echo "Copying ./Termfile to $TERM_FILE"
cp -p ./Termfile $TERM_FILE

GO_LOAD_ERROR_MSG=$ERROR_MSG

######################################################
# N. Notify Job Completion
######################################################
if test $JOB_SUCCESSFUL = "true"
then
   SUBJECT="GO Load Successful"
else
   
   SUBJECT="GO Load Failed"
fi
echo $SUBJECT

echo "Run Summary:"                                                                  > $$.txt
echo "****************************************************************************" >> $$.txt
echo "GO Downloader Completion Status:   $GO_DOWNLOADER_ERROR_MSG"                  >> $$.txt
echo "****************************************************************************" >> $$.txt
echo "GO Load Program Completion Status: $GO_LOAD_ERROR_MSG"                        >> $$.txt
echo "****************************************************************************" >> $$.txt
echo ""   >> $$.txt
echo ""   >> $$.txt
echo ""   >> $$.txt
echo "Full Log File is as follows:"                                                 >> $$.txt
echo "************************************************************************"     >> $$.txt
echo "************************************************************************"     >> $$.txt


echo "Job Complete: `date`"
echo "Job Complete: `date`"                                                         >> $FULL_LOG_FILE 2>&1

cat $$.txt $FULL_LOG_FILE | mailx -s "$SUBJECT" $MAINTAINER 

rm -rf $$.txt
