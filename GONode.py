# Purpose: representation of a node in the Gene Ontology
#
# History
#
# 04/02/2003 lec
#	- TR 4564; added support for comments (self.comment, setComment(), getComment())
#

import Node

class GONode(Node.Node):
    """
    #  Object representing a node in the GO vocabulary
    """

    def __init__(self, id, label):
        """
        #  Requires:
        #    id: string
        #    label: string
        #  Effects:
        #    constructor (adds definition, comment and secondary ID attributes)
        #  Modifies:
        #    self.definition
        #  Returns:
        #  Exceptions:
        """

        Node.Node.__init__(self, id, label)
        self.definition = ''
        self.comment = ''
        self.secondaryGOIDs = []
        return

    def setDefinition(self, definition):
        """
        #  Requires:
        #    definition: string
        #  Effects:
        #    Sets the GO term's definition to the given string
        #  Modifies:
        #    self.definition (attribute specific to GONode)
        #  Returns:
        #  Exceptions:
        """

        self.definition = definition

    def setComment(self, comment):
        """
        #  Requires:
        #    comment: string
        #  Effects:
        #    Sets the GO term's comment to the given string
        #  Modifies:
        #    self.comment (attribute specific to GONode)
        #  Returns:
        #  Exceptions:
        """

        self.comment = comment

    def setSecondaryGOIDs(self, secondaryGOIDs):
        """
        #  Requires:
        #    secondaryGOIDs: list
        #  Effects:
        #    Sets the GO term's secondaryGOIDs to the given list
        #  Modifies:
        #    self.secondaryGOIDs
        #  Returns:
        #  Exceptions:
        """
        self.secondaryGOIDs = secondaryGOIDs

    def getDefinition(self):
        """
        #  Requires:
        #  Effects:
        #    Returns the GO term's definition
        #  Modifies:
        #  Returns:
        #    self.definition: string
        #  Exceptions:
        """

        return self.definition
 
    def getComment(self):
        """
        #  Requires:
        #  Effects:
        #    Returns the GO term's comment
        #  Modifies:
        #  Returns:
        #    self.comment: string
        #  Exceptions:
        """

        return self.comment
 
    def getSecondaryGOIDs(self):
        """
        #  Requires:
        #  Effects:
        #    Returns the GO term's secondary IDs
        #  Modifies:
        #  Returns:
        #    self.secondarGOIDs: list
        #  Exceptions:
        """
        return self.secondaryGOIDs

#

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
# Copyright © 1996, 1999, 2000 by The Jackson Laboratory
# All Rights Reserved
#
