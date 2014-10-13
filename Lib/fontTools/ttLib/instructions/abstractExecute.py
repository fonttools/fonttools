from fontTools.ttLib.data import dataType
import logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(" ")
class DataFlowRegion(object):
    def __init__(self):
        self.condition = None
        self.outRegion = []
        self.inRegion = None
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
        self.cvt = ttFont.cvt_table
        self.set_graphics_state_to_default()
        self.program_stack = []
        self.current_instruction = None
    def __repr__(self):
        return str('storage' + str(self.storage_area) + 'stack' + str(self.program_stack[-3:]))

    def merge(self,executionContext2):
        '''
        merge the executionContext of the if-else
        '''
        if len(executionContext2.program_stack)!=len(self.program_stack):
            logger.warn("merge different len stack")
        for item in executionContext2.storage_area:
            if item not in self.storage_area:
                self.append(item)
        '''
        deal with 
        '''

    def pretty_print(self):
        #print('graphics_state',self.graphics_state,'program_stack',self.program_stack)
        #print('cvt',self.cvt)
        logger.info('storage%sstack%s', str(self.storage_area),  str(self.program_stack[-10:]))
            #, str(self.cvt))

    def set_currentInstruction(self, instruction):
        self.current_instruction = instruction

    def set_graphics_state_to_default(self):
        self.graphics_state = {
            'pv':                (1, 0), # Unit vector along the X axis.
            'fv':                (1, 0),
            'dv':                [1, 0],
            'rp':                [0,0,0],
            'zp':                [1,1,1],
            #'controlValueCutIn': 17/16, #(17 << 6) / 16, 17/16 as an f26dot6.
            #'deltaBase':         9,
            #'deltaShift':        3,
            #'minDist':           1, #1 << 6 1 as an f26dot6.
            'loop':               1,
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
        #self.current_instruction.data = self.program_stack[-1*self.current_instruction.get_pop_num():]
        for i in range(num):
            self.program_stack.pop()

    def binary_operation(self,action):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        if isinstance(op1,dataType.AbstractValue) or isinstance(op2,dataType.AbstractValue):
            res = dataType.Expression(op1,op2,action)
        elif action is 'ADD':
            res = op1 + op2
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
        elif action is 'NEQ':
            res = op1 != op2
        elif action is 'LT':
            res = op1 < op2
        elif action is 'LTEQ':
            res = op1 <= op2
        elif action is 'MAX':
            res = max(op1,op2)
        elif action is 'MIN':
            res = min(op1,op2)
        elif action is 'SUB':
            res = op1 - op2
        else:
            raise NotImplementedError
        self.program_stack_pop(2)
        self.program_stack.append(res)

    def exec_PUSH(self):
        for item in self.current_instruction.data:
            self.program_stack.append(item)

    # Don't execute any cfg-related instructions
    # This has the effect of "executing both branches".
    def exec_IF(self):
        res = self.program_stack[-1]
        self.program_stack.pop()
        return res
    def exec_EIF(self):
        pass
    def exec_ELSE(self):
        pass

    def exec_AA(self):#AdjustAngle
        self.program_stack.pop()

    def exec_ABS(self):#Absolute
        top = self.program_stack[-1]
        if  top< 0:
            top = -top
            self.program_stack[-1] = top

    def exec_ADD(self):
        self.binary_operation('ADD')

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
        self.program_stack.pop()
        #the index start from 1
        top = self.program_stack[-index]
        self.program_stack.append(top)

    def exec_CLEAR(self):#ClearStack
        self.program_stack = []

    def exec_DEBUG(self):#DebugCall
        self.program_stack_pop()

    def exec_DELTAC1(self):#DeltaExceptionC1
        raise NotImplementedError
    def exec_DEPTH(self):#GetDepthStack
        self.program_stack.append(len(self.program_stack))
    
    def exec_DIV(self):#Divide
        self.binary_operation('DIV')

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
        self.program_stack_pop()
        self.program_stack.append(dataType.EngineInfo())

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
        #self.program_stack_pop()
        raise NotImplementedError

    def exec_INSTCTRL(self):
        #raise NotImplementedError
        self.program_stack_pop(2)
        #XX
    
    def exec_IP(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_ISECT(self):
        self.program_stack_pop(5)

    def exec_IUP(self):#drawing-only 
        pass

    def exec_LOOPCALL(self):
        raise NotImplementedError

    def exec_LT(self):
        self.binary_operation('LT')

    def exec_LTEQ(self):
        self.binary_operation('LTEQ')

    def exec_MAX(self):
        self.binary_operation('MAX')

    def exec_MD(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        #assert isinstance(op1, dataType.PointValue) and (op1, dataType.PointValue)
        res = dataType.Distance()
        self.program_stack.append(res)

    def exec_MDAP(self):
        op = self.program_stack[-1]
        #assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)

    def exec_MDRP(self):
        op = self.program_stack[-1]
        #assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)

    def exec_MIAP(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)

    def exec_MIN(self):
        self.binary_operation('MIN')

    def exec_MINDEX(self):
        raise NotImplementedError

    def exec_MIRP(self):
        self.program_stack_pop(2)

    def exec_MPPEM(self):
        if self.graphics_state['pv'] == (0, 1):
            self.program_stack.append(dataType.PPEM_Y())
        else:
            self.program_stack.append(dataType.PPEM_X())
    def exec_MPS(self):
        raise NotImplementedError
    def exec_MSIRP(self):
        raise NotImplementedError
    def exec_MUL(self):
        self.program_stack_pop(2)
        self.program_stack.append(dataType.F26Dot6())
    def exec_NEG(self):
        op = self.program_stack[-1]
        if isinstance(op, dataType.AbstractValue):
            pass
        else:
            self.program_stack[-1] = -op
    def exec_NEQ(self):
        self.binary_operation('NEQ')
    def exec_NOT(self):
        op = self.program_stack[-1]
        if isinstance(op, dataType.AbstractValue):
            pass
        if (op == 0):
            self.program_stack[-1] = 1
        else
            self.program_stack[-1] = 0
    def exec_NROUND(self):
        raise NotImplementedError
    def exec_ODD(self):
        raise NotImplementedError
    def exec_OR(self):
        self.binary_operation('OR')
    def exec_POP(self):
        self.program_stack_pop()
    def exec_RCVT(self):
        op = self.program_stack[-1]
        self.program_stack_pop()
        res = self.cvt[op]
        self.program_stack.append(res)
    def exec_RDTG(self):
        raise NotImplementedError

    def exec_ROFF(self):
        raise NotImplementedError

    def exec_ROLL(self):
        op1 = self.program_stack[-1]
        op2 = self.program_stack[-2]
        self.program_stack[-1] = self.program_stack[-3]
        self.program_stack[-3] = self.program_stack[-2]
        self.program_stack[-2] = self.program_stack[-1]

    def exec_ROUND(self):
        self.program_stack_pop()
        self.program_stack.append(dataType.F26Dot6())

    def exec_RS(self):
        op = self.program_stack[-1]
        self.program_stack_pop()
        try:
            res = self.storage_area[op]
            self.program_stack.append(res)
        except KeyError:
            raise KeyError
            #self.program_stack.append(0)
    def exec_RTDG(self):
        raise NotImplementedError
    def exec_RTG(self):
        raise NotImplementedError
    def exec_RTHG(self):
        raise NotImplementedError
    def exec_RUTG(self):
        raise NotImplementedError
    def exec_S45ROUND(self):
        raise NotImplementedError
    def exec_SANGW(self):
        raise NotImplementedError

    def exec_SCANCTRL(self):
        self.program_stack_pop()
    
    def exec_SCANTYPE(self):
        self.program_stack_pop()
    
    def exec_SCFS(self):
        self.program_stack_pop(2)

    def exec_SCVTCI(self):
        self.program_stack_pop()

    def exec_SDB(self):
        self.program_stack_pop()

    def exec_SDPVTL(self):
        self.program_stack_pop(2)

    def exec_SDS(self):
        self.program_stack_pop()

    def exec_SFVFS(self):
        self.program_stack_pop(2)

    def exec_SFVTCA(self):#Set Freedom Vector To Coordinate Axis
        data = self.current_instruction.data[0]
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['fv'] = (0, 1)
        if data == 1:
            self.graphics_state['fv'] = (1, 0)
           
    def exec_SFVTL(self):#Set Freedom Vector To Line
        raise NotImplementedError

    def exec_SFVTPV(self):#Set Freedom Vector To Projection Vector
        self.graphics_state['fv'] = self.graphics_state['gv']

    def exec_SHC(self):
        raise NotImplementedError
    def exec_SHP(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)
    def exec_SHPIX(self):
        loopValue = self.graphics_state['loop']
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)
    def exec_SHZ(self):
        raise NotImplementedError
    def exec_SLOOP(self):
        raise NotImplementedError
    def exec_SMD(self):
        op = self.program_stack[-1]
        assert isinstance(op, dataType.Distance)
        self.program_stack_pop()

    def exec_SPVFS(self):
        raise NotImplementedError
    def exec_SPVTCA(self):
        data = self.current_instruction.data[0]
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['pv'] = (0, 1)
            self.graphics_state['dv'] = (0, 1)
        if data == 1:
            self.graphics_state['pv'] = (1, 0)
            self.graphics_state['dv'] = (1, 0)

    def exec_SPVTL(self):
        self.program_stack_pop(2)

    def exec_SROUND(self):
        self.program_stack_pop()

    def exec_SSW(self):
        self.program_stack_pop()

    def exec_SSWCI(self):
        self.program_stack_pop()

    def exec_SUB(self):
        self.binary_operation('SUB')

    def exec_SVTCA(self):
        data = self.current_instruction.data[0]
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['pv'] = (0, 1)
            self.graphics_state['fv'] = (0, 1)
            self.graphics_state['dv'] = (0, 1)
        if data == 1:
            self.graphics_state['pv'] = (1, 0)
            self.graphics_state['fv'] = (1, 0)
            self.graphics_state['dv'] = (1, 0)

    def exec_SWAP(self):
        tmp = self.program_stack[-1]
        self.program_stack[-1] = self.program_stack[-2]
        self.program_stack[-2] = tmp

    def exec_SZP0(self):
        self.program_stack_pop()

    def exec_SZP1(self):
        self.program_stack_pop()

    def exec_SZP2(self):
        self.program_stack_pop()

    def exec_SZPS(self):
        self.program_stack_pop()

    def exec_UTP(self):
        self.program_stack_pop()

    def exec_WCVTF(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        self.cvt[op1] = op2

    def exec_WCVTP(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        self.cvt[op1] = op2

    def exec_WS(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        assert not isinstance(op1,dataType.AbstractValue)

        self.storage_area[op1] = op2

    def exec_EQ(self):
        self.binary_operation('EQ')
       
    def exec_RTDG(self):#RoundToDoubleGrid
        pass
        #self.graphics_state['roundPeriod']
        
    def exec_RTG(self):#RoundToGrid
        pass
        #self.graphics_state['roundPeriod']

    def exec_RUTG(self):#RoundUpToGrid
        pass
        #self.graphics_state['roundPeriod']

    def exec_SRP(self,index):#SetRefPoint
        self.graphics_state['rp'][index] = self.program_stack[-1]
        self.program_stack_pop()

    def exec_SRP0(self):
        self.exec_SRP(0)
    
    def exec_SRP1(self):
        self.exec_SRP(1)

    def exec_SRP2(self):
        self.exec_SRP(2)

    def exec_S45ROUND(self):
        self.program_stack_pop()

    def exec_SANGW(self):
        self.program_stack_pop()
    
    def exec_SCFS(self):
        self.program_stack_pop(2)

    def exec_SCVTCI(self):
        self.graphics_state['controlValueCutIn'] = self.program_stack[-1]
        self.program_stack_pop()

    def exec_CALL(self):
        self.program_stack_pop()

    def exec_SDB(self):
        self.program_stack_pop()
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
        self.program = None

    def execute_all(self):
        for key in self.font.local_programs.keys():
            self.execute(key)

    def excute_CALL(self):
        top = self.environment.program_stack[-1]
        #if top not in self.program.call_function_set:
        self.program.call_function_set.append(top)
        logger.info('ADD CALL SET:%s', top)
        logger.info('ADD CALL SET:%s', self.program.call_function_set)
        self.program_ptr = self.font.function_table[top].start()
        self.font.function_table[top].printBody()
        self.environment.program_stack.pop()
        
        logger.info("jump to call function "+self.program_ptr.mnemonic)

    def execute(self,tag):
        self.program = self.font.programs[tag]
        self.program_ptr = self.program.start()
        is_back_ptr = False
        back_ptr = []
        successors_index = []
        top_if = None
        program_state = {}
        while len(self.program_ptr.successors)>0 or len(back_ptr)>0:
            if self.program_ptr.data is not None:
                logger.info("%s->%s%s",self.program_ptr.id,self.program_ptr.mnemonic,self.program_ptr.data)
            else:
                logger.info("%s->%s",self.program_ptr.id,self.program_ptr.mnemonic)
            if self.program_ptr.mnemonic == 'CALL' and not is_back_ptr:
                back_ptr.append((self.program_ptr,None))
                self.excute_CALL()

            self.environment.set_currentInstruction(self.program_ptr)
            self.environment.execute()
            
            if self.program_ptr.mnemonic == 'IF':
                top_if = self.program_ptr
                successors_index.append(0)
                back_ptr.append((self.program_ptr, self.environment))

            self.environment.pretty_print()
            if len(back_ptr) != 0:
                logger.info('back%s', str(back_ptr))
                if len(back_ptr)>0 and back_ptr[-1][0].mnemonic == 'IF':
                    top_if = back_ptr[-1][0]
                self.environment.pretty_print()
            if len(self.program_ptr.successors) == 0:
                if top_if.id not in program_state:
                    program_state[top_if.id] = [self.environment]
                    if back_ptr[-1][1] is not None:
                        logger.info("program environment recover to")
                        self.environment = back_ptr[-1][1]
                        self.environment.pretty_print()
                else:
                    program_state[top_if.id].append(self.environment)
                    logger.warn("STORE %s program state ", top_if.id)
                    if len(program_state[top_if.id])==2:
                        program_state[top_if.id][0].merge(program_state[top_if.id][1])
                        self.environment = program_state[top_if.id][0]
                        logger.warn("program environment merged")
                        self.environment.pretty_print()
                self.program_ptr = back_ptr[-1][0]
                logger.info("program pointer back to %s %s", str(self.program_ptr),str(self.program_ptr.id))
                back_ptr.pop()
                is_back_ptr = True

            if len(self.program_ptr.successors) > 1:
                self.program_ptr = self.program_ptr.successors[successors_index[-1]]
                is_back_ptr = False
                if successors_index[-1]==0:
                    successors_index[-1] = successors_index[-1] + 1
                else:
                    successors_index.pop()
                continue
            
            if len(self.program_ptr.successors) == 1:
                self.program_ptr = self.program_ptr.successors[0]
                is_back_ptr = False


               
