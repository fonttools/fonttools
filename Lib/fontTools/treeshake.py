"""
usage: pyfttreeshake [options] inputfile

    pyfttreeshake %s -- TrueType Bytecode Treeshake Tool

    General options:
    -h Help: print this message
    -x XML: emit XML output
    -v Verbose: be more verbose
"""

from fontTools import ttLib
from fontTools.ttLib import TTFont
from fontTools.ttLib.bytecodeContainer import BytecodeContainer
from fontTools.ttLib.instructions import abstractExecute
import tempfile
import sys
import logging
import copy
import getopt

def ttDump(input):
    output = tempfile.TemporaryFile(suffix=".ttx")
    ttf = TTFont(input, 0, allowVID=False,
            ignoreDecompileErrors=True,
            fontNumber=-1)
    ttf.saveXML(output, tables= [],
                skipTables= [], splitTables=False,
                disassembleInstructions=True,
                bitmapGlyphDataFormat='raw')
    ttf.close()
    return output

def executeGlyphs(abstractExecutor, initialEnvironment, glyphs):
    called_functions = set()
    for glyph in glyphs:
        abstractExecutor.environment = copy.deepcopy(initialEnvironment)
        abstractExecutor.execute(glyph)
        called_functions.update(list(set(abstractExecutor.program.call_function_set)))
    return called_functions

def process(jobs, options):
    for job in jobs:
        font = TTFont()
        font.importXML(job, quiet=None)
        bc = BytecodeContainer(font)

        abstractExecutor = abstractExecute.Executor(bc)

        called_functions = set()
        if 'prep' in bytecodeContainer.tag_to_programs:
            abstractExecutor.execute('prep')
            called_functions.update(list(set(abstractExecutor.program.call_function_set)))
        environment = copy.deepcopy(abstractExecutor.environment)
        tables_to_execute = bc.tag_to_programs.keys()
        for table in tables_to_execute:
            try:
                abstractExecutor.execute(table)
                called_functions.update(list(set(abstractExecutor.program.call_function_set)))
                abstractExecutor.environment = copy.deepcopy(environment)
            except:
                abstractExecutor.environment = copy.deepcopy(environment)

        function_set = bc.function_table.keys()
        unused_functions = [item for item in function_set if item not in called_functions]
        bc.removeFunctions(unused_functions)
        bc.updateTTFont(font)

        outfile = "Reduced%s.xml" % job
        font.saveXML(outfile)
        font.close()

class Options(object):
    verbose = False
    outputXML = False
    def __init__(self, rawOptions, numFiles):
        for option, value in rawOptions:
            # general options
            if option == "-h":
                from fontTools import version
                print(__doc__ % version)
                sys.exit(0)
            elif option == "-v":
                self.verbose = True
            elif option == "-x":
                self.outputXML = True

        if (self.verbose):
            logging.basicConfig(level = logging.INFO)
        else:
            logging.basicConfig(level = logging.ERROR)

def usage():
    from fontTools import version
    print(__doc__ % version)
    sys.exit(2)

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "vx")
    except getopt.GetoptError:
        usage()

    if not files:
        usage()

    options = Options(rawOptions, len(files))
    jobs = []

    for input in files:
        fileformat = input.split('.')[-1]
        if fileformat == 'ttf':
            output = ttDump(input)
            output.seek(0)
            jobs.append(output)
        elif fileformat == 'ttx':
            jobs.append(input)
        else:
            raise NotImplementedError
    return jobs, options

def main(args):
    if len(args) < 1:
        print("usage: treeshake font-file")
        sys.exit(1)
    jobs, options = parseOptions(args)
    process(jobs, options)

if __name__ == '__main__':
  main(sys.argv[1:])
                          
