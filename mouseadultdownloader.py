#!/usr/local/bin/python
"""
#    mouseadultdownloader.py
#
#    Downloads ontology and definition flat files from Stanford
#    GOBO FTP site.  It checks each new file for parsing errors - if
#    none are found, it overwrites the existing local file.
#
#    copied from godownloader.py (to remain consistent)
#	02/24/2003 lec (TR 4537)
#
"""

import sys, os, ftplib
import GOVocab

SERVER = 'genome-ftp.stanford.edu'       # GO FTP server
ONT_DIR = 'pub/go/gobo/anatomy.ontology' # ontology file directory


# Functions
############

ParseError = "Error parsing input file"

def o_writer(line):
    """
    #  Requires:
    #    line: string
    #  Effects:
    #    Writes each line of downloaded ontology file to local file
    #  Modifies:
    #  Returns:
    #  Exceptions:
    """

    o_out.write(line + '\n')
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
    ftp.retrlines("RETR adult_mouse_anatomy", o_writer)

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

    o_in = open(ontName, 'r')

    files = {ontName: o_in}

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

ontName = data_dir + 'adult_mouse_anatomy'

logFile = data_dir + 'mouseadultdownloader.log'

errLog = open(logFile, 'w')

o_out = open(ontName, 'w')
    
try:
   getOntologies(SERVER, ONT_DIR)
except:
   errLog.write('Error getting ontology files from Stanford\n')
   errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
   sys.exit(1)


try:
   # close files before calling alias function
   o_out.close()
   alias()

except ParseError, message:
    errLog.write(ParseError + message + '\n')
    errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
    sys.exit(1)

except:
    errLog.write('General error:\n')
    errLog.write(sys.exc_type + ': ' + sys.exc_value + '\n')
    sys.exit(1)

errLog.write ( 'mouseadultdownloader.py completed successfully: ' + data_dir )
errLog.write ( 'compName = ' + ontName )
errLog.write ( 'procName = ' + ontName )
errLog.close()
sys.exit(0)

