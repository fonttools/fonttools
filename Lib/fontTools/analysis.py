from __future__ import print_function, division, absolute_import
from ttLib import TTFont
from ttLib.instructions import statements, instructionConstructor
import sys

class Body(object):
    """ 
    Encapsulates a set of statments.
    This is a tree structure of statments
    the instruction's accessor is  
    """
    def __init__(self,statement_root):
        self.statement_root = statement_root
    def pinterHelper(self, indent):
        print("    ", indent)
    def pretty_printer(self):
        pass
    '''
    the transform function will make break the stack-based truetype bytecode and 
    make the instruction in a format : op [data]
    '''
    def transform(self):
        pass
class Function(object):
    def __init__(self, body, instructions=None):
        #function contains a function body
        self.body = body
    def appendInstruction(self,instruction):
        self.instruction.append(instruction)
    def pretty_printer(self):
        self.body.pretty_printer()
    #pre-compute the number of data a funtion consumes
    def argumentNum(self):
        pass

class BytecodeFont(object):
    """ Represents the bytecode-related data for a TrueType font. """
    def __init__(self):
        # CVT Table (initial)
        self.cvt_table = {}
        # Preprogram
        self.prep = {}
        # per-glyph id -> Program
        self.programs = {}
        # function_table: function label -> Function
        self.function_table = {}
    def set_programs(self, programs):
        self.programs = programs
        for key, program in self.programs.items():
            constructSuccessorAndPredecessor(program)
    def get_programs_from_ttf(self,tag,ttf,id=0):
        self.instructions = ttf[tag].program.getAssembly()

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
    """Given a TrueType instruction, abstractly transform the global state.

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
                
        

global_env = Environment()

def constructSuccessorAndPredecessor(input_statements):
    containing_fdef = None
    containing_if = []
    for index in range(len(input_statements)): 
        i = input_statements[index]
        
        if containing_fdef is not None:
            containing_fdef.data.append(i)

        if isinstance(i,statements.all.FDEF_Statement):
            assert containing_fdef is None # enforce non-nesting of FDEF
            containing_fdef = i
        # We don't think jump statements are actually ever used.
        elif isinstance(i,statements.all.JMPR_Statement):
            raise NotImplementedError
        elif isinstance(i,statements.all.JROT_Statement):
            raise NotImplementedError
        elif isinstance(i,statements.all.JROF_Statement):
            raise NotImplementedError
        #any statements except for the FDEF should have at least 
        #the next instruction in stream as a successor
        elif index < len(input_statements)-1:
            i.add_successor(input_statements[index+1])
            input_statements[index+1].set_predecessor(i)

        # FDEF should be followed by ENDF
        if isinstance(i,statements.all.ENDF_Statement):
            containing_fdef.add_successor(i)
            containing_fdef = None
        '''   
        # An IF statement should have two successors:
        #  one already added (index+1); one at the ELSE/ENDIF.
        if isinstance(i,statements.all.IF_Statement):
            # at the IF, push it onto the stack
            containing_if.append((i,None))
        elif isinstance(i,statements.all.ELSE_Statement):
            cif_info = containing_if.pop()
            # prev inst's successor is invalid; it will be the EIF
            # hence, record this inst for use at EIF:
            containing_if.append((cif_info[0], i))
            # set a second succ of the IF inst to this:
            cif_info[0].add_successor(i)
        elif isinstance(i,statements.all.EIF_Statement):
            cif_info = containing_if.pop()
            if (cif_info[1] is None):
                # if there was no ELSE,
                # then 2nd succ of the IF should be i
                cif_info[0].add_successor(i)
                i.
            else:
                # otherwise, set the succ of the inst before ELSE to this
                cif_info[1].add_successor(i)
        '''
        # what about CALL statements? I think .successors is an
        # intraprocedural CFG, so CALL is probably opaque to .successors.
        # also: LOOPCALL

def constructCVTTable(values):
    key = 1
    global_env.cvt_table = {}
    for value in values:
        global_env.cvt_table[key] = value
        key = key + 1

def constructInstructions(instructions):
    thisinstruction = None
    instructions_list = []
    def combineInstructionData(instruction,data):
        instruction.add_data(data)

    for instruction in instructions:
        instructionCons = instructionConstructor.instructionConstructor(instruction)
        instruction = instructionCons.getClass()
        
        if isinstance(instruction, instructionConstructor.data):
            combineInstructionData(thisinstruction,instruction)
        else:
            if thisinstruction is not None:
                instructions_list.append(thisinstruction)
            thisinstruction = instruction

    instructions_list.append(thisinstruction)
    return instructions_list

def extractProgram(tt):
    tag_to_program = {}

    #construct a dictionary maps tag->Program to extract all the bytecodes
    #in a single font file
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
    ttFont = BytecodeFont()
    ttp = ttFont.set_programs(tag_to_program)

def main(args):
        if len(args)<1:
            print("usage : please use the path of the font file as input")
        fileformat =args[0].split('.')[1] 
        if fileformat == 'ttf':
            raise NotImplementedError
            #tt = TTFont(args[0])
        if fileformat == 'ttx':
            tt = TTFont()
            tt.importXML(args[0])
        extractProgram(tt)

if __name__ == "__main__":
        main(sys.argv[1:])
