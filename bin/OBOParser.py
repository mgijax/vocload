import os
import re

import OBOHeader
import OBOTerm

# CLASS: Parser
# IS: An object that knows how to parse an OBO format file and extract
#     specific attributes that are needed by the OBO vocabulary loader.
# HAS: A header object to hold header attributes and a term object
#      to hold term attributes.
# DOES: Parses the OBO format file.
#
class Parser:

    # Purpose: Constructor
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Initializes header and term objects.
    # Throws: Nothing
    #
    def __init__(self, fpOBO, log):
        self.fpOBO = fpOBO
        self.log = log	# for debugging only
        self.vocabName = os.environ['VOCAB_NAME']

        # Create the head an term objects.
        #
        self.header = OBOHeader.Header()
        self.term = OBOTerm.Term()

        # Read through the header records from the OBO file and save the
        # necessary attributes in the header object.
        #
        self.line = self.fpOBO.readline()
        while self.line and self.line[0] != '[':
            self.line = self.line[:-1]
            tag = re.split (':', self.line, 1)[0]

            # Save the version number.
            #
            if tag == 'format-version':
                self.header.setVersion (re.split (' ', self.line, 1)[1])

            # Save the default namespace.
            #
            if tag == 'default-namespace':
                self.header.setDefaultNamespace (re.split (' ', self.line, 1)[1])

            # Read the next line from the OBO file.
            #
            self.line = self.fpOBO.readline()


    # Purpose: Returns the header object.
    # Returns: Header object
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    def getHeader (self):
        return self.header


    # Purpose: Parser the next "Term" stanza from the OBO input file and
    #          load the necessary attributes into the term object.
    # Returns: Next term object
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    def nextTerm (self):
        self.term.clear()

        # Read through the OBO file until a term stanza is found or EOF is
        # reached.
        #
        while self.line and self.line[0:6] != '[Term]':
            self.line = self.fpOBO.readline()

        # If the current line is not the start of a term stanza, it must be
        # an EOF condition.
        #
        if self.line[0:6] != '[Term]':
            return None

        # Read the first line of the term stanza and continue to process the
        # term until another stanza is found or EOF is reached.
        #
        self.line = self.fpOBO.readline()

        while self.line and self.line[0] != '[':
            self.line = self.line[:-1]
            tag = re.split (':', self.line, 1)[0]

            # Save the term ID.
            #
            if tag == 'id':
                self.term.setTermID (re.split (' ', self.line, 1)[1].strip())

            # Save the term name.
            #
            if tag == 'name':
                self.term.setName (re.split (' ', self.line, 1)[1].strip())

            # Save the namespace.
            #
            if tag == 'namespace':
                self.term.setNamespace (re.split (' ', self.line, 1)[1].strip())

            # Save the comment.
            #
            if tag == 'comment':
                self.term.setComment (re.split (' ', self.line, 1)[1])

            # Save the definition.
            #
            if tag == 'def':
                newLine = self.line.replace('\\"', "'")
                self.term.setDefinition (re.split ('"', newLine)[1])

            # Save the obsolete indicator.
            #
            if tag == 'is_obsolete':
                obsolete = re.split (' ', self.line, 1)[1]
                if obsolete == 'true':
                    self.term.setObsolete (1)
                else:
                    self.term.setObsolete (0)

            # Save an alternate ID.
            # per TR13072/do not attach alt_id for Disease Ontology
            if tag == 'alt_id' and self.vocabName != 'Disease Ontology':
                self.term.addAltID (re.split (' ', self.line, 1)[1].strip())

            # Save an alternate ID using xref.
            # hard-coded list of xref to be loaded from Disease Ontology
            xrefList = ['OMIM:', 'EFO:', 'KEGG:', 'MESH:', 'NCI:', 'ORDO:', 'HP:', 'UMLS_CUI', 'ICD10CM', 'ICD9CM']
            if tag == 'xref' and self.vocabName == 'Disease Ontology':
                for x in xrefList:
                    if self.line.find(x) >= 0:
                        xrefID = re.split (' ', self.line, 1)[1].strip()
                        xrefID = xrefID.replace('\\n', '')
                        xrefID = re.split ('{', xrefID, 1)[0].strip()
                        self.term.addAltID (xrefID)

            # Save an "is-a" relationship.
            #
            if tag == 'is_a':
                self.term.addRelationship (re.split (' ', self.line)[1])
                self.term.addRelationshipType ('is-a')

            # Save an "union_of" relationship.
            #
            if tag == 'union_of':
                self.term.addRelationship (re.split (' ', self.line)[1])
                self.term.addRelationshipType ('union_of')

            # Save a relationship.
            #
            if tag == 'relationship':
                if self.vocabName == 'Disease Ontology':
                    continue
                self.term.addRelationship (re.split (' ', self.line)[2])
                self.term.addRelationshipType (re.split (' ', self.line)[1])

            # Save a synonym and its synonym type.
            #
            if tag == 'synonym':
                self.term.addSynonym (re.split ('"', self.line)[1].rstrip())
                synType = re.split (' ', re.split ('"', self.line)[2].lstrip())[0]
                if self.vocabName == 'Feature Relationship' and synType == 'RELATED':
                    # example from obo file:
                    # synonym: "contains" RELATED REVERSE
                    # synonym: "is in " RELATED FORWARD

                    # RELATED FORWARD/RELATED REVERSE
                    synType = synType + ' ' + re.split (' ', re.split ('"', self.line)[2].lstrip())[1]

                self.term.addSynonymType (synType)

            # Save the subset value
            # For MCV this is the show/hide value of the term
            # For Disease Ontology, this is the DO_MGI_slim
            #
            subsetList = ['DO_MGI_slim', 'DO_GXD_slim']
            if tag == 'subset':
                if self.vocabName == 'Disease Ontology':
                    for s in subsetList:
                        if self.line.find(s) >= 0:
                            self.term.addSubset(re.split (' ', self.line)[1].strip())
                else:
                    self.term.addSubset(re.split (' ', self.line)[1])

            # Read the next line from the OBO file.
            #
            self.line = self.fpOBO.readline()

        return self.term
