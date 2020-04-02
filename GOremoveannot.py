
#
# Program: GOremoveannot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	To remove GO anntotations to obsoleted terms for
#	evidence J:60000, J:77247 or J:56000, J:72245.
#
#	To produce a tab-delimited report of deleted annotations:
#
#		MGI ID
#		Gene Symbol
#		Gene Name
#		GO ID
#		GO Term
#
# Requirements Satisfied by This Program:
#
#	TR 4623
#
# Usage:
#	program.py
#	-S = database server
#	-D = database
#	-U = user
#	-P = password file
#
# Envvars:
#
# Inputs:
#
# Outputs:
#
#	Report: GOremoveannot.rpt
#
# Exit Codes:
#
# Assumes:
#
# Bugs:
#
# Implementation:
#
# History
#
# 05/11/2005	lec
#	- added J:72245
#

import sys
import os
import getopt
import mgi_utils
import reportlib
import db

#globals

TAB = reportlib.TAB	# tab
CRT = reportlib.CRT	# carriage return/newline

diagFile = ''		# diagnostic file descriptor
reportFile = ''		# report file descriptor

diagFileName = ''	# diagnostic file name
reportFileName = ''	# report file name
passwordFileName = ''	# password file name

def showUsage():
    # Purpose: displays correct usage of this program
    # Returns: nothing
    # Assumes: nothing
    # Effects: exits with status of 1
    # Throws: nothing
 
    usage = 'usage: %s -S server\n' % sys.argv[0] + \
        '-D database\n' + \
        '-U user\n' + \
        '-P password file\n'

    exit(1, usage)
 
def exit(
    status,          # numeric exit status (integer)
    message = None   # exit message string
    ):

    # Purpose:
    # Returns: nothing
    # Assumes: nothing
    # Effects: nothing
    # Throws: nothing

    if message is not None:
        sys.stderr.write('\n' + str(message) + '\n')
 
    try:
        diagFile.write('\n\nEnd Date/Time: %s\n' % (mgi_utils.date()))
        diagFile.close()
    except:
        pass

    try:
        reportlib.finish_nonps(reportFile)
    except:
        pass

    db.useOneConnection(0)
    sys.exit(status)
 
def init():
    # Purpose: process command line options
    # Returns: nothing
    # Assumes: nothing
    # Effects: initializes global variables
    #          calls showUsage() if usage error
    #          exits if files cannot be opened
    # Throws: nothing

    global diagFile, reportFile, reportFileName, diagFileName, passwordFileName
    global mode
 
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'S:D:U:P:')
    except:
        showUsage()
 
    #
    # Set server, database, user, passwords depending on options
    # specified by user.
    #
 
    server = ''
    database = ''
    user = ''
    password = ''
 
    for opt in optlist:
        if opt[0] == '-S':
            server = opt[1]
        elif opt[0] == '-D':
            database = opt[1]
        elif opt[0] == '-U':
            user = opt[1]
        elif opt[0] == '-P':
            passwordFileName = opt[1]
        else:
            showUsage()

    # User must specify Server, Database, User and Password
    password = str.strip(open(passwordFileName, 'r').readline())
    if server == '' or \
        database == '' or \
        user == '' or \
        password == '':
        showUsage()

    # Initialize db.py DBMS parameters
    db.set_sqlLogin(user, password, server, database)
    db.useOneConnection(1)
 
    head, tail = os.path.split(sys.argv[0])
    diagFileName = os.environ['RUNTIME_DIR'] + '/' + tail + '.diagnostics'
    reportFileName = tail + '.rpt'

    try:
        diagFile = open(diagFileName, 'w')
    except:
        exit(1, 'Could not open file %s\n' % diagFileName)
                
    try:
        reportFile = reportlib.init(reportFileName, 'Deleted:  Marker Annotations To Obsolete Terms', outputdir = os.environ['RUNTIME_DIR'])
    except:
        exit(1, 'Could not open file %s\n' % reportFileName)
                
    # Log all SQL
    db.set_sqlLogFunction(db.sqlLogAll)

    # Set Log File Descriptor
    #db.set_sqlLogFD(diagFile)

    diagFile.write('Start Date/Time: %s\n' % (mgi_utils.date()))
    diagFile.write('Server: %s\n' % (server))
    diagFile.write('Database: %s\n' % (database))
    diagFile.write('User: %s\n' % (user))

    return

def process():
    # Purpose: process updates, print records to report
    # Returns: nothing
    # Assumes: nothing
    # Effects: 
    # Throws: nothing

    db.sql('select a.accID, a._Object_key, t.term ' + \
        'into temp obsolete ' + \
        'from VOC_Term_ACC_View a, VOC_Term t ' + \
        'where t._Vocab_key = 4 ' + \
        'and t.isObsolete = 1 ' + \
        'and t._Term_key = a._Object_key', None)

    db.sql('create index idx_key on obsolete(_Object_key)', None)

    results = db.sql('select m.symbol, m.name, ma.accID, o.accID as goid, o.term ' + \
        'from obsolete o, VOC_Annot a, VOC_Evidence e, MRK_Marker m, ACC_Accession ma ' + \
        'where a._AnnotType_key = 1000 ' + \
        'and a._Term_key = o._Object_key ' + \
        'and a._Annot_key = e._Annot_key ' + \
        'and e._Refs_key in (59154,61933,73199,73197) ' + \
        'and a._Object_key = m._Marker_key ' + \
        'and a._Object_key = ma._Object_key ' + \
        'and ma._MGIType_key = 2 ' + \
        'and ma._LogicalDB_key = 1 ' + \
        'and ma.prefixPart = \'MGI:\' ' + \
        'and ma.preferred = 1', 'auto')

    for r in results:
        reportFile.write(r['accID'] + TAB + \
            r['symbol'] + TAB + \
            r['name'] + TAB + \
            r['goid'] + TAB + \
            r['term'] + CRT)

    db.sql('delete from VOC_Evidence ' + \
        'using obsolete o, VOC_Annot a ' + \
        'where a._AnnotType_key = 1000 ' + \
        'and a._Term_key = o._Object_key ' + \
        'and a._Annot_key = VOC_Evidence._Annot_key ' + \
        'and VOC_Evidence._Refs_key in (59154,61933,73199,73197)', None)

    db.sql('delete from VOC_Annot a ' + \
        'where _AnnotType_key = 1000 and not exists (select 1 from VOC_Evidence e where a._Annot_key = e._Annot_key)', None)


    db.commit()


#
# Main
#

init()
process()
exit(0)
