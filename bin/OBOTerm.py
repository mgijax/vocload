import os
import re

# CLASS: Term
# IS: An object that holds specific attributes from a Term stanza of an
#     OBO format file.
# HAS: Term attributes
# DOES: Nothing
#
class Term:

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
        self.termID = ''
        self.name = ''
        self.namespace = ''
        self.comment = ''
        self.definition = ''
        self.obsolete = 0
        self.altID = []
        self.relationship = []
        self.relationshipType = []
        self.synonym = []
        self.synonymType = []
        self.subset = []


    # The following methods are used to set/get the attributes of the
    # term object.
    #

    def setTermID (self, termID):
        self.termID = termID

    def getTermID (self):
        return self.termID

    def setName (self, name):
        self.name = name

    def getName (self):
        return self.name

    def setNamespace (self, namespace):
        self.namespace = namespace

    def getNamespace (self):
        return self.namespace

    def setComment (self, comment):
        self.comment = comment

    def getComment (self):
        return ''.join([i if ord(i) < 128 else ' ' for i in self.comment])

    def setDefinition (self, definition):
        self.definition = definition

    def getDefinition (self):
        return ''.join([i if ord(i) < 128 else ' ' for i in self.definition])

    def setObsolete (self, obsolete):
        self.obsolete = obsolete

    def getObsolete (self):
        return self.obsolete

    def addAltID (self, altID):
        self.altID.append(altID)

    def getAltID (self):
        return self.altID

    def addRelationship (self, relationship):
        self.relationship.append(relationship)

    def getRelationship (self):
        return self.relationship

    def addRelationshipType (self, relationshipType):
        self.relationshipType.append(relationshipType)

    def getRelationshipType (self):
        return self.relationshipType

    def addSynonym (self, synonym):
        self.synonym.append(synonym)

    def getSynonym (self):
        return self.synonym

    def addSynonymType (self, synonymType):
        self.synonymType.append(synonymType)

    def getSynonymType (self):
        return self.synonymType
    
    def addSubset (self, subset):
        self.subset.append(subset)

    def getSubset (self):
        return self.subset

    # Purpose: Return all the attributes as one str.(for debugging).
    # Returns: String of all objects.
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    def debug (self):
        return '|termID=' + self.termID + \
               '|name=' + self.name + \
               '|namespace=' + self.namespace + \
               '|comment=' + self.comment + \
               '|definition=' + self.definition + \
               '|obsolete=' + str(self.obsolete) + \
               '|altID=' + ','.join(self.altID) + \
               '|relationship=' + ','.join(self.relationship) + \
               '|relationshipType=' + ','.join(self.relationshipType) + \
               '|synonym=' + ','.join(self.synonym) + \
               '|synonymType=' + ','.join(self.synonymType) + \
               '|subset=' + ','.join(self.subset) + '|'
