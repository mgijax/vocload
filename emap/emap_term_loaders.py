"""
Classes that implement loadTerms.TermLoad for EMAPA and EMAPS
"""

import sys 
import os
import db

vocloadpath = os.environ['VOCLOAD'] + '/bin'
sys.path.insert(0, vocloadpath)
vocloadpath = os.environ['VOCLOAD'] + '/lib'
sys.path.insert(0, vocloadpath)
from loadTerms import TermLoad, CREATEDBY_KEY, CDATE
import vocloadlib

###--- Constants ---###
DELETE_EMAPA = '''delete from VOC_Term_EMAPA'''
DELETE_EMAPS = '''delete from VOC_Term_EMAPS'''

BCP_INSERT_EMAPA = '''%%s|%%s|%%s|%%s|%d|%d|%s|%s\n''' % \
        (CREATEDBY_KEY, CREATEDBY_KEY, CDATE, CDATE)
        
EMAPA_BCP_FILE_NAME = os.environ['TERM_EMAPA_TS_BCP_FILE']
EMAPS_BCP_FILE_NAME = os.environ['TERM_EMAPS_TS_BCP_FILE']

###--- Classes ---###

class EMAPALoad(TermLoad):
    """
    EMAPA customization of TermLoad
    Also loads VOC_Term_EMAPA
    """
    
    def loadDataFile(self, filename):
        """
        Load EMAPA type datafile from filename
        """
        self.datafile = vocloadlib.readTabFile(filename,
            [ 'term', 'accID', 'status', 'abbreviation',
            'note', 'comment', 'synonyms', 'synonymTypes',
            'otherIDs', 'start', 'end', 'parent' 
        ])
        
    def postProcess(self):
        """
        Post process hook into TermLoad.
        Allows us to add extra VOC_Term_EMAPA table
        """
        self.loadEMAPABCP(EMAPA_BCP_FILE_NAME)
        
    def loadEMAPABCP(self, bcpFileName):
        """
        Create VOC_Term_EMAPA BCP file and load into database
        
        VOC_Term_EMAPA will be a full drop and reload,
            even though VOC_Term is incremental
            
        Note: We only load VOC_Term_EMAPA for non-obsolete terms
        """
        
        vocloadlib.nl_sqlog(DELETE_EMAPA, self.log)
    
        # Build map of EMAPA IDs to _term_keys
        #    (excluding obsoletes)
        results = db.sql('''select a.accid, a._Object_key
            from ACC_Accession a
            where a._MGIType_key = 13
            and a._LogicalDB_key = 169
            and a.preferred = 1
            and exists (select 1 from VOC_Term t where a._Object_key = t._Term_key and t.isObsolete = 0)
            ''')
    
        emapaTermDict = {}
        for r in results:
            emapaTermDict[r['accid']] = r['_Object_key']
        
        # Write the BCP file
        emapaBcpFile = open(bcpFileName, 'w')
        
        try:
            for record in self.datafile:
        
                start = record['start']
                end = record['end']
                accID = record['accID']
                defaultParent = record['parent']
                
                if accID not in emapaTermDict:
                    # skip any term IDs not in the loadable set or that may be invalid
                    continue
                
                termKey = emapaTermDict[accID]
                
                if not start:
                    # skip if we have an invalid start stage
                    continue
        
                # set _defaultparent_key
                parentKey = ''
                if defaultParent in emapaTermDict:
                    parentKey = emapaTermDict[defaultParent]
    
                emapaBcpFile.write(BCP_INSERT_EMAPA % (termKey, parentKey, start, end))
                
        finally: 
            emapaBcpFile.close()
            
        # load BCP into database
        db.bcp(bcpFileName, 'VOC_Term_EMAPA', delimiter='|')
    
class EMAPSLoad(TermLoad):
    """
    EMAPS customization of TermLoad
    Also loads VOC_Term_EMAPS
    """
    
    def loadDataFile(self, filename):
        """
        Load EMAPS type datafile from filename
        """
        
        self.datafile = vocloadlib.readTabFile(filename,
            [ 'term', 'accID', 'status', 'abbreviation',
            'note', 'comment', 'synonyms', 'synonymTypes',
            'otherIDs', 'emapa', 'ts', 'parent']
        )
        
    def postProcess(self):
        """
        Post process hook into TermLoad.
        Allows us to add extra VOC_Term_EMAPS table
        """
        self.loadEMAPSBCP(EMAPS_BCP_FILE_NAME)
        
    def loadEMAPSBCP(self, bcpFileName):
        """
        Create VOC_Term_EMAPS BCP file and load into database
        
        VOC_Term_EMAPS will be a full drop and reload,
            even though VOC_Term is incremental
            
        Note: We only load VOC_Term_EMAPS for non-obsolete terms
        """
        
        vocloadlib.nl_sqlog(DELETE_EMAPS, self.log)
    
        # Build map of EMAPA and EMAPS IDs to _term_keys
        #    (excluding obsoletes)
        results = db.sql('''select a.accid, a._Object_key
            from ACC_Accession a
            where a._MGIType_key = 13
            and a._LogicalDB_key in(169, 170)
            and a.preferred = 1
            and exists (select 1 from VOC_Term t where a._Object_key = t._Term_key and t.isObsolete = 0)
        ''')

        emapTermDict = {}
        for r in results:
            emapTermDict[r['accid']] = r['_Object_key']
    
        # Write the BCP file
        emapsBcpFile = open(bcpFileName, 'w')
        
        try:
            for record in self.datafile:
        
                stage = record['ts']
                accID = record['accID']
                defaultParent = record['parent']
                emapaID = record['emapa']
                
                if accID not in emapTermDict:
                    # skip any term IDs not in the loadable set or that may be invalid
                    continue
                
                termKey = emapTermDict[accID]
                
                if emapaID not in emapTermDict:
                    # skip any emapa IDs not in the loadable set or that may be invalid
                    continue
                
                emapaKey = emapTermDict[emapaID]
                
                if not stage:
                    # skip if we have an invalid theiler stage
                    continue
        
                # set _defaultparent_key
                parentKey = ''
                if defaultParent in emapTermDict:
                    parentKey = emapTermDict[defaultParent]
    
                emapsBcpFile.write(BCP_INSERT_EMAPA % (termKey, stage, parentKey, emapaKey))
                
        finally: 
            emapsBcpFile.close()
                
        # load BCP into database
        db.bcp(bcpFileName, 'VOC_Term_EMAPS', delimiter='|')

