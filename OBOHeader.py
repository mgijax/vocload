import sys
import os
import string

# CLASS: Header
# IS: An object that holds specific attributes from the header of an
#     OBO format file.
# HAS: Header attributes
# DOES: Nothing
#
class Header:

    # Purpose: Constructor
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Initializes the attributes
    # Throws: Nothing
    #
    def __init__ (self):
        self.clear()


    # Purpose: Clears the attributes
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Clears the attributes
    # Throws: Nothing
    #
    def clear (self):
        self.defaultNamespace = ''


    # The following methods are used to set/get the attributes of the
    # header object.
    #

    def setVersion (self, version):
        self.version = version

    def getVersion (self):
        return self.version

    def setDefaultNamespace (self, defaultNamespace):
        self.defaultNamespace = defaultNamespace

    def getDefaultNamespace (self):
        return self.defaultNamespace
