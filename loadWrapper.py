
import sys		# standard Python libraries
import getopt

import Log		# MGI-written Python libraries
import rcdlib
import vocloadlib
import loadVOC

###--- Global Constants ---###

# format for writing tab-delimited files for loading terms and a DAG:
TERM_LINE = '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'
DAG_LINE = '%s\t%s\t%s\t%s\n'

###--- Classes ---###

class LoadWrapper:

        ###--- class variables:  (shared by instances of this class) ---###

        USAGE = '''Usage: %s [-f|-i][-l <file>] <RcdFile> <input file>
        -f | -i	: full load or incremental load? (default is full)
        -n	: use no-load option (log changes, but don't execute them)
        -l	: name of the log file to create (default is stderr only)
        RcdFile	: name of the RcdFile-formatted configuration file to read
        input file : the data file to load
''' % sys.argv[0]

        NUM_ARGS = 2

        ###--- methods ---###

        def __init__ (self,
                parms
                ):
                self.config = None
                self.mode = 'full'
                self.log = None
                self.name = None
                self.inputFile = None

                self.parseParameters(parms)
                self.setID()
                return

        def parseParameters (self,
                parms
                ):
                try:
                        options, args = getopt.getopt (parms, 'finl:')
                except getopt.error:
                        print('Error: Unknown command-line options/args')
                        print(self.USAGE)
                        sys.exit(1)

                if len(args) != self.NUM_ARGS:
                        print('Error: Wrong number of parameters')
                        print(self.USAGE)
                        sys.exit(1)

                if len(args) > 1:
                        self.inputFile = args[1]

                self.config = rcdlib.RcdFile (args[0], rcdlib.Rcd, 'NAME')

                noload = 0
                for (option, value) in options:
                        if option == '-f':
                                self.mode = 'full'
                        elif option == '-i':
                                self.mode = 'incremental'
                        elif option == '-n':
                                vocloadlib.setNoload()
                                noload = 1
                        elif option == '-l':
                                self.log = Log.Log (filename = value)
                        else:
                                pass

                if not self.log:
                        self.log = Log.Log()

                if noload:
                        self.log.writeline ('Operating in NO-LOAD mode')
                return

        def setID (self):
                self.name = 'Unnamed'
                return

        def go (self):
                self.log.writeline ('Beginning %s load' % self.name)
                self.log.writeline ('*' * 70)

                self.preProcess()

                vocload = loadVOC.VOCLoad (self.config, self.mode, self.log)
                vocload.go()

                self.postProcess()

                self.log.writeline ('*' * 70)
                self.log.writeline ('Finished %s load' % self.name)
                self.log.close()
                return

        def preProcess (self):
                return

        def postProcess (self):
                return

if __name__ == '__main__':
        print("not runnable from the command-line")

#	wrapper = LoadWrapper (sys.argv[1:])
#	wrapper.go()
