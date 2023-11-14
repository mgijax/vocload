# Name: Node.py
# Purpose: contains a Node class, independent of graph representation

class Node:
    """
    #  Node object, independent of graph membership
    """
    
    def __init__(self, id, label):
        """
        #  Requires:
        #    id: string
        #    label: string
        #  Effects:
        #    constructor
        #  Modifies:
        #    self.id, self.label
        #  Returns:
        #  Exceptions:
        """
        
        self.id = id
        self.label = label
        self.synonyms = []

    def getId(self):
        """
        #  Requires:
        #  Effects:
        #    Returns node's id
        #  Modifies:
        #  Returns:
        #    self.id
        #  Exceptions:
        """
        
        return self.id

    def getLabel(self):
        """
        #  Requires:
        #  Effects:
        #    Returns node's label
        #  Modifies:
        #  Returns:
        #    self.label
        #  Exceptions:
        """

        return self.label

    def addSynonyms(self, syns):
        """
        #  Requires:
        #    syns: list of strings
        #  Effects:
        #    Adds a list of synonyms to the node
        #  Modifies:
        #    self.synonyms: list
        #  Returns:
        #  Exceptions:
        """

        self.synonyms = syns

    def getSynonyms(self):
        """
        #  Requires:
        #  Effects:
        #    Returns node's synonyms
        #  Modifies:
        #  Returns:
        #    self.synonyms
        #  Exceptions:
        """

        return self.synonyms

#
# Warranty Disclaimer and Copyright Notice
# 
#  THE JACKSON LABORATORY MAKES NO REPRESENTATION ABOUT THE SUITABILITY OR 
#  ACCURACY OF THIS SOFTWARE OR DATA FOR ANY PURPOSE, AND MAKES NO WARRANTIES, 
#  EITHER EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A 
#  PARTICULAR PURPOSE OR THAT THE USE OF THIS SOFTWARE OR DATA WILL NOT 
#  INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS, OR OTHER RIGHTS.  
#  THE SOFTWARE AND DATA ARE PROVIDED "AS IS".
# 
#  This software and data are provided to enhance knowledge and encourage 
#  progress in the scientific community and are to be used only for research 
#  and educational purposes.  Any reproduction or use for commercial purpose 
#  is prohibited without the prior express written permission of the Jackson 
#  Laboratory.
# 
# Copyright (c) 1996, 1999, 2002 by The Jackson Laboratory
# All Rights Reserved
#
