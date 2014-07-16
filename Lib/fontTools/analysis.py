from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.instructions import statements, instructionConstructor
import sys

class Body(object):
    """ 
    Encapsulates a set of statements.
    This is a tree structure of statments 
    """
    def __init__(self,*args, **kwargs):
        if kwargs.get('statement_root') is not None:
            self.statement_root = kwargs.get('statement_root')
        if kwargs.get('instructions') is not None:
            input_instructions = kwargs.get('instructions')
            self.statement_root = self.constructSuccessorAndPredecessor(input_instructions)
    def num_of_branches(self):
        #TODO
        self.num_of_branches = 0
    def compute_stack_level(self):
        #TODO
        pass
    def constructSuccessorAndPredecessor(self,input_statements):
        def is_not_divid_branch(instruction):
            if isinstance(instruction,statements.all.EIF_Statement):
                return False
            elif isinstance(instruction,statements.all.ELSE_Statement):
                return False
            else:
                return True
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
            elif index < len(input_statements)-1 and is_not_divid_branch(input_statements[index+1]):
                this_instruction.add_successor(input_statements[index+1])
                input_statements[index+1].set_predecessor(this_instruction)
            # An IF statement should have two successors:
            #  one already added (index+1); one at the ELSE/ENDIF.
            if isinstance(this_instruction,statements.all.IF_Statement):
                if_waited.append(this_instruction)
            elif isinstance(this_instruction,statements.all.ELSE_Statement):
                this_if = if_waited[-1]
                this_if.add_successor(this_instruction)
            elif isinstance(this_instruction,statements.all.EIF_Statement):
                this_if = if_waited[-1]
                this_if.add_successor(this_instruction)
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

    '''
    the transform function will make break the stack-based truetype bytecode and 
    make the instruction in a format : op [data]
    '''
    def transform(self):
        pass

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
#per glyph instructions
class Program(object):
    def __init__(self, input):
        self.body = Body(instructions = input)
    
    def print_program(self):
        self.body.pretty_print()

class BytecodeFont(object):
    """ Represents the original bytecode-related global data for a TrueType font. """
    def __init__(self):
        # CVT Table (initial)
        self.cvt_table = {}
        self.global_program = {}
        # tag id -> Program
        self.local_programs = {}
        self.body = {}
        # function_table: function label -> Function
        self.function_table = {}
    def setup(self,programs):
        self.global_program['fpgm'] = programs['fpgm']
        self.global_program['prep'] = programs['prep']
        self.setup_global_programs()
        self.setup_local_programs(programs)
    
    def setup_global_programs(self):
        self.extractFunctions()
        self.pre_compute()
    def setup_local_programs(self, programs):
        for key, instr in programs.items():
            if key is not 'fpgm' and key is not 'prep':
                program = Program(instr)
                self.local_programs[key] =  program
        
        #for key, value in self.local_programs.items():
            #print(key)
            #value.print_program()
        
    #preprocess and get the function definitions
    def extractFunctions(self,):
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
        
class Environment(object):
    """Abstractly represents the global environment at a single point in time. 

    The global environment consists of a Control Variable Table (CVT) and
    storage area, as well as a program stack.

    The cvt_table consists of a dict mapping locations to 16-bit signed
    integers.

    The function_table consists of a dict mapping function labels to lists
    of instructions.

    The storage_area consists of a dict mapping locations to 32-bit numbersself
    [again, same comment as for cvt_table].

    The program stack abstractly represents the program stack. This is the
    critical part of the abstract state, since TrueType consists of an
    stack-based virtual machine.

    """
    def __init__(self):
        # cvt_table: location -> Value
        self.cvt_table = {}
        # storage_area: location -> Value
        self.storage_area = {}
        self.graphics_state = {}
        self.program_stack = []

class Value(object):
    """Represents either a concrete or abstract TrueType value."""
    pass

class AbstractValue(Value):
    pass

class ConcreteValue(Value):
    pass

class AbstractExecutor(object):
    """
    Given a TrueType instruction, abstractly transform the global state.

    Produces a new global state accounting for the effects of that
    instruction. Modifies the stack, CVT table, and storage area.

    """
    def __init__(self,font):
        self.function_table = font.function_table
        
    def execute(self,instruction,incoming_state):
        self.data = []
        #get data from incoming, feed it to instructions
        self.program_stack = incoming_state.program_stack
         
        if isinstance(instruction,instructions.all.FDEF):
            self.function_table[self.program_stack[-1]] = Function(instruction.data)

        if instruction.get_pop_num()>0: 
            for i in range(instruction.get_pop_num()):
                self.data.append(self.program_stack[-1])
                self.program_stack.pop()
        
        if instruction.get_push_num()>0:
            if len(self.data)>0:
                instruction.set_input(self.data)
            instruction.action()
            self.result = instruction.get_result()
            for data in self.result:
                incoming_state.program_stack.append(data)
                
#one ttFont object for one ttx file       
ttFont = BytecodeFont()

def constructCVTTable(tt):
    values = tt['cvt '].values
    key = 1
    for value in values:
        ttFont.cvt_table[key] = value
        key = key + 1

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

#tested#
def extractProgram(tt):
    #a dictionary maps tag->Program to extract all the bytecodes
    #in a single font file
    tag_to_program = {}
    
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
    ttp = ttFont.setup(tag_to_program)

def main(args):
    if len(args)<1:
        print("usage : please use the path of the font file as input")
    fileformat =args[0].split('.')[-1] 
    if fileformat == 'ttf':
    #TODO:transform ttf file to ttx and feed it to the analysis
        raise NotImplementedError
    if fileformat == 'ttx':
        tt = TTFont()
        tt.importXML(args[0])
    else:
        raise NotImplementedError
    constructCVTTable(tt)
    extractProgram(tt)

if __name__ == "__main__":
        main(sys.argv[1:])
