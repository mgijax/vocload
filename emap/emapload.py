#
#  emapload.py
###########################################################################
#
#  Purpose:
#
#      This script will perform sanity checks on emapload data.
#	If no sanity errors and LIVE_RUN=1, load the data
#
#  Env Vars:
#
#      The following environment variable is set by the wrapper script:
#
#          LIVE_RUN
#
#      If LIVE_RUN=0, just do sanity checks
#      If LIVE_RUN=1, do sanity checks and if no errors, load the data
#
#  Inputs:
#
#	EMAPA.obo
#
#  Outputs:
#
#      - Fatal QC report (${QC_RPT})
#      - Warning QC report (${QC_WARN_RPT})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:
#	If there are sanity errors, the term and dag files created are not valid
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Perform initialization steps.
#      3) Open the input/output files.
#      4) Generate the sanity reports.
#      5) Close the input/output files.
#
#  History
#
#  04/19/2017	sc
#	- TR12461 bug reporting multiple emaps root terms
#	  changed this:
#	    if len(aRootTermList) > 1 or len(sRootTermList) > 1:
#	  to this:
#	    if len(aRootTermList) > 1 or len(sRootTermList) > 0:
#	  because the actual 28 emaps Root terms are not in sRootTermList
#
#	  This was an edge case bug that only happened when there was ONE 
#	  extra EMAPS root term (parentless term - this happens when a child
#	  EMAPA term is outside the TS range of ALL of its parents range
# 	  e.g. child TS26-28 with one parent and  parent range is TS27-28
#
#  02/22/2016	lec
#	- TR12223/gxd anatomy II
#	- see ../loadTerms.py history
#	- added Annotation tests (annotDiscrepancyList, annotEMAPIDSet, annotDict)
#	- added 'mode' ro runTermLoad()
#
###########################################################################

import sys 
import os
import Set 
import db

vocloadpath = os.environ['VOCLOAD'] + '/lib'
sys.path.insert(0, vocloadpath)
import Ontology
import loadDAG
import Log 

from emap_term_loaders import EMAPALoad, EMAPSLoad

#
#  CONSTANTS
#
debug = 0

TAB = '\t'
CRT = '\n'
STATUS = 'current'
OBSTATUS = 'obsolete'
SYNTYPE = 'EXACT'
USAGE = 'emapload.py'

# valid Theiler Stages
TSSTART = int(os.environ['TS_START'])
TSEND = int(os.environ['TS_END'])

#
#  GLOBALS
#
# QC globals
liveRun = os.environ['LIVE_RUN']
qcRptFile = os.environ['QC_RPT']
qcWarnFile = os.environ['QC_WARN_RPT']
errorCount = 0

# input files
oboFile = os.environ['INPUT_FILE_DEFAULT']

# dup ids in the input
dupFile = os.environ['DUP_IDS_RPT']

# duplicate EMAPA IDs, created by the sanity checker	
dupEMAPAIDList = []

# invalid TS in the input file, created by the sanity checker
invalidTSFile = os.environ['INVALID_TS_RPT']

# missing fields in obo stanzas file, created by the sanity checker
missingFieldsFile = os.environ['MISSING_FIELD_RPT']

# missing EMAPA IDs or terms
missingNameIdList = []

# invalid EMAPA ids in the input file, created by the sanity checker
invalidIdFile = os.environ['INVALID_ID_RPT']

# EMAPA IDs in the db and not in the input file, created by the sanity checker
inDbNotInInputFile = os.environ['TERM_IN_DB_NOTIN_INPUT_RPT']

# created by initial sanity checker to indicate when an obo file does not have 
# a configured min number of terms
minTermsFile = os.environ['MIN_TERMS_RPT']

# undefined parent ids in the input file, created by the sanity checker
undefinedParentFile = os.environ['UNDEFINED_PARENT_RPT']

# alt_ids that are also primary ids
altIsPrimaryFile = os.environ['ALT_IS_PRIMARY_RPT']

# obsolete ids that are parent ids
obsIsParentFile = os.environ['OBS_IS_PARENT_RPT']

# obsolete ids that  have relationships
obsWithRelationshipFile = os.environ['OBS_WITH_RELATIONSHIP_RPT']

# EMAPA ids with stanza lines containing tabs 
stanzaHasTabFile = os.environ['STANZA_HAS_TAB_RPT']

# database keys
emapaVocabKey = os.environ['EMAPA_VOCAB_KEY']
emapsVocabKey = os.environ['EMAPS_VOCAB_KEY']
refsKey = int(os.environ['REFS_KEY'])

# emapa output files
emapaTermFile = os.environ['EMAPA_TERM_FILE']
emapaDagFile = os.environ['EMAPA_DAG_FILE']

# emaps output files
emapsTermFile = os.environ['EMAPS_TERM_FILE']
emapsDagFile = os.environ['EMAPS_DAG_FILE']

log = Log.Log(0, os.environ['LOG_EMAP_TERMDAG'])

passwordFileName = os.environ['PG_DBPASSWORDFILE']

class EmapTerm(Ontology.OboTerm):
     # IS: an OboTerm
     # HAS: methods to return synonyms and alt IDs
     # DOES: gets Synonyms and altIDs from an obo file
    def __init__(self, id, name, ontol):
        super(EmapTerm, self).__init__(id, name, ontol)

    def getSynonyms(self):
        synonyms = getattr(self, 'synonym', [])
        # looks like:
        # ['"oogonia" RELATED []', '"premeiotic germ cell" RELATED []']
        synList = []
        for s in synonyms:
            synList.append(s.split('"')[1])
        return synList

    def getAltIDs(self):
        altIDs = getattr(self, 'alt_id', [])
        return altIDs

def checkArgs():
    # Purpose: Validate the arguments to the script.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: exits if args found on the command line
    # Throws: Nothing

    if len(sys.argv) != 1:
        print(USAGE)
        sys.exit(1)

    return

# end checkArgs() -------------------------------

def openOutputFiles():
    # Purpose: Open the files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables, exits if a file cant be opened, 
    #  creates files in the file system

    global fpEmapaTerm, fpEmapsTerm, fpEmapaDag, fpEmapsDagDict
    global emapsDagFileDict

    fpEmapsDagDict = {}
    emapsDagFileDict = {}

    try:
        fpEmapaTerm = open(emapaTermFile, 'w')
    except:
        print('Cannot open EMAPA term file: %s' % emapaTermFile)
        sys.exit(1)

    try:
        fpEmapsTerm = open(emapsTermFile, 'w')
    except:
        print('Cannot open EMAPS term file: %s' % emapsTermFile)
        sys.exit(1)

    try:
        fpEmapaDag = open(emapaDagFile, 'w')
    except:
        print('Cannot open EMAPA DAG file: %s' % emapaDagFile)
        sys.exit(1)

    try:
        for ts in range(1,29):
            tsFile = '%s.%s' % (emapsDagFile, ts)
            fpEmapsDagDict[ts] = globals()['fp%s' % ts] = open(tsFile, 'w')
            emapsDagFileDict[ts] = tsFile
    except:
        print('Cannot open EMAPS DAG file: %s' % tsFile)
        sys.exit(1)

    return

# end openOutputFiles() -------------------------------

def parseDupFile():
    # Purpose: Open the files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables, exits if a file cannot be opened
    # Throws: Nothing

    global dupEMAPAIDList

    try:
        fpDupFile = open(dupFile, 'r')

    except:
        print('Cannot open duplicate ID file: %s' % dupFile)
        sys.exit(1)

    for d in fpDupFile.readlines():
        dupEMAPAIDList.append(d)

    return

# end parseDupFile() -------------------------------

def getInitialSanityErrors():
    # Purpose: Writes out initial sanity errors to the report
    # Returns: Nothing
    # Assumes: fpQcRpt has been initialized
    # Effects: Sets global variables, opens its own input files, exits if 
    #  error opening files
    # Throws: Nothing

    global fpQcRpt

    retCode = 0

    parseDupFile()

    #
    # Invalid Theiler Stages
    #

    invalidTSList = []
    
    try:
        fpInvalidTS = open(invalidTSFile, 'r')
    except:
        print('Cannot open invalid TS file: %s' % invalidTSFile)
        sys.exit(1)

    for d in fpInvalidTS.readlines():
        invalidTSList.append(d)
    fpInvalidTS.close()

    #
    # missing fields in stanza
    #

    missingFieldsList = []

    try:
        fpMissingFields = open(missingFieldsFile, 'r')
    except:
        print('Cannot open missing Fields file: %s' % missingFieldsFile)
        sys.exit(1)

    for m in fpMissingFields.readlines():
         missingFieldsList.append(m)
    fpMissingFields.close()

    #
    # invalid EMAPA id format
    #

    invalidIdList = []

    try:
        fpInvalidId = open(invalidIdFile, 'r')
    except:
        print('Cannot open invalid Id file: %s' % invalidIdFile)
        sys.exit(1)

    for m in fpInvalidId.readlines():
         invalidIdList.append(m)
    fpInvalidId.close()

    #
    # if minimum number of terms in input file not present
    #

    minTermsList = []

    try:
        fpMinTerms = open(minTermsFile, 'r')
    except:
        print('Cannot open minumum terms file: %s' % minTermsFile)
        sys.exit(1)

    for t in fpMinTerms.readlines():
        minTermsList.append(t)
    fpMinTerms.close()

    #
    # Parent IDs which are not defined
    #

    undefinedParentList = []

    try:
        fpUndefinedParent = open(undefinedParentFile, 'r')
    except:
        print('Cannot open undefined parent file: %s' % undefinedParentFile)
        sys.exit(1)

    for u in fpUndefinedParent.readlines():
        undefinedParentList .append(u)
    fpUndefinedParent.close()

    #
    # alt_ids which are also primary ids
    #

    altIsPrimaryList = []

    try:
        fpAltIdPrimary = open(altIsPrimaryFile, 'r')
    except:
        print('Cannot open alt ids also defined as primary file: %s' % altIsPrimaryFile)
        sys.exit(1)

    for a in fpAltIdPrimary.readlines():
        altIsPrimaryList.append(a)
    fpAltIdPrimary.close()

    #
    # obsolete ids which are parents
    #

    obsIsParentList = []

    try:
        fpObsIsParent = open(obsIsParentFile, 'r')
    except:
        print('Cannot open obsolete ids that are parents file: %s' % obsIsParentFile)

    for o in fpObsIsParent.readlines():
        obsIsParentList.append(o)
    fpObsIsParent.close()

    #
    # obsolete ids which have relationships
    #

    obsWithRelationshipList = []

    try:
        fpObsWithRelationship = open(obsWithRelationshipFile, 'r')
    except:
        print('Cannot open obsolete ids with relationships file: %s' % obsWithRelationshipFile)

    for o in fpObsWithRelationship.readlines():
        obsWithRelationshipList.append(o)
    fpObsWithRelationship.close()

    #
    # Ids with lines containing tabs
    #

    stanzaHasTabList = []

    try:
        fpStanzaHasTab = open(stanzaHasTabFile, 'r')
    except:
        print('Cannot open Stanzas with tab file: %s' % stanzaHasTabFile)

    for i in fpStanzaHasTab.readlines():
        stanzaHasTabList.append(i)
    fpStanzaHasTab.close()

    #
    # Now determine and report all sanity errors
    #

    if len(invalidTSList) or len(missingFieldsList) or len(invalidIdList) \
      or len(minTermsList) or len(undefinedParentList) \
      or len(altIsPrimaryList) or len(obsIsParentList) \
      or len(obsWithRelationshipList) or len(stanzaHasTabList):

        retCode = 2

        openQCFiles()

        fpQcRpt.write('You must fix all errors in this report and run the QC script again%s' % CRT)
        fpQcRpt.write('to find any additional errors %s%s' % (CRT, CRT))

        if len(invalidTSList):
            fpQcRpt.write('EMAPA IDs with invalid Theiler stages: %s%s' % (CRT, CRT))
            for ts in invalidTSList:
                fpQcRpt.write('%s' % (ts))
            fpQcRpt.write(CRT)

        if len(missingFieldsList):
            for msg in missingFieldsList:
                fpQcRpt.write('%s' % (msg))
            fpQcRpt.write(CRT)

        if len(invalidIdList):
            fpQcRpt.write('Invalid EMAPA IDs: %s%s' % (CRT, CRT))
            for id in invalidIdList:
                fpQcRpt.write('%s' % (id))
            fpQcRpt.write(CRT)
            
        if len(minTermsList):
            for msg in minTermsList:
                fpQcRpt.write('%s' % (msg))
            fpQcRpt.write(CRT)

        if len(undefinedParentList):
            fpQcRpt.write('Undefined parent IDs: %s%s' % (CRT, CRT))
            for id in undefinedParentList:
                 fpQcRpt.write('%s' % (id))
            fpQcRpt.write(CRT)

        if len(altIsPrimaryList):
            fpQcRpt.write('Alt_ids that are also primary:  %s%s' % (CRT, CRT))
            for id in altIsPrimaryList:
                fpQcRpt.write('%s' % (id))
            fpQcRpt.write(CRT)

        if len(obsIsParentList):
            fpQcRpt.write('Obsolete Ids that are also parents: %s%s' % (CRT, CRT))
            for id in obsIsParentList:
                fpQcRpt.write('%s' % (id))
            fpQcRpt.write(CRT)

        if len(obsWithRelationshipList):
            fpQcRpt.write('Obsolete Ids that have parent or TS relationships: %s%s' % (CRT, CRT))
            for id in obsWithRelationshipList:
                fpQcRpt.write('%s' % (id))
            fpQcRpt.write(CRT)

        if len(stanzaHasTabList):
            fpQcRpt.write('Stanzas with embedded tabs: %s%s' % (CRT, CRT))
            for line in stanzaHasTabList:
                fpQcRpt.write('%s' % (line)) 

    if retCode != 0:
        closeQCFiles()
        sys.exit(retCode)

    return

# end getInitialSanityErrors() -------------------------------

def closeOutputFiles():
    # Purpose: Close all file descriptors
    # Returns: Nothing
    # Assumes: all file descriptors were initialized
    # Effects: Nothing
    # Throws: Nothing

    global fpEmapaTerm, fpEmapaDag
    
    fpEmapaTerm.close()
    fpEmapsTerm.close()
    fpEmapaDag.close()
    for ts in list(fpEmapsDagDict.keys()):
        fpEmapsDagDict[ts].close()

    return

# end closeOutputFiles() -------------------------------

def openQCFiles():
    # Purpose: Open the QC  file
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Sets global variables. Creates file in the filesystem
    # Throws: Nothing

    global fpQcRpt

    try:
        fpQcRpt = open(qcRptFile, 'w')
    except:
        print('Cannot open qc report file: %s' % qcRptFile)
        sys.exit(1)

    return

# end openQCFiles() -------------------------------

def closeQCFiles():
    # Purpose: Close the files.
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    global fpQcRpt
    
    fpQcRpt.close()

    return

# end  closeQCFiles() -------------------------------

def termCleanup(t,	# a term object (OboTerm)
                stanza	# dict whose keys are the stanza keywords,
                        #      & values are the text after the keyword
                ):
    # Purpose: Call back function that morphs starts_at/ends_at relationships
    #       into attributes
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing

    setattr(t, "starts_at", [])
    setattr(t, "ends_at", [])
    # check for starts_at and ends_at relationships
    for r in stanza.get("relationship", []): 
        (reltype, relid) = r.split()
        ts = relid[2:].replace(':','')

        if reltype == "starts_at":
            #setattr(t, "starts_at", int(relid[2:]))
            t.starts_at.append(int(ts))
        if reltype == "ends_at":
            #setattr(t, "ends_at", int(relid[2:]))	
            t.ends_at.append(int(ts))
    return

# end termCleanup() -------------------------------

def createFiles(): 
    # Purpose: parses an obo file and creates EMAPA/EMAPS term and dag files
    #  Does sanity checking
    # Returns: Nothing
    # Assumes: file descriptors have been initialized
    # Effects: sets global variables, writes to the file system
    # Throws: Nothing

    global errorCount, aRootTermList, sRootTermList, noOverlapList
    global tsDiscrepancyList, cyclesList, seenEMAPIDSet
    global annotDiscrepancyList, annotEMAPIDSet, annotDict
    global allEMAPIDs, debug
 
    # list of EMAPA root nodes, if > 1 will report
    aRootTermList = []
  
    # list of EMAPA cycles, if any will report
    cyclesList = []
 
    # list of EMAPS root nodes, if > 1 will report
    sRootTermList = []
 
    # list of terms whose TS range does not overlap one or more of its
    # parents' for reporting
    noOverlapList = []

    # list of terms with TS discrepancies, for reporting
    tsDiscrepancyList = []

    # list of terms with Annotation discrepancies, for reporting
    annotDiscrepancyList = []

    # EMAPA IDs we've seen so far
    seenEMAPIDSet = set([])

    # EMAPA IDs in annotations
    annotEMAPIDSet = set([])

    # EMAPA IDs in annotations w/ min/max stage
    annotDict = {}

    # all EMAPA IDs - both preferred and non-preferred
    allEMAPIDs = {}

    # consider only terms from this namespace
    ns = 'anatomical_structure'

    # 'ont' is instance of Ontology.OboOntology
    ont = Ontology.load(oboFile, cullObsolete=False, cullCrossEdges=True, termCallBack=termCleanup, nodeType=EmapTerm)

    #
    # remove root node EMAPA:0
    #
    ont.removeTerm(ont.getTerm('EMAPA:0'))

    # now check for single root
    roots = ont.getRoots( ns=ns)
    if len(roots) > 1:
        for et in roots:
            aRootTermList.append(et.id)
            errorCount += 1

    #
    # check for cycles 
    #
    cycleNodes = ont.checkCycles()
    if len(cycleNodes) > 0:
        errorCount +=1
        for t in cycleNodes:
            cyclesList.append('%s %s' % (t.id, t.name))

    # 
    # create dictionary of EMAPA terms (both preferred & non-preferred)
    # will be used to check for merges
    #
    results = db.sql('''
        select distinct accid, _object_key 
        from ACC_Accession
        where _mgitype_key = 13
        and _logicaldb_key = 169
        ''', 'auto')
    for r in results:
        key = r['accid']
        value = r['_object_key']
        allEMAPIDs[key] = value

    #
    # create dictionary of existing annotations : emapa id
    #
    results = db.sql('''
                (
                select distinct a.accid
                from GXD_GelLaneStructure s, ACC_Accession a
                where s._emapa_term_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                union all
                select distinct a.accid
                from GXD_ISResultStructure s, ACC_Accession a
                where s._emapa_term_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                union all
                select distinct a.accid
                from GXD_HTSample s, ACC_Accession a
                where s._emapa_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                )
                ''', 'auto')
    for r in results:
        key = r['accid']
        annotEMAPIDSet.add(key)

    #
    # create dictionary of existing annotations : emapa id, min-stage, max-stage
    #
    results = db.sql('''
                (
                select distinct a.accid, min(ts.stage) as minStage, max(ts.stage) as maxStage
                from GXD_GelLaneStructure s, GXD_TheilerStage ts, ACC_Accession a
                where s._emapa_term_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                and s._stage_key = ts._stage_key
                group by a.accid
                union all
                select distinct a.accid, min(ts.stage) as minStage, max(ts.stage) as maxStage
                from GXD_ISResultStructure s, GXD_TheilerStage ts, ACC_Accession a
                where s._emapa_term_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                and s._stage_key = ts._stage_key
                group by a.accid
                union all
                select distinct a.accid, min(ts.stage) as minStage, max(ts.stage) as maxStage
                from GXD_HTSample s, GXD_TheilerStage ts, ACC_Accession a
                where s._emapa_key = a._object_key
                and a._mgitype_key = 13
                and a._logicaldb_key = 169
                and a.preferred = 1
                and s._stage_key = ts._stage_key
                group by a.accid
                )
                ''', 'auto')
    for r in results:
        key = r['accid']
        annotDict[key] = r

    #
    # build EMAPA/EMAPS term and dag files, checking for errors as we go
    #
    # t is instance of EmapTerm which extends Ontology.OBOTerm
    for t in ont.iterNodes():	# iterate through the nodes 
        # only consider anatomical_structure namespace
        if t.namespace != ns:
            continue

        # determine if root node, we'll use this more than once
        isRoot = 0
        if ont.isRoot(t):
            isRoot = 1

        # get the term and its ID
        term = t.name
        emapaId = t.id

        # 'endochronal bone' 'EMAPA:35304 child of 'bone tissue' EMAPA:35179
        #if emapaId == 'EMAPA:35304':
        #    debug = 1
        #    print 'Debugging: %s %s' % (emapaId, term)
        #    print 'Starts at: %s Ends at: %s' % (t.starts_at, t.ends_at)
        
        if term == '' or emapaId == '':
            missingNameIdList.append('id: "%s", name: "%s" has blank attribute' % (emapaId, term))
            errorCount += 1

        # for now...continue on...even if term/emapaId is missing...?

        # add to seenEMAPIDSet...
        seenEMAPIDSet.add(emapaId)

        #
        # for obsolete terms...
        #
        if t.is_obsolete:

            # if annotations exist, then error
            if emapaId in annotDict:
                annotDiscrepancyList.append('annotation exists for obsolete term: %s' % (emapaId))
                errorCount += 1

            fpEmapaTerm.write('%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % \
                (term, TAB, emapaId, TAB, OBSTATUS, TAB, TAB, TAB, TAB, \
                 TAB, TAB, TAB, TAB, TAB, CRT))

            continue
                 
        # get the theiler stage start and end values
        # for terms that don't have start/end
        # QC catches terms missing one or the other or multi

        if t.starts_at == [] and t.ends_at == []:
            start = TSSTART
            end = TSEND
        elif t.starts_at == []:
            tsDiscrepancyList.append('%s has missing starts_at' % t.id )
            errorCount += 1
        elif t.ends_at == []:
            tsDiscrepancyList.append('%s has missing ends_at' % t.id )
            errorCount += 1
        elif len(t.starts_at) > 1 and len(t.ends_at) > 1:
            tsDiscrepancyList.append('%s has multiple starts_at AND ends_at values' % t.id)
            errorCount += 1
            continue
        elif len(t.starts_at) > 1:
            tsDiscrepancyList.append('%s has multiple starts_at values' % t.id)
            errorCount += 1
            continue
        elif len(t.ends_at) > 1 :
            tsDiscrepancyList.append('%s has multiple ends_at values' % t.id)
            errorCount += 1
            continue	
        else:
            start = t.starts_at[0]
            end = t.ends_at[0]
            # check that start < end
            if end < start:
                tsDiscrepancyList.append('%s ends_at < starts_at' % t.id)
                errorCount += 1
                continue
            # check  for valid TS value
            if start not in list(range(TSSTART, TSEND + 1)):
                tsDiscrepancyList.append('Invalid starts_at value %s for %s' % (start, t.id))
                errorCount += 1
            if end not in list(range(TSSTART, TSEND + 1)):
                tsDiscrepancyList.append('Invalid ends_at value %s for %s' % (start, t.id))
                errorCount += 1
        
        #
        # if annotation exist and start/end stage conflicts, then error
        # 	annotation/minStage is less than the new start stage
        # 	annotation/maxStage is greater than the new end stage
        #
        if emapaId in annotDict:
            if annotDict[emapaId]['minStage'] < start:
               annotDiscrepancyList.append('start stage conflict: %s, %s (in mgi), %s (in obo)' \
                   % (emapaId, annotDict[emapaId]['minStage'], start))
               errorCount += 1
            if annotDict[emapaId]['maxStage'] > end:
               annotDiscrepancyList.append('end stage conflict: %s, %s (in mgi), %s (in obo)' \
                   % (emapaId, annotDict[emapaId]['maxStage'], end))
               errorCount += 1

        # get the term's alternate ids joining with '|'
        altIdList = t.getAltIDs()
        altIds = str.join('|', altIdList)

        # if altID term object != emapaID term object, then this is a merge, report error
        if emapaId in allEMAPIDs:
            for a in altIdList:
                if a in allEMAPIDs:
                    if allEMAPIDs[emapaId] != allEMAPIDs[a] and a in annotDict:
                        message = 'term merge detected and annotations exist for alt_id: %s, alt_id = %s'
                        annotDiscrepancyList.append(message % (emapaId, a))
                        errorCount += 1

        # get the term's synonyms joining with '|'
        synList = t.getSynonyms()
        syns = str.join('|', synList)
        synTypeList = []

        # create synonym type string
        for s in range(0, len(synList)):
            synTypeList.append(SYNTYPE)
        synType = str.join('|', synTypeList)

        # create a list of the current term's TSs
        cTSList = []
        for i in range(start, end + 1):
            cTSList.append(i)

        # get parent's end edges of 't'
        parentDict = {}
        for parent, edge in ont.iterInEdges(t):
                parentDict[parent] = edge
        #
        # Determine parent overlap
        #

        # get list of parents for term, for sorting`
        # [pName|pid, ...]
        parentList = []
        
        # parents whose TS overlaps with 't'
        # {ts:[pid1, ...], ...}
        parentOverlapTSDict = {}

        # root term has no parents - add all ts to the dictionary
        #pList = ont.getParents(t)
        pList = list(parentDict.keys())

        if len(pList) == 0:
            for i in range(1, 29):
                parentOverlapTSDict[i] = ['root|']

        # We want to skip this check if relationship is develops_from or attached_to
        # iterate over the parents adding to the overlap dict
        for p in pList:
            # get relationship between the node and this parent
            # we need to sort on the term, but we need the ID for the
            # defaultParent
            
            parentList.append('%s|%s' % (p.name, p.id))

            # create a set of parent TS values to determine TS overlap
            # Here we assume QC of starts_at/ends_at will fail for p 
            # above if len > 1, so we grab the first one in the list
            #
            # we also assume that missing starts_at/ends_at will be
            # caught for p in earlier check
            pTSSet = set([])
            if p.starts_at == []:
                pStart = TSSTART
            else:
                pStart = p.starts_at[0]

            if p.ends_at == []:
                pEnd = TSEND
            else:
                pEnd = p.ends_at[0]
            for j in range(pStart, pEnd + 1):
                pTSSet.add(j)

            # check for child/parent TS overlap
            hasOverlap = False
            if parentDict[p] == 'develops_from' or parentDict[p] == 'attached_to':
                hasOverlap = True # skip this QC check, child with develops_from relationship will NOT
                                  # overlap parent
            else:
                for ts in cTSList:
                    # all it takes is one overlap to be valid
                    if ts in pTSSet:
                        hasOverlap = True
                        pid = '%s|%s' %(p.name, p.id)
                        if ts not in parentOverlapTSDict:
                            parentOverlapTSDict[ts] = []
                        if pid  not in  parentOverlapTSDict[ts]:
                            parentOverlapTSDict[ts].append(pid)
                    
            # If hasOverlap is false we have no overlap
            if hasOverlap == False:
                errorCount += 1
                noOverlapList.append('%s range %s-%s not in parent %s range %s-%s' % (t.id, start, end, p.id, pStart, pEnd  ) )

        #
        # determine default parent, lowest alpha
        # default value empty - this is a root
        #
        defaultParent = ''

        # if we hava one or more parents, find the default parent
        if (len(parentList)) > 0:
            # we sort to find defaultParent (alpha order),even if only one
            parentList.sort()
            
            # Get the first sorted ID 
            defaultParent = parentList[0].split('|')[1]
        
        # write out to the emapa term file
        fpEmapaTerm.write('%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % \
            (term, TAB, emapaId, TAB, STATUS, TAB, TAB, TAB, TAB, \
                syns, TAB, synType, TAB, altIds, TAB, start, TAB, end, TAB, defaultParent, CRT))
    
        #
        # get the parent edges, parent is an EMAPTerm object
        # edgeLabel is a string
        #
        
        # root term has no edges
        if isRoot:
            edge = ''
            pid = ''
            fpEmapaDag.write('%s%s%s%s%s%s%s' % (emapaId, TAB, TAB, edge, TAB, pid, CRT))

        # if edges, translate to proper edge term, write out to emapa dag 
        # file and save for later use determining emaps
 
        parentEdgeDict = {}
        for (parent, edgeLabel) in ont.iterInEdges(t):
            # part_of -> part-of, is_a -> is-a
            edge = edgeLabel.replace('_', '-')
            
            # get id from parent object
            pid = parent.id

            # save edges for use by EMAPS calculation
            if pid not in parentEdgeDict:
                parentEdgeDict[pid] = []
            parentEdgeDict[pid].append(edge)

            # write out to the dag file
            fpEmapaDag.write('%s%s%s%s%s%s%s' % (emapaId, TAB, TAB, edge, TAB, pid, CRT))
        
        # 
        # determine EMAPS terms and
        # write out to the emaps term file
        #

        # create EMAPS term for each TS stage 
        if debug:
            print('Start of creating EMAPS term')

        for ts in cTSList:
            # we need the leading zero for the id 
            if int(ts) < 10:
                tsString = '0%s' % ts
            else:
                tsString = '%s' % ts    
            if debug:
                print('ts: %s' % ts)

            # the term is the same as the emapa term
            sTerm = term  

            # Calculate the emaps ID
            # EMAPA:123456 at TS01 -> EMAPS:12345601
            emapsId = '%s%s' % (emapaId.replace('A:', 'S:'), tsString)
            if debug:
                print('emapsId: %s' % emapsId)

            pidList = []
            if ts in parentOverlapTSDict:
                if debug:
                    print('parentOverlapTSDict[ts]: %s' %  parentOverlapTSDict[ts])
                pidList = parentOverlapTSDict[ts]
            else:
                # parentless terms are root terms, save for multi-root detection
                sRootTermList.append(emapsId)
                if debug:
                    print('adding to sRootTermList: %s' % sRootTermList)

                continue
            # Calculate the emaps default parent ID
            # null if its the root 
            if isRoot:
                defaultEmapsParent = defaultParent # empty string
            else:
                pidList.sort()
                dep = pidList[0].split('|')[1]
                defaultEmapsParent = '%s%s' % (dep.replace('A:', 'S:'), tsString)

            # write to emaps term file; status, synonyms, synType same as EMAPA
            if debug:
                print('writing to emapsTerm file: %s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % \
                (sTerm, TAB, emapsId, TAB, STATUS, TAB, TAB, TAB, TAB, syns, \
                TAB, synType, TAB, TAB, emapaId, TAB, ts, TAB, defaultEmapsParent, CRT))

            # write to emaps term file; status, synonyms, synType same as EMAPA
            fpEmapsTerm.write('%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s' % \
                (sTerm, TAB, emapsId, TAB, STATUS, TAB, TAB, TAB, TAB, syns, \
                TAB, synType, TAB, TAB, emapaId, TAB, ts, TAB, defaultEmapsParent, CRT)) 

            # create emaps dag file for each emaps TS overlap with parent
            for p in pidList: 
                pid = p.split('|')[1]
                # if we have the root write out parentless/edgeless record
                if isRoot:
                    pEmapsId = ''
                    edge = ''
                    fpEmapsDagDict[int(ts)].write('%s%s%s%s%s%s%s' % \
                        (emapsId, TAB, TAB, edge, TAB, pEmapsId, CRT))

                # write out edge for each parent
                elif pid in list(parentEdgeDict.keys()):
                    pEmapsId = '%s%s' % (pid.replace('A:', 'S:'), tsString)
                    edges = parentEdgeDict[pid]
                    for edge in edges:
                        fpEmapsDagDict[int(ts)].write('%s%s%s%s%s%s%s' % \
                            (emapsId, TAB, TAB, edge, TAB, pEmapsId, CRT))
        if errorCount:
            continue

    #
    # end : for t in ont.iterNodes():	# iterate through the nodes 
    #

    #
    # if terms exist in annotations but are not in obo file
    #
    diff = annotEMAPIDSet - seenEMAPIDSet
    if len(diff) > 0:
        annotDiscrepancyList.append('terms exist in annotations but are not in obo file: %s' % (diff))
        errorCount += 1

    # Check if dags rooted in one term
    if len(aRootTermList) > 1 or len(sRootTermList) > 0:
        errorCount += 1

    return

# end createFiles() -------------------------------------


def runDagLoad(file, dag):
    # Purpose: Runs a DAG load
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: a DAG is loaded into a database
    # Throws: Nothing

    dagload = loadDAG.DAGLoad (file, 'full', dag, log, passwordFileName)
    dagload.go()

    return

# end  runDagLoad() -------------------------------

def writeFatalSanityReport():
    # Purpose: writes sanity errors to the sanity report if any are found
    # Returns: Nothing
    # Assumes:  file descriptor has been initialized
    # Effects: a DAG is loaded into a database,
    #       exits with return code 2 if sanity errors are found
    # Throws: Nothing

    openQCFiles()

    if len(aRootTermList) > 1:
        fpQcRpt.write('Multiple EMAPA Root Nodes: %s%s' % (CRT, CRT))
        fpQcRpt.write(str.join(aRootTermList, ', '))
        fpQcRpt.write('%s%s' % ( CRT, CRT))

    if len(cyclesList) > 0:
        fpQcRpt.write('Cycles exist between the following nodes: %s%s' % (CRT, CRT))
        fpQcRpt.write(str.join(cyclesList, CRT))
        fpQcRpt.write('%s%s' % ( CRT, CRT))

    if len(sRootTermList) > 0:
        fpQcRpt.write('Multiple EMAPS Root Nodes: %s%s' % (CRT, CRT))
        fpQcRpt.write('EMAPS roots are EMAPS:25765 (1-28) these are in addition: %s%s' % (CRT, CRT))
        for r in sRootTermList:
            fpQcRpt.write('%s%s' % (r, CRT))
        fpQcRpt.write('%s%s' % ( CRT, CRT))

    if len(noOverlapList) > 0:
        fpQcRpt.write("Child Terms that don't overlap a parent: %s%s" % (CRT, CRT))
        for line in noOverlapList:
            fpQcRpt.write('%s%s' % (line, CRT))
        fpQcRpt.write('%s' % CRT)

    if len(tsDiscrepancyList) > 0:
        fpQcRpt.write('Terms with starts_at or ends_at discrepancies: %s%s' % (CRT, CRT))
        for line in tsDiscrepancyList:
            fpQcRpt.write('%s%s' % (line, CRT))
        fpQcRpt.write('%s' % CRT)

    if len(annotDiscrepancyList) > 0:
        fpQcRpt.write('Terms with annotation discrepancies: %s%s' % (CRT, CRT))
        for line in annotDiscrepancyList:
            fpQcRpt.write('%s%s' % (line, CRT))
        fpQcRpt.write('%s' % CRT)

    if len(dupEMAPAIDList) > 0:
        fpQcRpt.write('EMAPA IDs duplicated in the input: %s%s' % (CRT, CRT))
        for line in dupEMAPAIDList:
            fpQcRpt.write('%s' % (line))
        fpQcRpt.write('%s' % CRT)

    if len(missingNameIdList) > 1:
        fpQcRpt.write('Terms with missing id and/or name: %s%s' % (CRT, CRT))
        for line in missingNameIdList:
            fpQcRpt.write('%s%s' % (line, CRT))

    closeQCFiles()

    sys.exit(2)

def writeWarningSanityReport():

    #
    # EMAPA id in database and not in input file
    #

    try:
        fpInDbNotInInput = open(inDbNotInInputFile, 'r')
    except:
        print('Cannot open invalid Id file: %s' % inDbNotInInputFile)
        sys.exit(1)

    try:
        fpWarning = open(qcWarnFile, 'w')
    except:
        print('Cannot open Warning Sanity file: %s' % qcWarnFile)
        sys.exit(1)

    lines = fpInDbNotInInput.readlines()

    if len(lines):
        print('Non-fatal errors detected. See %s%s' % (qcWarnFile, CRT))
    else:
        print('No warnings detected.')

    for line in lines:
        fpWarning.write(line)

    fpWarning.close()
    fpInDbNotInInput.close()

    return
    
# end writeFatalSanityReport() -------------------------------

def runLoads():
    # Purpose: runs all EMAPA/EMAPS term and dag loads
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: terms and DAGs are loaded into a database,
    # Throws: Nothing

    print('running EMAPA term load')
    termload = EMAPALoad (emapaTermFile, 'incremental', emapaVocabKey, refsKey, log, passwordFileName)
    termload.go()
    
    print('running EMAPA dag load')
    runDagLoad(emapaDagFile, 'EMAPA')

    print('running EMAPS term load')
    
    # reset the TermLoad environment variables
    os.environ['TERM_TERM_BCP_FILE'] = os.environ['TERM_TERM_S_BCP_FILE']
    os.environ['TERM_NOTE_BCP_FILE'] = os.environ['TERM_NOTE_S_BCP_FILE']
    os.environ['TERM_SYNONYM_BCP_FILE']  = os.environ['TERM_SYNONYM_S_BCP_FILE']
    os.environ['ACCESSION_BCP_FILE']  = os.environ['ACCESSION_S_BCP_FILE']
    os.environ['DISCREP_FILE'] = os.environ['DISCREP_S_FILE']
    
    # run the EMAPS load
    termload = EMAPSLoad (emapsTermFile, 'full', emapsVocabKey, refsKey, log, passwordFileName)
    termload.go()

    print('running EMAPS dag loads')
    for ts in list(emapsDagFileDict.keys()):
        tsFile = emapsDagFileDict[ts]

        # dynamically create discrepancy, edge, node and closure file names
        # and set them in the environment
        discrepFile = os.environ['DAG_DISCREP_S_FILE']
        os.environ['DAG_DISCREP_FILE'] = discrepFile.replace('~', '%s' % ts) 

        edgeFile = os.environ['DAG_EDGE_S_BCP_FILE']

        nodeFile =  os.environ['DAG_NODE_S_BCP_FILE']
        os.environ['DAG_NODE_BCP_FILE'] = nodeFile.replace('~', '%s' % ts)

        closureFile = os.environ['DAG_CLOSURE_S_BCP_FILE']
        os.environ['DAG_CLOSURE_BCP_FILE'] = closureFile.replace('~', '%s' % ts)

        runDagLoad(tsFile, 'EMAPS%s' % ts)

    return

# end runLoads() -------------------------------

#####################
#
# Main
#
#####################

# check the arguments to this script
checkArgs()

# this function will exit(2) if any initial sanity errors are found
getInitialSanityErrors()

# this function will exit(1) if errors opening files
openOutputFiles()

# create term and dag input files, running sanity checks as it goes
createFiles()

# close all output files
closeOutputFiles()

# write any warnings to the warning report
writeWarningSanityReport()

# if createFiles finds any sanity errors write them out
# this function will exit(2) if any sanity errors are found while creating files
if errorCount > 0:
    writeFatalSanityReport()

# if this is a live run, load the terms and dags
print('liveRun: ' + str(liveRun))
if liveRun == '1':
    # run the term and DAG loads
    print('calling runLoads')
    runLoads()
    db.commit()

sys.exit(0)
