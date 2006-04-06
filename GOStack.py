# Name: GOStack.py
# Purpose: GO Stack class
#
# History
#
# 12/15/2005 lec
#	- TR 5677
#	- moved Stack class into new file from GOVocab.py
#

import os

class Stack:
    """
    #  Object representing a stack
    """

    def __init__(self):
        """
        #  Requires:
        #  Effects:
        #    constructor
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #  Exceptions:
        """
        
        self.stack = []

    def push(self, obj):
        """
        #  Requires:
        #    obj: any object
        #  Effects:
        #    Appends obj to self.stack
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #  Exceptions:
        """
        
        self.stack.append(obj)

    def pop(self):
        """
        #  Requires:
        #  Effects:
        #    If self.stack is not empty, returns the last element of the
        #    list.  Slices last element off of self.stack.
        #  Modifies:
        #    self.stack: list
        #  Returns:
        #    rval: any object
        #  Exceptions:
        #    STACKEMPTY
        """
        
        if self.isEmpty():
            raise "STACKEMPTY"
        rval = self.stack[-1]
        self.stack = self.stack[:-1]
        return rval

    def peek(self):
        """
        #  Requires:
        #  Effects:
        #    If self.stack is not empty, returns the last element of the
        #    list.
        #  Modifies:
        #  Returns:
        #    rval: any object
        #  Exceptions:
        #    STACKEMPTY
        """
        
        if self.isEmpty():
            raise "STACKEMPTY"
        rval = self.stack[-1]
        return rval

    def isEmpty(self):
        """
        #  Requires:
        #  Effects:
        #    Tests for len of self.stack; if empty, returns true.
        #  Modifies:
        #  Returns:
        #    boolean
        #  Exceptions:
        """
        
        return len(self.stack) == 0

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
