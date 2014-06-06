from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
import fontTools.ttLib.instructions
import sys

class Global(object):
    """Abstractly represents the global environment at a single point in time. 

The global environment consists of a Control Variable Table (CVT),
function table, and storage area, as well as a state and program
stack.

The cvt_table consists of a dict mapping locations to 16-bit signed
integers.  [do we actually need to keep this in the abstract store?]

The function_table consists of a dict mapping function labels to lists
of instructions.

The storage_area consists of a dict mapping locations to 32-bit numbers.
[again, same comment as for cvt_table].

State appears to always be 1 at the moment.

The program stack abstractly represents the program stack. This is the
critical part of the abstract state, since TrueType consists of an
stack-based virtual machine.

    """
    def __init__(self):
        # cvt_table: location -> value
        self.cvt_table = {}
        # function_table: function label -> list of instructions
        self.function_table = {}
        # storage_area: location -> value
        self.storage_area = {}
        self.program_stack = []
    def insert_function():
        pass

class AbstractExecutor(object):
    """Given a TrueType instruction, abstractly transform the global state.

Produces a new global state accounting for the effects of that
instruction. Modifies the stack, CVT table, and storage area.

    """
    def __init__(self,prgm_global):
        self.global_env = prgm_global
        
    def execute(self,instruction):
        self.data = []
        #get data from global, feed it to instructions
        self.program_stack = self.global_env.program_stack
        
        self.instruction = instruction
        print("program stack",self.program_stack,self.instruction.get_pop_num())
        if len(self.program_stack)>0:
            self.instruction.set_top(self.program_stack[-1])

        if self.instruction.get_pop_num()>0: 
            for i in range(self.instruction.get_pop_num()):
                self.data.append(self.program_stack[-1])
                self.program_stack.pop()
        
        if self.instruction.get_push_num()>0:
            if len(self.data)>0:
                self.instruction.set_input(self.data)
            self.instruction.action()
            self.result = self.instruction.get_result()
            for data in self.result:
                self.global_env.program_stack.append(data)

        if isinstance(self.instruction,instructions.all.FDEF):
            self.global_env.function_table[self.instruction.top] = self.instruction.data

class Body(object):
    """ Encapsulates a set of instructions. """
    def __init__(self,body,ttf,id=0):
        self.body = body
        self.instructions = ttf[self.body].program.getAssembly()
        self.id = id 

global_env = Global()
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
            this_fdef = body_instructions[i]
        #any instructions expect for the FDEF should have at least 
        #the next instruction in stream as a successor
        elif isinstance(body_instructions[i],instructions.all.JMPR):
            pass
        elif isinstance(body_instructions[i],instructions.all.JROT):
            pass
        elif isinstance(body_instructions[i],instructions.all.JROF):
            pass
        elif i < len(body_instructions)-1:
            body_instructions[i].add_successor(body_instructions[i+1])
        #FDEF should be followed by ENDF
        if isinstance(body_instructions[i],instructions.all.ENDF):           
            this_fdef.add_successor(body_instructions[i])
        #IF statement should have two successors (depends on the condition)
        if isinstance(body_instructions[i],instructions.all.IF):
            this_if = body_instructions[i]
        elif isinstance(body_instructions[i],instructions.all.ELSE):
            this_if.add_successor(body_instructions[i])
        elif isinstance(body_instructions[i],instructions.all.EIF):
            pass # TODO

        # We don't think these instructions are actually ever used.
        if isinstance(body_instructions[i],instructions.all.JMPR):
            raise NotImplementedError
        elif isinstance(body_instructions[i],instructions.all.JROT):
            raise NotImplementedError
        elif isinstance(body_instructions[i],instructions.all.JROF):
            raise NotImplementedError

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
        #load the data and initialize the cvt table 
        constructCVTTable(ttf['cvt '].values)
        #TODO:for now just analyze the font program file, later
        #should add the prep and all the glyphs
        fpgm_program = Body('fpgm',ttf)
        #construct instructions with the data in instruction stream
        constructInstructions(fpgm_program)
        #build successors for every instruction
        constructSuccessor(fpgm_program)
        
        font_global = Global()
        executor = AbstractExecutor(font_global)

        instruction = fpgm_program.instructions[0]
        
        while instruction.successor_size() is not 0:
            executor.execute(instruction)
            instruction.prettyPrinter()
            instruction = instruction.get_successor()

        for key,value in font_global.function_table.items():
            print(key)
            for instruction in value:
                instruction.prettyPrinter()
        

if __name__ == "__main__":
        main(sys.argv[1:])
