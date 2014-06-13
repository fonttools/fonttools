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
        # successors, predecessors: instruction -> list[instructions]
        self.successors = {}
        self.predecessors = {}
        self.id = id 

global_env = Environment()
def constructSuccessor(body):
    containing_fdef = None
    containing_if = []
    #TODO revise this for loop and use iteration
    for index in range(len(body.instructions)):
        i = body.instructions[index]
        
        #recording mode: all the instructions betwen FDEF and ENDF are considered
        #as data in functions
        #TODO:add a seperate function class
        if containing_fdef is not None and not containing_fdef in body.successors:
            containing_fdef.data.append(i)

        if isinstance(i,instructions.all.FDEF):
            assert containing_fdef is None # enforce non-nesting of FDEF
            containing_fdef = i
        # We don't think jump instructions are actually ever used.
        elif isinstance(i,instructions.all.JMPR):
            raise NotImplementedError
        elif isinstance(i,instructions.all.JROT):
            raise NotImplementedError
        elif isinstance(i,instructions.all.JROF):
            raise NotImplementedError
        #any instructions except for the FDEF should have at least 
        #the next instruction in stream as a successor
        elif index < len(body.instructions)-1:
            body.successors[i] = [body.instructions[index+1]]

        # FDEF should be followed by ENDF
        if isinstance(i,instructions.all.ENDF):
            body.successors[containing_fdef] = [i]
            containing_fdef = None
            
        # An IF statement should have two successors:
        #  one already added (index+1); one at the ELSE/ENDIF.
        if isinstance(i,instructions.all.IF):
            # at the IF, push it onto the stack
            containing_if.append((i,None))
        elif isinstance(i,instructions.all.ELSE):
            cif_info = containing_if.pop()
            # prev inst's successor is invalid; it will be the EIF
            body.successors[body.instructions[index-1]].pop()
            # hence, record this inst for use at EIF:
            containing_if.append((cif_info[0], i))
            # set a second succ of the IF inst to this:
            body.successors[cif_info[0]].append(i)
        elif isinstance(i,instructions.all.EIF):
            cif_info = containing_if.pop()
            if (cif_info[1] is None):
                # if there was no ELSE,
                # then 2nd succ of the IF should be i
                body.successors[cif_info[0]].append(i)
            else:
                # otherwise, set the succ of the inst before ELSE to this
                body.successors[cif_info[1]].append(i)

        # what about CALL statements? I think add_successor is an
        # intraprocedural CFG, so CALL is probably opaque to
        # add_successor.
        # also: LOOPCALL

def constructPredecessor(body):
    for i in range(len(body_instructions)):
        pass

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
            instruction.prettyPrint()
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
        
        while instruction in body.successors:
            executor.execute(instruction, current_state)
            instruction.prettyPrint()
            instruction = body.successors[instruction][0]

        for key,value in bytecode_font.function_table.items():
            print(key)
            for instruction in value:
                instruction.prettyPrint()
        

if __name__ == "__main__":
        main(sys.argv[1:])
