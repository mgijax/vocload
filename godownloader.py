#!/usr/local/bin/python
"""
#    GO_downloader.py
#
#    Downloads ontology and definition flat files from Stanford
#    GO FTP site.  It checks each new file for parsing errors - if
#    none are found, it overwrites the existing local file.
#
"""

import sys, os, ftplib
import GOVocab

SERVER = 'genome-ftp.stanford.edu'       # GO FTP server
ONT_DIR = 'pub/go/ontology'              # ontology file directory
DEFS_DIR = 'pub/go/doc'                  # definitions file directory


# Functions
############

ParseError = "Error parsing input file"

def f_writer(line):
    """
    #  Requires:
    #    line: string
    #  Effects:
    #    Writes each line of downloaded function ontology file to local file
    #  Modifies:
    #  Returns:
    #  Exceptions:
    """

    f_out.write(line + '\n')
    return

def p_writer(line):
    """
    #  Process ontology file parser
    """

    p_out.write(line + '\n')
    return

def c_writer(line):
    """
    #  Component ontology file parser
    """

    c_out.write(line + '\n')
    return

def defs_writer(line):
    """
    #  Definitions file parser
    """

    defs_out.write(line + '\n')
    return

def getOntologies(server, dir):
    """
    #  Requires:
    #    server: string
    #    dir: string
    #  Effects:
    #    Uses ftplib to download ontology flat files
    #  Modifies:
    #  Returns:
    #  Exceptions:
    """
    
    ftp = ftplib.FTP(server)
    ftp.login()
    ftp.cwd(dir)

    # use parser functions to process one line at a time
    ftp.retrlines("RETR function.ontology", f_writer)
    ftp.retrlines("RETR process.ontology", p_writer)
    ftp.retrlines("RETR component.ontology", c_writer)

def getDefsFile(server, dir):
    """
    #  Requires:
    #    server: string
    #    dir: string
    #  Effects:
    #    Uses ftplib to download GO definitions file
    #  Modifies:
    #  Returns:
    #  Exceptions:
    """

    ftp = ftplib.FTP(server)
    ftp.login()
    ftp.cwd(dir)

    ftp.retrlines("RETR GO.defs", defs_writer)

def alias():
    """
    #  Requires:
    #  Effects:
    #    Parses the newly downloaded ontology files and renames them to
    #    replace the older files.  If parsing errors are encountered,
    #    the older file remains in place and the error is logged.
    #  Modifies:
    #  Returns:
    #  Exceptions:
    """

    f_in = open(funcName, 'r')
    p_in = open(procName, 'r')
    c_in = open(compName, 'r')

    files = {funcName: f_in,
             procName: p_in,
             compName: c_in}

    for fname in files.keys():
        ifile = files[fname]
        newName = fname + '.txt'

        # check for parsing errors before replacing old file
        try:
            GO = GOVocab.GOVocab()
	    GO.initializeRegExps ("GO")
            graph = GO.parseGOfile(ifile)
            os.rename(fname, newName)
            ifile.close()
            del graph
        except:
            ifile.close()
            raise ParseError, 'while parsing file: ' + fname

# Main
#######

# set output directory from configuration file
if os.environ.has_key("RUNTIME_DIR"):
    data_dir = os.environ["RUNTIME_DIR"]
else:
    data_dir = './'

funcName = data_dir + 'function.ontology'      # function ontolgy file name
procName = data_dir + 'process.ontology'       # process ontology file name
compName = data_dir + 'component.ontology'     # component ontology file name
defsName = data_dir + 'GO.defs'                # definitions file name

logFile = data_dir +'godownloader.log'

errLog = open(logFile, 'w')

f_out = open(funcName, 'w')
p_out = open(procName, 'w')
c_out = open(compName, 'w')
defs_out = open(defsName, 'w')
    
try:
   getOntologies(SERVER, ONT_DIR)
   getDefsFile(SERVER, DEFS_DIR)
except:
   errLog.write('Error getting ontology and/or def files from Stanford\n')
   errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
   sys.exit(1)


try:
   # close files before calling alias function
   f_out.close()
   p_out.close()
   c_out.close()
   defs_out.close()
   alias()

except ParseError, message:
    errLog.write(ParseError + message + '\n')
    errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
    sys.exit(1)

except:
    errLog.write('General error:\n')
    errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
    sys.exit(1)

errLog.write ( 'godownloader.py completed successfully: ' + data_dir )
errLog.write ( 'compName = ' + funcName )
errLog.write ( 'procName = ' + funcName )
errLog.close()
sys.exit(0)

