"""\
usage: pyftanalysis [options] inputfile

    pyftanalysis %s -- TrueType Bytecode Analysis Tool

    General options:
    -h Help: print this message
    -m MaxStackDepth: print out the maximum stack depth for the executed code
    -s State: print the graphics state after executing prep
    -c CVT: print the CVT after executing prep
    -f Functions: print out function and prep bytecodes
    -g NAME Glyph: execute prep plus hints for glyph NAME
    -G AllGlyphs: execute prep plus hints for all glyphs in font
    -v Verbose: be more verbose
"""

from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.instructions import statements, instructionConstructor, abstractExecute
from fontTools.ttLib.data import dataType
import sys
import getopt
import math
import pdb
import logging
import copy

class Body(object):
    '''
    Encapsulates a list of statements.
    '''
    def __init__(self,*args, **kwargs):
        if kwargs.get('statement_root') is not None:
            self.statement_root = kwargs.get('statement_root')
        if kwargs.get('instructions') is not None:
            input_instructions = kwargs.get('instructions')
            self.statement_root = self.constructSuccessorAndPredecessor(input_instructions)
        self.condition = None

    def set_condition(self,expression):
        self.condition = expression #the eval(expression) should return true for choosing this 

    def constructSuccessorAndPredecessor(self,input_statements):
        def is_branch(instruction):
            if isinstance(instruction,statements.all.EIF_Statement):
                return True
            elif isinstance(instruction,statements.all.ELSE_Statement):
                return True
            else:
                return False
        if_waited = []
        for index in range(len(input_statements)): 
            this_instruction = input_statements[index]
            # We don't think jump statements are actually ever used.
            if isinstance(this_instruction,statements.all.JMPR_Statement):
                raise NotImplementedError
            elif isinstance(this_instruction,statements.all.JROT_Statement):
                raise NotImplementedError
            elif isinstance(this_instruction,statements.all.JROF_Statement):
                raise NotImplementedError
            #other statements should have at least 
            #the next instruction in stream as a successor
            elif index < len(input_statements)-1 and not is_branch(input_statements[index+1]):
                this_instruction.add_successor(input_statements[index+1])
                input_statements[index+1].set_predecessor(this_instruction)
            # An IF statement should have two successors:
            #  one already added (index+1); one at the ELSE/ENDIF.
            if isinstance(this_instruction,statements.all.IF_Statement):
                if_waited.append(this_instruction)
            elif isinstance(this_instruction,statements.all.ELSE_Statement):
                this_if = if_waited[-1]
                this_if.add_successor(this_instruction)
                this_instruction.set_predecessor(this_if)
            elif isinstance(this_instruction,statements.all.EIF_Statement):
                this_if = if_waited[-1]
                this_if.add_successor(this_instruction)
                this_instruction.set_predecessor(this_if)
                if_waited.pop()
        return input_statements[0]

    def pretty_print(self):
        level = 1
        instruction = self.statement_root
        instruction_stack = []
        instruction_stack.append(instruction)

        def printHelper(instruction,level):
            print(level*"   ", instruction)

        level = 0
        while len(instruction_stack)>0:
            top_instruction = instruction_stack[-1]
            printHelper(top_instruction,level)
            if isinstance(top_instruction, statements.all.IF_Statement) or isinstance(top_instruction, statements.all.ELSE_Statement):
                level = level + 1
            instruction_stack.pop()
            if len(top_instruction.successors) == 0:
                level = level - 1
            elif len(top_instruction.successors) > 1:
                reverse_successor = top_instruction.successors[::-1]
                instruction_stack.extend(reverse_successor)
            else:
                instruction_stack.extend(top_instruction.successors)

class Function(object):
    def __init__(self, instructions=None):
        #function contains a function body
        self.instructions = []
    def pretty_printer(self):
        self.body.pretty_printer()
    def constructBody(self):
        #convert the list to tree structure
        self.body = Body(instructions = self.instructions)
    def start(self):
        return self.body.statement_root

#per glyph instructions
class Program(object):
    def __init__(self, input):
        self.body = Body(instructions = input)
        self.call_function_set = []#a set of function being called in the tag program
    
    def start(self):
        return self.body.statement_root
    
    def print_program(self):
        self.body.pretty_print()

class BytecodeContainer(object):
    """ Represents the original bytecode-related global data for a TrueType font. """
    def __init__(self, tt):
        # tag id -> Program
        self.programs = {}
        # function_table: function label -> Function
        self.function_table = {}
        #preprocess the static value to construct cvt table
        self.constructCVTTable(tt)
        #extract instructions from font file
        self.extractProgram(tt)
        #original TTFont object to be replaced
        self.ttFont = tt

    def setup(self, programs):
        self.programs = programs
        self.extractFunctions(programs)
        self.setup_programs(programs)
    
    def constructCVTTable(self, tt):
        self.cvt_table = {}
        try:
            values = tt['cvt '].values
            key = 0
            for value in values:
                self.cvt_table[key] = value
                key = key + 1
        except:
            pass
    
    #tested#
    def extractProgram(self, tt):
        '''
        a dictionary maps tag->Program to extract all the bytecodes
        in a single font file
        '''
        tag_to_program = {}
        def constructInstructions(program_tag, instructions):
            thisinstruction = None
            instructions_list = []
            def combineInstructionData(instruction,data):
                instruction.add_data(data)
            number = 0
            for instruction in instructions:
                instructionCons = instructionConstructor.instructionConstructor(instruction)
                instruction = instructionCons.getClass()
        
                if isinstance(instruction, instructionConstructor.Data):
                    combineInstructionData(thisinstruction,instruction)
                else:
                    if thisinstruction is not None:
                        thisinstruction.id = program_tag + '.' + str(number)
                        instructions_list.append(thisinstruction)
                        number = number+1
                    thisinstruction = instruction

            instructions_list.append(thisinstruction)
            return instructions_list
        
        def addTagsWithBytecode(tt,tag):
            for key in tt.keys():
                if hasattr(tt[key], 'program'):
                    if len(tag) != 0:
                        program_tag = tag+"."+key
                    else:
                        program_tag = key
                    tag_to_program[program_tag] = constructInstructions(program_tag, tt[key].program.getAssembly())
                if hasattr(tt[key], 'keys'):
                    addTagsWithBytecode(tt[key],tag+key)

        addTagsWithBytecode(tt,"")
        self.setup(tag_to_program)
        
    #transform list of instructions -> Program 
    def setup_programs(self, programs):
        for key, instr in programs.items():
            if key is not 'fpgm':
                program = Program(instr)
                self.programs[key] =  program
        
    #preprocess the function definition instructions between <fpgm></fpgm>
    def extractFunctions(self, programs):
        instructions = programs['fpgm']
        functionsLabels = []
        skip = False
        function_ptr = None
        for instruction in instructions:
            if not skip:
                if isinstance(instruction, statements.all.PUSH_Statement):
                    functionsLabels.extend(instruction.data)
                if isinstance(instruction, statements.all.FDEF_Statement):
                    skip = True
                    function_ptr = Function()
            else:
                if isinstance(instruction, statements.all.ENDF_Statement):
                    skip = False
                    function_label = functionsLabels[-1]
                    functionsLabels.pop()
                    self.function_table[function_label] = function_ptr
                else:
                    function_ptr.instructions.append(instruction)
        
        for key, value in self.function_table.items():
            value.constructBody()

    def updateTTFont(self):
        self.replaceCVTTable()
        self.replaceProgram()   
 
    def replaceCVTTable(self):
        #Reset old cvt table with a new table filled with 0s
        self.ttFont['cvt '].values = array.array('i',(0,)*len(self.cvt_table))
        try:
            for i in range(len(self.cvt_table)):
                self.ttFont['cvt '].values[i] = self.cvt_table[i]
        except:
            pass

    def replaceProgram(self):
        pass

def analysis(tt, glyphs=[]):
    #one ttFont object for one ttx file       
    absExecutor = abstractExecute.Executor(tt)
    absExecutor.execute('prep')
    environment_after_prep = copy.deepcopy(absExecutor.environment)
    for glyph in glyphs:
        print(glyph)
        absExecutor.environment = copy.deepcopy(environment_after_prep)
        absExecutor.execute(glyph)
    return absExecutor

class Options(object):
    verbose = False
    outputState = False
    outputCVT = False
    outputFunctions = False
    outputMaxStackDepth = False
    glyphs = []
    allGlyphs = False

    def __init__(self, rawOptions, numFiles):
        for option, value in rawOptions:
            # general options
            if option == "-h":
                from fontTools import version
                print(__doc__ % version)
                sys.exit(0)
            elif option == "-s":
                self.outputState = True
            elif option == "-c":
                self.outputCVT = True
            elif option == "-m":
                self.outputMaxStackDepth = True
            elif option == "-f":
                self.outputFunctions = True
            elif option == "-g":
                self.glyphs.append(value)
            elif option == "-G":
                self.allGlyphs = True
            elif option == "-v":
                self.verbose = True

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
        ttFont = BytecodeContainer(tt)

        if (options.allGlyphs):
            glyphs = filter(lambda x: x != 'fpgm' and x != 'prep', ttFont.programs.keys())
        else:
            glyphs = map(lambda x: 'glyf.'+x, options.glyphs)

        ae = analysis(ttFont, glyphs)
        if (options.outputFunctions):
            ttFont.programs['prep'].body.pretty_print()
            for key, value in ttFont.function_table.items():
                print("Function #%d" % (key))
                value.body.pretty_print()

        if (options.outputState):
            ae.environment.pretty_print()
        if (options.outputCVT):
            print("CVT = ", ae.environment.cvt)
        if (options.outputMaxStackDepth):
            print("Max Stack Depth =", ae.maximum_stack_depth)

def parseOptions(args):
    try:
        rawOptions, files = getopt.getopt(args, "hscfGmg:v")
    except getopt.GetoptError:
        usage()

    if not files:
        usage()

    options = Options(rawOptions, len(files))
    jobs = []

    for input in files:
        fileformat = input.split('.')[-1]
        if fileformat == 'ttf':
            #TODO: transform ttf file to ttx and feed it to the analysis
            raise NotImplementedError
        if fileformat == 'ttx':
            jobs.append(input)
        else:
            raise NotImplementedError
    return jobs, options

def main(args):
    jobs, options = parseOptions(args)
    process(jobs, options)
    
if __name__ == "__main__":
    main(sys.argv[1:])
