from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.instructions import instructions, instructionConstructor
import sys

class BytecodeFont(object):
    """ Represents the bytecode-related data for a TrueType font. """
    def __init__(self):
        # CVT Table (initial)
        self.cvt_table = {}
        # Preprogram
        self.prep = {}
        # per-glyph programs
        self.programs = {}
        # function_table: function label -> list of instructions
        self.function_table = {}
    def insert_function():
        pass

class Environment(object):
    """Abstractly represents the global environment at a single point in time. 

The global environment consists of a Control Variable Table (CVT) and
storage area, as well as a program stack.

The cvt_table consists of a dict mapping locations to 16-bit signed
integers.

The function_table consists of a dict mapping function labels to lists
of instructions.

The storage_area consists of a dict mapping locations to 32-bit numbers.
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
        
        print("program stack",self.program_stack,instruction.get_pop_num())
        if len(self.program_stack)>0:
            instruction.set_top(self.program_stack[-1])

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

        if isinstance(instruction,instructions.all.FDEF):
            self.function_table[instruction.top] = instruction.data

class Body(object):
    """ Encapsulates a set of instructions. """
    def __init__(self,containing_font,tag,ttf,id=0):
        self.containing_font = containing_font
        self.instructions = ttf[tag].program.getAssembly()
        self.id = id 

global_env = Environment()
def constructSuccessor(body):
    body_instructions = body.instructions
    this_fdef = None
    #TODO revise this for loop and use iteration
    for i in range(len(body_instructions)):

        #recording mode: all the instructions betwen FDEF and ENDF are considered
        #as data in functions 
        #TODO:add a seperate function class   
        if this_fdef is not None and this_fdef.successor_size() is 0:
            this_fdef.data.append(body_instructions[i])
        
        if isinstance(body_instructions[i],instructions.all.FDEF):
            assert this_fdef is None
            this_fdef = body_instructions[i]
        # We don't think jump instructions are actually ever used.
        elif isinstance(body_instructions[i],instructions.all.JMPR):
            raise NotImplementedError
        elif isinstance(body_instructions[i],instructions.all.JROT):
            raise NotImplementedError
        elif isinstance(body_instructions[i],instructions.all.JROF):
            raise NotImplementedError
        #any instructions except for the FDEF should have at least 
        #the next instruction in stream as a successor
        elif i < len(body_instructions)-1:
            body_instructions[i].add_successor(body_instructions[i+1])
            
        # FDEF should be followed by ENDF
        if isinstance(body_instructions[i],instructions.all.ENDF):           
            this_fdef.add_successor(body_instructions[i])
            this_fdef = None
            
        #IF statement should have two successors (depends on the condition)
        if isinstance(body_instructions[i],instructions.all.IF):
            this_if = body_instructions[i]
        elif isinstance(body_instructions[i],instructions.all.ELSE):
            this_if.add_successor(body_instructions[i])
        elif isinstance(body_instructions[i],instructions.all.EIF):
            pass # TODO

        # what about CALL statements? I think add_successor is an
        # intraprocedural CFG, so CALL is probably opaque to
        # add_successor.
        # also: LOOPCALL

def constructCVTTable(values):
    key = 1
    global_env.cvt_table = {}
    for value in values:
        global_env.cvt_table[key] = value
        key = key + 1
        
def extractFunctions(fpgm_program):
    label = 1

def constructInstructions(body):
    thisinstruction = None
    instructions_list = []
    instructions = body.instructions

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
    body.instructions = instructions_list
    
def combineInstructionData(instruction,data):
        instruction.add_data(data)
        
def testSuccessor(body):
        instruction = body.instructions[0]
        
        while instruction.get_successor() is not None:
            instruction.prettyPrinter()
            instruction = instruction.get_successor()
    
def main(args):
        #assume input is .ttx file
        #TODO:input is .ttf file
        input = args[0]
        ttf = TTFont()
        ttf.importXML(input,quiet=True)

        bytecode_font = BytecodeFont()
        constructCVTTable(ttf['cvt '].values)
        # TODO:for now just analyze the font program file, later
        # should add the prep and all the glyphs
        body = Body(bytecode_font, 'fpgm', ttf)

        constructInstructions(body)
        constructSuccessor(body)
        
        current_state = Environment()
        executor = AbstractExecutor(bytecode_font)

        instruction = body.instructions[0]
        
        while instruction.successor_size() is not 0:
            executor.execute(instruction, current_state)
            instruction.prettyPrinter()
            instruction = instruction.get_successor()

        for key,value in bytecode_font.function_table.items():
            print(key)
            for instruction in value:
                instruction.prettyPrinter()
        

if __name__ == "__main__":
        main(sys.argv[1:])
