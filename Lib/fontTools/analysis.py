"""
usage: pyftanalysis [options] inputfile

    pyftanalysis %s -- TrueType Bytecode Analysis Tool

    General options:
    -h Help: print this message
    -i IR: print out IR rather than bytecode
    -s State: print the graphics state after executing prep
    -c CallGraph: print out the call graph
    -m MaxStackDepth: print out the maximum stack depth for the executed code
    -p Prep: print out prep bytecodes/IR
    -f Functions: print out function bytecodes/IR
    -z Glyphs: print out selected glyph bytecode/IR
    -g NAME Glyph: execute prep plus hints for glyph NAME
    -G AllGlyphs: execute prep plus hints for all glyphs in font
    -r Reduce: remove uncalled functions
    --cvt CVT: print the CVT after executing prep
    -v Verbose: be more verbose
"""

from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.bytecodeContainer import BytecodeContainer
from fontTools.ttLib.instructions import statements, abstractExecute
from fontTools.ttLib.data import dataType
from fontTools.misc.util import makeOutputFileName
import sys
import os
import getopt
import math
import pdb
import logging
import copy

def ttDump(input):
    output = makeOutputFileName(input, ".ttx")
    ttf = TTFont(input, 0, verbose=False, allowVID=False,
            quiet=False, ignoreDecompileErrors=True,
            fontNumber=-1)
    ttf.saveXML(output, quiet=True, tables= [],
            skipTables= [], splitTables=False,
            disassembleInstructions=True,
            bitmapGlyphDataFormat='raw')
    ttf.close()
    return output

def executeGlyphs(absExecutor, initialEnvironment, glyphs):
    called_functions = set() 
    for glyph in glyphs:
        absExecutor.environment = copy.deepcopy(initialEnvironment)
        absExecutor.execute(glyph)
        called_functions.update(list(set(absExecutor.program.call_function_set)))
    return called_functions

def analysis(tt, glyphs):
    #one ttFont object for one ttx file       
    absExecutor = abstractExecute.Executor(tt)
    called_functions = set()
    absExecutor.execute('prep')
    called_functions.update(list(set(absExecutor.program.call_function_set)))

    environment_after_prep = copy.deepcopy(absExecutor.environment)
    called_functions.update(executeGlyphs(absExecutor, environment_after_prep, glyphs))
    return absExecutor, called_functions

class Options(object):
    verbose = False
    outputState = False
    outputCVT = False
    outputIR = False
    outputPrep = False
    outputFunctions = False
    outputGlyfPrograms = False
    outputCallGraph = False
    outputMaxStackDepth = False
    glyphs = []
    allGlyphs = False
    reduceFunctions = False

    def __init__(self, rawOptions, numFiles):
        for option, value in rawOptions:
            # general options
            if option == "-h":
                from fontTools import version
                print(__doc__ % version)
                sys.exit(0)
            elif option == "-i":
                self.outputIR = True
            elif option == "-s":
                self.outputState = True
            elif option == "--cvt":
                self.outputCVT = True
            elif option == "-c":
                self.outputCallGraph = True
            elif option == "-m":
                self.outputMaxStackDepth = True
            elif option == "-p":
                self.outputPrep = True
            elif option == "-f":
                self.outputFunctions = True
            elif option == "-z":
                self.outputGlyfPrograms = True
            elif option == "-g":
                self.glyphs.append(value)
            elif option == "-G":
                self.allGlyphs = True
            elif option == "-v":
                self.verbose = True
            elif option == "-r":
                self.reduceFunctions = True

        if (self.verbose):
            logging.basicConfig(level = logging.INFO)
        else:
            logging.basicConfig(level = logging.ERROR)

def usage():
    from fontTools import version
    print(__doc__ % version)
    sys.exit(2)

def process(jobs, options):
    for input in jobs:
        tt = TTFont()
        tt.importXML(input, quiet=True)
        bc = BytecodeContainer(tt)

        if (options.allGlyphs):
            glyphs = filter(lambda x: x != 'fpgm' and x != 'prep', bc.programs.keys())
        else:
            glyphs = map(lambda x: 'glyf.'+x, options.glyphs)

        ae, called_functions = analysis(bc, glyphs)

        if (options.outputPrep):
            print ("PREP:")
            bc.programs['prep'].body.pretty_print(options.outputIR)
            print ()
        if (options.outputFunctions):
            for key, value in bc.function_table.items():
                print ("Function #%d:" % (key))
                value.body.pretty_print(options.outputIR)
                print ()
        if (options.outputGlyfPrograms):
            for glyph in glyphs:
                print ("%s:" % glyph)
                bc.programs[glyph].body.pretty_print(options.outputIR)
                print ()

        if (options.outputCallGraph):
            print ("called function set:")
            print (called_functions)
            print ("call graph (function, # calls to):")
            for item in ae.global_function_table.items():
                print (item)

        if (options.outputState):
            ae.environment.pretty_print()
        if (options.outputCVT):
            print("CVT = ", ae.environment.cvt)
        if (options.outputMaxStackDepth):
            print("Max Stack Depth =", ae.maximum_stack_depth)
        if (options.reduceFunctions):
            if not options.allGlyphs:
                glyphs = filter(lambda x: x != 'fpgm' and x != 'prep', bc.programs.keys())
                called_functions.update(executeGlyphs(ae, glyphs)) 
            
            function_set = ae.environment.function_table.keys()
            unused_functions = [item for item in function_set if item not in called_functions]
          
            bc.removeFunctions(unused_functions)
            bc.updateTTFont(tt)
            output = "Reduced"+input
            output = makeOutputFileName(output, ".ttf")
            tt.save(output)

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "hiscpfzGmg:vr", ['cvt'])
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
            jobs.append(output)
        elif fileformat == 'ttx':
            jobs.append(input)
        else:
            raise NotImplementedError
    return jobs, options

def main(args):
    jobs, options = parseOptions(args)
    process(jobs, options)
    
if __name__ == "__main__":
    main(sys.argv[1:])
