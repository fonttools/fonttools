from fontTools.ttLib.data import dataType
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
        #print('graphics_state',self.graphics_state,'program_stack',self.program_stack)
        print('storage_area',self.storage_area,'program_stack',self.program_stack)

    def set_currentInstruction(self, instruction):
        self.current_instruction = instruction

    def set_graphics_state_to_default(self):
        self.graphics_state = {
            'pv':                [0x4000, 0], # Unit vector along the X axis.
            'fv':                [0x4000, 0],
            'dv':                [0x4000, 0],
            'rp':                [0,0,0],
            'zp':                [1,1,1],
            #'controlValueCutIn': 17/16, #(17 << 6) / 16, 17/16 as an f26dot6.
            #'deltaBase':         9,
            #'deltaShift':        3,
            #'minDist':           1, #1 << 6 1 as an f26dot6.
            #'loop':              1,
            #'roundPhase':        1,
            #'roundPeriod':       1,#1 << 6,1 as an f26dot6.
            #'roundThreshold':    0.5,#1 << 5, 1/2 as an f26dot6.
            #'roundSuper45':      False,
            #'autoFlip':          True
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
    #don't execute any cfg-related instructions
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
        if isinstance(op1,dataType.AbstractValue) or isinstance(op2,dataType.AbstractValue):
            res = dataType.Expression(op1,op2,action)
        elif action is 'GT':
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
        elif action is 'LT':
            res = op1 < op2
        elif action is 'LTEQ':
            res = op1 <= op2

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
        self.binary_operation('LT')
    def exec_LTEQ(self):
        self.binary_operation('LTEQ')
    def exec_MAX(self):
        pass
    def exec_MD(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        assert isinstance(op1, dataType.PointValue) and (op1, dataType.PointValue)
        res = dataType.Distance()
        self.program_stack.append(res)
    def exec_MDAP(self):
        op = self.program_stack[-1]
        assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)
    def exec_MDRP(self):
        op = self.program_stack[-1]
        assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)
    def exec_MIAP(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
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
        op = self.program_stack[-1]
        res = self.storage_area[op]
        self.program_stack.append(res) 
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
        data = self.current_instruction.data[0]
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
        op = self.program_stack[-1]
        assert isinstance(op, dataType.Distance)
        self.program_stack_pop(1)

    def exec_SPVFS(self):
        pass
    def exec_SPVTCA(self):
        data = self.current_instruction.data[0]
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
        data = self.current_instruction.data[0]
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
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        self.storage_area[op1] = op2
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

class Executor(object):
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