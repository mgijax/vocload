
import sys
import os

# in vocload/bin
import loadWrapper

# in vocload/lib
vocloadpath = os.environ['VOCLOAD'] + '/lib'
sys.path.insert(0, vocloadpath)
import vocloadlib

class OMIM_Wrapper (loadWrapper.LoadWrapper):
        def preProcess (self):
                datafile = vocloadlib.readTabFile (self.inputFile,
                        [ 'accID', 'term' ])

                self.loadfile = self.config.getConstant('TERM_FILE')
                fp = open (self.loadfile, 'w')

                for row in datafile:
                        fp.write (loadWrapper.TERM_LINE % (
                                row['term'],
                                row['accID'],
                                'current',
                                '',			# abbreviation
                                '',			# definition
                                '',			# synonyms
                                ''			# secondary IDs
                                ))
                fp.close()
                return

        def postProcess (self):
                os.remove (self.loadfile)
                return

        def setID (self):
                self.name = "OMIM"
                return

if __name__ == '__main__':
        wrapper = OMIM_Wrapper (sys.argv[1:])
        wrapper.go()

        db.commit()
