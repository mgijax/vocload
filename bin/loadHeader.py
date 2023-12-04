#
#  loadHeader.py
###########################################################################
#
#  Purpose:
#
#	Loads a header file into database
#
#  Usage:
#
#      loadHeader.py
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:  None
#
#  Outputs:
#
#      - Log file (${FULL_LOG_FILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  03/17/2005  DBM  Initial development
#
###########################################################################

import sys 
import os
import db
vocloadpath = os.environ['VOCLOAD'] + '/lib'
sys.path.insert(0, vocloadpath)
import vocloadlib

#db.setTrace()

# init database connection
server = os.environ['DBSERVER']
database = os.environ['DBNAME']
username = os.environ['DBUSER']
passwordFileName = os.environ['DBPASSWORDFILE']
fp = open(passwordFileName, 'r')
password = str.strip(fp.readline())
fp.close()
vocloadlib.setupSql (server, database, username, password)

# get vocabName, mgiTypeKey
vocabName = os.environ['VOCAB_NAME']

# load header file into memory in format  ID
headerFile = sys.argv[1]
headerAnnotTypeKey = sys.argv[2]

print('loading header file %s' % headerFile)
headerRecords = set([])
fp = open(headerFile, 'r')
for line in fp.readlines():
        line = line.strip()
        if line:
                headerRecords.add(line)
fp.close()

headerIDs = list(headerRecords)
vocabKey = vocloadlib.getVocabKey(vocabName)

#
#  Get the DAG key for the current vocabulary.
#
results = db.sql('''select _DAG_key from VOC_VocabDAG vd where vd._Vocab_key = %s ''' % vocabKey)
dagKey = results[0]['_dag_key']

#
#  Get the label key for a "Header" label.
#
results = db.sql('''select _label_key from DAG_Label where label = 'Header' ''')
labelKey = results[0]['_label_key']

print('Vocab key: %d' % vocabKey)
print('DAG key: %d' % dagKey)
print('Label key: %d' % labelKey)

#
#  Find all the DAG nodes for the accession IDs in the VOC_Header table and save them in a temp table.
#
db.sql('''
        select n._Node_key 
        into temp Nodes 
        from ACC_Accession a, VOC_Term t, DAG_Node n 
        where a._MGIType_key = 13
                and a.accID in ('%s')
                and a._Object_key = t._Term_key
                and t._Vocab_key = %s
                and t._Term_key = n._Object_key
                and n._DAG_key = %s
        ''' % ('\',\''.join(headerIDs), str(vocabKey), str(dagKey)))

db.sql('create index idx1 on Nodes(_Node_key)')

#
#  Update the label key for each of the identified nodes using the label key for a header label.
#
db.sql('''
        update DAG_Node 
            set _Label_key = %s
            from Nodes t 
            where DAG_Node._Node_key = t._Node_key
        ''' % (str(labelKey)))

db.sql('''
        update DAG_Closure 
            set _AncestorLabel_key = %s
            from Nodes t 
            where DAG_Closure._Ancestor_key = t._Node_key
        ''' % (str(labelKey)))

db.sql('''
        update DAG_Closure 
            set _DescendentLabel_key = %s
            from  Nodes t 
            where DAG_Closure._Descendent_key = t._Node_key
        ''' % (str(labelKey)))

results = db.sql('select count(*) as cnt from Nodes')
print('Number of header nodes identified: %d' % results[0]['cnt'])

print('Running VOC_processAnnotHeaderAll(' + str(headerAnnotTypeKey) + ')')
db.sql('''select * from VOC_processAnnotHeaderAll(%s);''' % (headerAnnotTypeKey))
db.commit()

sys.exit(0)
