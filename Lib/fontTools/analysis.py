from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont
from fontTools.ttLib.instructions import statements, instructionConstructor, stackValues
from fontTools.ttLib.data import dataType
import sys
import math
import pdb
import logging

class Expression(self):
    def __init__(self):
        self.op1 = None
        self.op2 = None
        self.operation = None

def eval(expression):
    options = {'<':less,
                '<=':lessEqual,
                '>':greater,
                '>=':greaterEqual,
                '==':equal,
                '&&':logicAnd,
                '||':logicOr}
    if op1 isinstance AbstractValue() or op2 isinstance AbstractValue():
        return 'uncertain'
    return options[expression.operation](expression.op1,expression.op2)
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
    def condition(self):

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
    def __init__(self):
        # CVT Table (initial)
        self.cvt_table = {}
        self.global_program = {}
        # tag id -> Program
        self.local_programs = {}
        # function_table: function label -> Function
        self.function_table = {}
        self.programs = {}

    def setup(self,programs):
        self.programs = programs
        self.global_program['fpgm'] = programs['fpgm']
        self.global_program['prep'] = programs['prep']
        self.setup_global_programs()
        self.setup_local_programs(programs)
        self.programs = dict(self.global_program.items() + self.local_programs.items())
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
        
class ExecutionContext(object):
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
    def __init__(self,ttFont):
        self.function_table = ttFont.function_table
        # cvt_table: location -> Value
        self.cvt_table = ttFont.cvt_table
        # storage_area: location -> Value
        self.storage_area = {}
        self.set_graphics_state_to_default()
        self.program_stack = []
        self.current_instruction = None
    def pretty_print(self):
        print('graphics_state',self.graphics_state,'program_stack',self.program_stack)
        #pdb.set_trace()

    def set_currentInstruction(self, instruction):
        self.current_instruction = instruction

    def set_graphics_state_to_default(self):
        self.graphics_state = {
            'pv':                [0x4000, 0], # Unit vector along the X axis.
            'fv':                [0x4000, 0],
            'dv':                [0x4000, 0],
            'rp':                [0,0,0],
            'zp':                [1,1,1],
            'controlValueCutIn': 17/16, #(17 << 6) / 16, 17/16 as an f26dot6.
            'deltaBase':         9,
            'deltaShift':        3,
            'minDist':           1, #1 << 6 1 as an f26dot6.
            'loop':              1,
            'roundPhase':        1,
            'roundPeriod':       1,#1 << 6,1 as an f26dot6.
            'roundThreshold':    0.5,#1 << 5, 1/2 as an f26dot6.
            'roundSuper45':      False,
            'autoFlip':          True
            }

    def set_storage_area(self, index, value):
        self.storage_area[index] = value

    def read_storage_area(self, index):
        return self.storage_area[index]

    def program_stack_pop(self, num=1):
        for i in range(num):
            self.program_stack.pop()
    def exec_PUSH(self):
        for item in self.current_instruction.data:
            self.program_stack.append(item)
    def exec_IF(self):
        pass
    def exec_EIF(self):
        pass
    def exec_ELSE(self):
        pass
    def exec_AA(self):#AdjustAngle
        pass

    def exec_ABS(self):#Absolute
        top = self.program_stack[-1]
        if  top< 0:
            top = -top
            self.program_stack[-1] = top

    def exec_ADD(self):
        add1 = self.program_stack[-1]
        add2 = self.program_stack[-2]
        self.program_stack.pop()
        self.program_stack[-1] = add1 + add2
    
    def binary_operation(self,action):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        if action is 'GT':
            res = op1 > op2
        elif action is 'GTEQ':
            res = op1 >= op2
        elif action is 'AND':
            res = op1 and op2
        elif action is 'OR':
            res = op1 or op2
        elif action is 'DIV':
            res = op1/op2
        elif action is 'EQ':
            res = op1 == op2

        self.program_stack_pop(2)
        self.program_stack.append(res)

    def exec_ALIGNPTS(self):
        '''
        move to points, has no further effect on the stack
        '''
        self.program_stack_pop(2)

    def exec_ALIGNRP(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_AND(self):
        self.binary_operation('AND')

    def exec_CEILING(self):
        self.program_stack[-1] = math.ceil(self.program_stack[-1])

    def exec_CINDEX(self):#CopyXToTopStack
        index = self.program_stack[-1]
        #the index start from 1
        top = self.program_stack[index-1]
        self.program_stack.append(top)

    def exec_CLEAR(self):#ClearStack
        self.program_stack = []

    def exec_DEBUG(self):#DebugCall
        self.program_stack_pop()

    def exec_DELTAC1(self):#DeltaExceptionC1
        pass
    def exec_DEPTH(self):#GetDepthStack
        self.program_stack.append(len(self.program_stack))
    
    def exec_DIV(self):#Divide
        binary_operation('DIV')

    def exec_DUP(self):#DuplicateTopStack
        self.program_stack.append(self.program_stack[-1])

    def exec_FLIPOFF(self):
        self.graphics_state['autoFlip'] = False

    def exec_FLIPON(self):
        self.graphics_state['autoFlip'] = True

    def exec_FLIPPT(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_FLIPRGOFF(self):
        self.program_stack_pop(2)

    def exec_FLIPRGON(self):
        self.program_stack_pop(2)

    def exec_FLOOR(self):
        self.program_stack[-1] = math.floor(self.program_stack[-1])

    def exec_GC(self):
        top = self.program_stack[-1]
        self.program_stack_pop(1)

    def exec_GETINFO(self):
        '''
        if h.stack[-1]&(1<<0) != 0:
        #Set the engine version. We hard-code this to 35, the same as
        #the C freetype code, which says that "Version~35 corresponds
        #to MS rasterizer v.1.7 as used e.g. in Windows~98".
        res |= 35
            
        if h.stack[-1]&(1<<5) != 0:
        #Set that we support grayscale.
        res |= 1 << 12
            
        #We set no other bits, as we do not support rotated or stretched glyphs.
        h.stack[-1] = res
        '''
        pass

    def exec_GPV(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.graphics_state['pv'] = (op1,op2)
        self.program_stack_pop(2)

    def exec_GFV(self):
        op1 = self.graphics_state['fv'][0]
        op2 = self.graphics_state['fv'][1]
        self.program_stack.append(op1)
        self.program_stack.append(op2)

    def exec_GT(self):
        self.binary_operation('GT')

    def exec_GTEQ(self):
        self.binary_operation('GTEQ')

    def exec_IDEF(self):
        raise NotImplementedError

    def exec_INSTCTRL(self):
        raise NotImplementedError
    
    def exec_IP(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)
    def exec_ISECT(self):
        self.program_stack_pop(5)
    def exec_IUP(self):
        pass
    def exec_LOOPCALL(self):
        pass
    def exec_LT(self):
        pass
    def exec_LTEQ(self):
        pass
    def exec_MAX(self):
        pass
    def exec_MD(self):
        pass
    def exec_MDAP(self):
        pass
    def exec_MDRP(self):
        pass
    def exec_MIAP(self):
        pass
    def exec_MIN(self):
        pass
    def exec_MINDEX(self):
        pass
    def exec_MIRP(self):
        pass
    def exec_MPPEM(self):
        if self.graphics_state['pv'] == [0, 0x4000]:
            self.program_stack.append(dataType.PPEM_Y())
        else:
            self.program_stack.append(dataType.PPEM_X())
    def exec_MPS(self):
        pass
    def exec_MSIRP(self):
        pass
    def exec_MUL(self):
        pass
    def exec_NEG(self):
        pass
    def exec_NEQ(self):
        pass
    def exec_NOT(self):
        pass
    def exec_NROUND(self):
        pass
    def exec_ODD(self):
        pass
    def exec_OR(self):
        self.binary_operation('OR')
    def exec_POP(self):
        pass
    def exec_RCVT(self):
        pass
    def exec_RDTG(self):
        pass
    def exec_ROFF(self):
        pass
    def exec_ROLL(self):
        pass
    def exec_ROUND(self):
        pass
    def exec_RS(self):
        pass
    def exec_RTDG(self):
        pass
    def exec_RTG(self):
        pass
    def exec_RTHG(self):
        pass
    def exec_RUTG(self):
        pass
    def exec_S45ROUND(self):
        pass
    def exec_SANGW(self):
        pass
    def exec_SCANCTRL(self):
        pass
    def exec_SCANTYPE(self):
        pass
    def exec_SCFS(self):
        pass
    def exec_SCVTCI(self):
        pass
    def exec_SDBV(self):
        pass
    def exec_SDPVTL(self):
        pass
    def exec_SDS(self):
        pass
    def exec_SFVFS(self):
        pass
    def exec_SFVTCA(self):#Set Freedom Vector To Coordinate Axis
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['fv'] = [0, 0x4000]
        if data == 1:
            self.graphics_state['fv'] = [0x4000, 0]
           
    def exec_SFVTL(self):#Set Freedom Vector To Line
    #Todo: finish it
        '''
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        point1 = (0, 0, op1)
        point2 = (0, 0, op2)
        self.program_stack_pop(2)
        dx := point2[0] - point1[0]
        dy := point2[1] - point1[1]
        data = int(self.current_instruction.data[0])
        if data == 1:
            dy = -dy#data is 1:p1->p2
        '''
        logging.info("Set Freedom Vector To Line")

    def exec_SFVTPV(self):#Set Freedom Vector To Projection Vector
        self.graphics_state['fv'] = self.graphics_state['gv']

    def exec_SHC(self):
        pass
    def exec_SHP(self):
        pass
    def exec_SHPIX(self):
        pass
    def exec_SHZ(self):
        pass
    def exec_SLOOP(self):
        pass
    def exec_SMD(self):
        pass
    def exec_SPVFS(self):
        pass
    def exec_SPVTCA(self):
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['pv'] = (0, 0x4000)
            self.graphics_state['dv'] = (0, 0x4000)
        if data == 1:
            self.graphics_state['pv'] = (0x4000, 0)
            self.graphics_state['dv'] = (0x4000, 0)

    def exec_SPVTL(self):
        pass
    def exec_SROUND(self):
        pass
    def exec_SSW(self):
        pass
    def exec_SSWCI(self):
        pass
    def exec_SUB(self):
        pass
    def exec_SVTCA(self):
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['pv'] = [0, 0x4000]
            self.graphics_state['fv'] = [0, 0x4000]
            self.graphics_state['dv'] = [0, 0x4000]
        if data == 1:
            self.graphics_state['pv'] = [0x4000, 0]
            self.graphics_state['fv'] = [0x4000, 0]
            self.graphics_state['dv'] = [0x4000, 0]

    def exec_SWAP(self):
        pass
    def exec_SZP0(self):
        pass
    def exec_SZP1(self):
        pass
    def exec_SZP2(self):
        pass
    def exec_SZPS(self):
        pass
    def exec_UTP(self):
        pass
    def exec_WCVTF(self):
        pass
    def exec_WCVTP(self):
        pass
    def exec_WS(self):
        pass
    def exec_EQ(self):
        self.binary_operation('EQ')

    def round(self,value):
        if self.graphics_state['roundPeriod'] == 0:
            # Rounding is off.
            return value
        
        if value >= 0:
            result = value - self.graphics_state['roundPhase'] + self.graphics_state['roundThreshold']
            if self.graphics_state['roundSuper45']:
                result = result / self.graphics_state['roundPeriod']
                result = result * self.graphics_state['roundPeriod']
            else:
                result = result & (-self.graphics_state['roundPeriod'])
            if result < 0:
                result = 0
        #TODO
       
    def exec_RTDG(self):#RoundToDoubleGrid
        self.graphics_state['roundPeriod']
        
    def exec_RTG(self):#RoundToGrid
        self.graphics_state['roundPeriod']

    def exec_RUTG(self):#RoundUpToGrid
        self.graphics_state['roundPeriod']

    def exec_SRP(self,index):#SetRefPoint
        self.graphics_state['rp'][index] = self.program_stack[-1]
        self.program_stack_pop(1)

    def exec_SRP0(self):
        self.exec_SRP(0)
    
    def exec_SRP1(self):
        self.exec_SRP(1)

    def exec_SRP2(self):
        self.exec_SRP(2)

    def exec_S45ROUND(self):
        pass
    def exec_SANGW(self):
        pass
    def exec_SCANCTRL(self):
        pass
    def exec_SCANTYPE(self):
        pass
    def exec_SCFS(self):
        pass
    def exec_SCVTCI(self):
        self.graphics_state['controlValueCutIn'] = self.program_stack[-1]
        self.program_stack_pop(1)

    def exec_SDB(self):
        pass
    def execute(self):
        getattr(self,"exec_"+self.current_instruction.mnemonic)()

class AbstractExecutor(object):
    """
    Given a TrueType instruction, abstractly transform the global state.

    Produces a new global state accounting for the effects of that
    instruction. Modifies the stack, CVT table, and storage area.

    This class manages the program pointer like jump to function call
    """
    def __init__(self,font):
        self.font = font
        #maps instruction to ExecutionContext
        self.instruction_state = {}
        self.environment = ExecutionContext(font)
        self.program_ptr = None
        self.body = None
    def execute_all(self):
        for key in self.font.local_programs.keys():
            self.execute(key)

    def excute_CALL(self):
        top = self.environment.program_stack[-1]
        self.program_ptr = self.font.function_table[top].start_ptr()

    def execute(self,tag):
        self.program_ptr = self.font.programs[tag].start_ptr()

        back_ptr = None
        while len(self.program_ptr.successors)>0 or back_ptr != None:
            print("executing..." + self.program_ptr.mnemonic)
            self.environment.set_currentInstruction(self.program_ptr)
            if self.program_ptr.mnemonic == 'CALL':
                self.excute_CALL()
            else:
                self.environment.execute()
            
            
            self.environment.pretty_print()
            if len(self.program_ptr.successors) == 1:
                self.program_ptr = self.program_ptr.successors[0]
                successors_index = 1
                continue
            if len(self.program_ptr.successors) > 1 and successors_index<len(program_ptr.successors):
                back_ptr = self.program_ptr
                successors_index = 1
                continue
            if len(self.program_ptr.successors)==0:
                self.program_ptr = back_ptr
                continue


    def exec_CALL(self):
        pass
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
    '''
    a dictionary maps tag->Program to extract all the bytecodes
    in a single font file
    '''
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

def analysis(tt):
    #preprocess the static value to construct cvt table
    constructCVTTable(tt)
    #extract instructions from font file
    extractProgram(tt)
    absExecutor = AbstractExecutor(ttFont)
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
