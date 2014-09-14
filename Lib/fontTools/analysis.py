from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.instructions import statements, instructionConstructor, stackValues, abstractExecute
from fontTools.ttLib.data import dataType
import sys
import math
import pdb
import logging

class Expression(object):
    def __init__(self,op1 = None,op2 = None,operation = None):
        self.op1 = op1
        self.op2 = op2
        self.operation = operation

    def eval(self):
        options = {'LT':less,
                'LTEQ':lessEqual,
                'GT':greater,
                'GTEQ':greaterEqual,
                'EQ':equal,
                'AND':logicAnd,
                'OR':logicOr}
        if isinstance(op1, AbstractValue) or isinstance(op2, AbstractValue):
            return 'uncertain'
        return options[self.operation](self.op1,self.op2)
        def less(op1,op2):
            return op1 < op2
        def lessEqual(op1,op2):
            return op1 <= op2
        def greater(op1,op2):
            return op1 > op2
        def greaterEqual(op1,op2):
            return op1 >= op2
        def logicAnd(op1,op2):
            return (op1 and op2)
        def logicOr(op1,op2):
            return (op1 or op2)

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
    def compute_stack_level(self):
        #TODO
        pass
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
        # what about CALL statements? I think .successors is an
        # intraprocedural CFG, so CALL is probably opaque to .successors.
        # also: LOOPCALL

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
    def appendInstruction(self,instruction):
        self.instructions.append(instruction)
    def pretty_printer(self):
        self.body.pretty_printer()
    #pre-compute the number of data a funtion consumes
    def argumentNum(self):
        pass
    def constructBody(self):
        #convert the list to tree structure
        self.body = Body(instructions = self.instructions)
    def printBody(self):
        self.body.pretty_print()
    def start_ptr(self):
        return self.body.statement_root

#per glyph instructions
class Program(object):
    def __init__(self, input):
        self.body = Body(instructions = input)
    
    def start_ptr(self):
        return self.body.statement_root
    def print_program(self):
        self.body.pretty_print()

class BytecodeFont(object):
    """ Represents the original bytecode-related global data for a TrueType font. """
    def __init__(self, tt):
        self.global_program = {}
        # tag id -> Program
        self.local_programs = {}
        # function_table: function label -> Function
        self.function_table = {}
        self.programs = {}
        #preprocess the static value to construct cvt table
        self.constructCVTTable(tt)
        #extract instructions from font file
        self.extractProgram(tt)

    def setup(self,programs):
        self.programs = programs
        self.global_program['fpgm'] = programs['fpgm']
        self.global_program['prep'] = programs['prep']
        self.setup_global_programs()
        self.setup_local_programs(programs)
        self.programs = dict(self.global_program.items() + self.local_programs.items())
    
    def constructCVTTable(self, tt):
        self.cvt_table = {}
        values = tt['cvt '].values
        key = 1
        for value in values:
            self.cvt_table[key] = value
            key = key + 1
    
    #tested#
    def extractProgram(self, tt):
        '''
        a dictionary maps tag->Program to extract all the bytecodes
        in a single font file
        '''
        tag_to_program = {}
        def constructInstructions(instructions):
            thisinstruction = None
            instructions_list = []
            def combineInstructionData(instruction,data):
                instruction.add_data(data)

            for instruction in instructions:
                instructionCons = instructionConstructor.instructionConstructor(instruction)
                instruction = instructionCons.getClass()
        
                if isinstance(instruction, instructionConstructor.Data):
                    combineInstructionData(thisinstruction,instruction)
                else:
                    if thisinstruction is not None:
                        instructions_list.append(thisinstruction)
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
                    tag_to_program[program_tag] = constructInstructions(tt[key].program.getAssembly())
                if hasattr(tt[key], 'keys'):
                    addTagsWithBytecode(tt[key],tag+key)

        addTagsWithBytecode(tt,"")
        ttp = self.setup(tag_to_program)
    def setup_global_programs(self):
        #build the function table
        self.extractFunctions()

    #transform list of instructions -> Program 
    def setup_local_programs(self, programs):
        for key, instr in programs.items():
            if key is not 'fpgm':
                program = Program(instr)
                self.local_programs[key] =  program
        
    #preprocess the function definition instructions between <fpgm></fpgm>
    def extractFunctions(self):
        instructions = self.global_program['fpgm']
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
                    function_ptr.appendInstruction(instruction)
        
        for key, value in self.function_table.items():
            print(key)
            value.constructBody()
            value.printBody()
        
def analysis(tt):
    ttFont = BytecodeFont(tt)
    #one ttFont object for one ttx file       
    absExecutor = abstractExecute.Executor(ttFont)
    absExecutor.execute('prep')

def main(args):
    if len(args)<1:
        print("usage : please use the path of the font file as input")
    fileformat = args[0].split('.')[-1] 
    if fileformat == 'ttf':
    #TODO:transform ttf file to ttx and feed it to the analysis
        raise NotImplementedError
    if fileformat == 'ttx':
        tt = TTFont()
        tt.importXML(args[0])
    else:
        raise NotImplementedError
    analysis(tt)
    
if __name__ == "__main__":
        main(sys.argv[1:])
