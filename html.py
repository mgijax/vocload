#!/usr/local/bin/python

# This is a simple library to return an html
# string to the program calling a method.
# This object contains no data; it simply
# encapsulates a few basic html operations

import vocloadlib

EOL = '\n'
TODAYS_DATE = vocloadlib.timestamp("")

def getStartTableHTML ():
   return "<Table border cellpadding = 2 cellspacing = 3 width = 90%><TR align=center>" + EOL

def getEndTableHTML():
   return "</Table>" + EOL

def getCellHTML ( cellContent ):
   return "<TD>" + cellContent + "</TD>" + EOL

def getTableHeaderLabelHTML( cellContent ):
   return getCellHTML ("<B>" + cellContent + "</B>") + EOL

def getStartTableRowHTML():
   return "<TR align=center>" + EOL

def getEndTableRowHTML():
   return "</TR>" + EOL

def getStartHTMLDocumentHTML( documentTitle ):
   return "<HTML>" + EOL + \
          "<HEAD>" + EOL + \
          "<TITLE>" + documentTitle + "</TITLE>" + EOL + \
          "</HEAD>" + EOL + \
          "<BODY bgcolor=#ffffff>" + EOL + \
          "<H1><U><CENTER>" + documentTitle + "</H1></U></CENTER>" + EOL + \
          "<H2><CENTER><I> DATE:" + TODAYS_DATE + "</I></CENTER></H2>"

def getEndHTMLDocumentHTML():
   return "</BODY>" + EOL + \
          "</HTML>" + EOL



