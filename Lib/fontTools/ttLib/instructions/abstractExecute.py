from fontTools.ttLib.data import dataType
import logging
import copy
import math
import IntermediateCode as IR
logger = logging.getLogger(" ")
global_fucntion_table = {}
class IdentifierGenerator(object):
    def __init__(self):
        self.countTable = {}
    def generateIdentifier(self, tag):
        if tag in self.countTable:
            number = self.countTable[tag]
        else:
            number = 0
            self.countTable[tag] = 0
        self.countTable[tag] = self.countTable[tag] + 1
        return '$' + tag + str(number)

class DataFlowRegion(object):
    def __init__(self):
        self.condition = None
        self.outRegion = []
        self.inRegion = None

identifierGenerator = IdentifierGenerator()
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
        self.current_instruction_intermediate = []
        self.variables = []
    def topVar(self):
        return  self.variables[-1]

    def __repr__(self):

        stackRep = str(self.program_stack[-3:])
        if (len(self.program_stack) > 3):
            stackRep = '[..., ' + stackRep[1:]
        return str('storage = ' + str(self.storage_area) + 
            ', graphics_state = ' + str(self.graphics_state) 
            + ', stack = ' + stackRep + ', length = ' + str(len(self.program_stack)))

    def merge(self,executionContext2):
        '''
        merge the executionContext of the if-else
        '''
        if len(executionContext2.program_stack)!=len(self.program_stack):
            executionContext2.pretty_print()
            self.pretty_print()
        assert len(executionContext2.program_stack)==len(self.program_stack)
        for item in executionContext2.storage_area:
            if item not in self.storage_area:
                self.append(item)
        '''
        deal with Graphics state
        '''
        for gs_key in self.graphics_state:
            if self.graphics_state[gs_key] != executionContext2.graphics_state[gs_key]:
                logger.info("graphics_state%s become uncertain", gs_key)
                self.graphics_state[gs_key] = dataType.UncertainValue([self.graphics_state[gs_key],
                                        executionContext2.graphics_state[gs_key]])
                logger.info("possible values are %s", str(self.graphics_state[gs_key].possibleValues))

    def pretty_print(self):
        print self.__repr__()

    def set_currentInstruction(self, instruction):
        self.current_instruction = instruction
        self.tag = (str(instruction.id)).split(".")[0]

    def set_graphics_state_to_default(self):
        self.graphics_state = {
            'pv':                (1, 0), # Unit vector along the X axis.
            'fv':                (1, 0),
            'dv':                (1, 0),
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
            'autoFlip':          True
            }

    def set_storage_area(self, index, value):
        self.storage_area[index] = value

    def read_storage_area(self, index):
        return self.storage_area[index]

    def getVariable(self):
        res = self.variables[-1]
        self.variables.pop()
        return res  

    def assignVariable(self, var, data):
        self.current_instruction_intermediate.append(IR.CopyStatement(var, data))

    def putVariable(self, data=None, assign = True):
        tempVariableName = identifierGenerator.generateIdentifier(self.tag)
        tempVariable = IR.Variable(tempVariableName, data)
        if data is not None and assign:
            self.assignVariable(tempVariable, data)
        self.variables.append(tempVariable)
        

    def program_stack_pop(self, num=1):
        for i in range(num):
            self.program_stack.pop()

    def unary_operation(self, op, action):
        if isinstance(op, dataType.AbstractValue):
            res = dataType.Expression(op, action)
        elif action is 'ceil':
            res = math.ceil(op)
        elif action is 'floor':
            res = math.floor(op)
        elif action is 'abs':
            res = math.fabs(op)
        return res

    def binary_operation(self, action):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)
        v_op2 = self.getVariable()
        v_op1 = self.getVariable()
            
        expression = None
        if isinstance(op1,dataType.AbstractValue) or isinstance(op2,dataType.AbstractValue):
            res = dataType.Expression(op1, op2, action)
            if action is not 'MAX' and action is not 'MIN':
                expression = IR.BinaryExpression(v_op1, v_op2, getattr(IR,action+'Operator')())
        elif action is 'ADD':
            res = op1 + op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.ADDOperator())
        elif action is 'GT':
            res = op1 > op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.GTOperator())
        elif action is 'GTEQ':
            res = op1 >= op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.GTEQOperator())
        elif action is 'AND':
            res = op1 and op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.ANDOperator())
        elif action is 'OR':
            res = op1 or op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.OROperator())
        elif action is 'MUL':
            res = op1 * op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.MULOperator())
        elif action is 'DIV':
            res = op1 / op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.DIVOperator())
        elif action is 'EQ':
            res = op1 == op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.EQOperator())
        elif action is 'NEQ':
            res = op1 != op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.NEQOperator())
        elif action is 'LT':
            res = op1 < op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.LTOperator())
        elif action is 'LTEQ':
            res = op1 <= op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.LTEQOperator())
        elif action is 'MAX':
            res = max(op1,op2)
        elif action is 'MIN':
            res = min(op1,op2)
        elif action is 'SUB':
            res = op1 - op2
            expression = IR.BinaryExpression(v_op1,v_op2,IR.SUBOperator())
        else:
            raise NotImplementedError
        
        self.program_stack.append(res)
        self.putVariable(expression, False)
        resVariable = self.topVar()
        if action is 'MAX' or action is 'MIN':
            three_address_code = getattr(IR, action+'MethodCall')([v_op1,v_op2], resVariable)
            self.current_instruction_intermediate.append(three_address_code)
        else:
            self.current_instruction_intermediate.append(IR.OperationAssignmentStatement(resVariable, expression))

    def exec_PUSH(self):
        for item in self.current_instruction.data:
            self.program_stack.append(item)
            self.putVariable(item)

    # Don't execute any cfg-related instructions
    # This has the effect of "executing both branches".
    def exec_IF(self):
        pass
    def exec_EIF(self):
        pass
    def exec_ELSE(self):
        pass

    def exec_AA(self):#AdjustAngle
        self.program_stack.pop()

    def exec_ABS(self):#Absolute
        op1 = self.program_stack[-1]
        res = self.unary_operation(op1, 'abs')
        self.program_stack[-1] = res
        v_op = self.getVariable()
        self.putVariable(res, False)
        resVar = self.topVar()
        self.current_instruction_intermediate.append(IR.ABSMethodCall([v_op],resVar))

    def exec_ADD(self):
        self.binary_operation('ADD')
        

    def exec_ALIGNPTS(self):
        '''
        move to points, has no further effect on the stack
        '''
        self.program_stack_pop(2)

    def exec_ALIGNRP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_AND(self):
        self.binary_operation('AND')

    def exec_CEILING(self):
        op1 = self.program_stack[-1]
        res = self.unary_operation(op1, 'ceil')
        self.program_stack[-1] = res
        v_op = self.getVariable()
        self.putVariable(res, False)
        resVar = self.topVar()
        self.current_instruction_intermediate.append(IR.CEILINGMethodCall([v_op],resVar))

    def exec_CINDEX(self):#CopyXToTopStack
        index = self.program_stack[-1]
        self.program_stack.pop()
        #the index start from 1
        top = self.program_stack[-index]
        self.program_stack.append(top)
        self.putVariable(top)

    def exec_CLEAR(self):#ClearStack
        self.program_stack = []

    def exec_DEBUG(self):#DebugCall
        self.program_stack_pop()

    def exec_DELTA(self):
        number = self.program_stack[-1]
        self.program_stack_pop()
        self.program_stack_pop(2*number)

    def exec_DELTAC1(self):#DeltaExceptionC1
        self.exec_DELTA()

    def exec_DELTAC2(self):#DeltaExceptionC2
        self.exec_DELTA()

    def exec_DELTAC3(self):#DeltaExceptionC3
        self.exec_DELTA()

    def exec_DELTAP1(self):#DeltaExceptionC1
        self.exec_DELTA()

    def exec_DELTAP2(self):#DeltaExceptionC2
        self.exec_DELTA()

    def exec_DELTAP3(self):#DeltaExceptionC3
        self.exec_DELTA()

    def exec_DEPTH(self):#GetDepthStack
        depth = len(self.program_stack)
        self.program_stack.append(depth)
        self.putVariable(depth)
    
    def exec_DIV(self):#Divide
        self.binary_operation('DIV')

    def exec_DUP(self):#DuplicateTopStack
        top = self.program_stack[-1]
        self.program_stack.append(top)
        self.putVariable(top)

    def exec_FLIPOFF(self):
        self.graphics_state['autoFlip'] = False
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('false')))

    def exec_FLIPON(self):
        self.graphics_state['autoFlip'] = True
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('true')))

    def exec_FLIPPT(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_FLIPRGOFF(self):
        self.program_stack_pop(2)

    def exec_FLIPRGON(self):
        self.program_stack_pop(2)
        
    def exec_FLOOR(self):
        op1 = self.program_stack[-1]
        res = self.unary_operation(op1, 'floor')
        self.program_stack[-1] = res
        v_op = self.getVariable()
        self.putVariable(res, False)
        resVar = self.topVar()
        self.current_instruction_intermediate.append(IR.FLOORMethodCall([v_op],resVar))

    def exec_GC(self):
        top = self.program_stack[-1]
        self.program_stack_pop()
        v_op = self.getVariable()
        self.program_stack.append(dataType.AbstractValue())
        self.putVariable(dataType.AbstractValue(), False)
        resVar = self.getVariable()
        self.current_instruction_intermediate.append(IR.GCMethodCall([v_op],resVar))
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
        v_op = self.getVariable()
        self.putVariable(dataType.EngineInfo(), False)
        resVar = self.topVar()
        self.program_stack.append(dataType.EngineInfo())
        self.current_instruction_intermediate.append(IR.GETINFOMethodCall([v_op],resVar))

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
        self.graphics_state['loop'] = 1
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
        index = self.program_stack[-1]
        self.program_stack.pop()
        #the index start from 1
        top = self.program_stack[-index]
        del self.program_stack[-index]
        self.program_stack.append(top)

    def exec_MIRP(self):
        self.program_stack_pop(2)

    def exec_MPPEM(self):
        if self.graphics_state['pv'] == (0, 1):
            self.program_stack.append(dataType.PPEM_Y())
            self.putVariable(dataType.PPEM_Y())
        else:
            self.program_stack.append(dataType.PPEM_X())
            self.putVariable(dataType.PPEM_X())
    def exec_MPS(self):
        self.program_stack.append(dataType.PointSize())
    def exec_MSIRP(self):
        self.program_stack_pop(2)
    def exec_MUL(self):
        self.binary_operation('MUL')
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
        else:
            self.program_stack[-1] = 0
    def exec_NROUND(self):
        pass
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
        self.putVariable(res)
    def exec_RDTG(self):
        pass

    def exec_ROFF(self):
        pass

    def exec_ROLL(self):
        op1 = self.program_stack[-1]
        self.program_stack[-1] = self.program_stack[-3]
        self.program_stack[-3] = self.program_stack[-2]
        self.program_stack[-2] = op1

    def exec_ROUND(self):
        self.program_stack_pop()
        self.program_stack.append(dataType.F26Dot6())

    def exec_RS(self):
        op = self.program_stack[-1]
        self.program_stack_pop()
        self.variables.pop()
        try:
            res = self.storage_area[op]
            self.program_stack.append(res)
            self.putVariable(res)
        except KeyError:
            raise KeyError
        
    def exec_RTDG(self):
        pass
    def exec_RTG(self):
        pass
    def exec_RTHG(self):
        pass
    def exec_RUTG(self):
        pass
    def exec_S45ROUND(self):
        self.program_stack_pop()
    def exec_SANGW(self):
        self.program_stack_pop()

    def exec_SCANCTRL(self):
        self.program_stack_pop()
        self.variables.pop()   
 
    def exec_SCANTYPE(self):
        self.program_stack_pop()
        self.variables.pop()    

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
        self.program_stack_pop(2)

    def exec_SFVTPV(self):#Set Freedom Vector To Projection Vector
        self.graphics_state['fv'] = self.graphics_state['gv']

    def exec_SHC(self):
        self.program_stack_pop(1)
    def exec_SHP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)
    def exec_SHPIX(self):
        self.program_stack_pop()
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)
    def exec_SHZ(self):
        self.program_stack_pop(1)
    def exec_SLOOP(self):
        self.graphics_state['loop'] = self.program_stack[-1]
        self.program_stack_pop()
    def exec_SMD(self):
        self.program_stack_pop()

    def exec_SPVFS(self):
        self.program_stack_pop(2)

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
            
        if data == 1:
            self.graphics_state['pv'] = (1, 0)
            self.graphics_state['fv'] = (1, 0)
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.FreedomVector(),IR.Constant(data)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.ProjectionVector(),IR.Constant(data)))

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
        self.exec_WCVTP()

    def exec_WCVTP(self):
        res = self.getOpandVar()
        self.cvt[res[0]] = res[1]
        assert not isinstance(res[0], dataType.AbstractValue)
        self.current_instruction_intermediate.append(IR.CVTStorageStatement(res[2],res[3]))
       
    def getOpandVar(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)

        v2 = self.getVariable()
        v1 = self.getVariable()
        return [op1,op2,v1,v2]

    def exec_WS(self):
        res = self.getOpandVar()
        self.current_instruction_intermediate.append(IR.WriteStorageStatement(res[2],res[3]))

        assert not isinstance(res[0], dataType.AbstractValue)

        self.storage_area[res[0]] = res[1]

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
        #self.graphics_state['rp'][index] = self.program_stack[-1]
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

    def exec_SDB(self):
        self.program_stack_pop()

    def exec_CALL(self):
        data = self.program_stack[-1]
        self.program_stack_pop()
        var = self.getVariable()
        self.current_instruction_intermediate.append(IR.CallStatement(var))
        

    def execute(self):
        self.current_instruction_intermediate = []
        getattr(self,"exec_"+self.current_instruction.mnemonic)()
        return self.current_instruction_intermediate

def setGSDefaults():
    intermediateCodes = []
    intermediateCodes.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('true')))
    intermediateCodes.append(IR.CopyStatement(IR.ScanControl(),IR.Boolean('false')))
    intermediateCodes.append(IR.CopyStatement(IR.SingleWidthCutIn(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.SingleWidthValue(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.FreedomVector(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.ProjectionVector(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.LoopValue(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.InstructControl(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.MinimumDistance(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.RoundState(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.ZP0(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.ZP1(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.ZP2(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.RP0(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.RP1(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.RP2(),IR.Constant(0)))
    return intermediateCodes

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
        self.program_state = {}
        self.maximum_stack_depth = 0
        self.intermediateCodes = []
        self.conditionBlock = None
        
    def execute_all(self):
        for key in self.font.local_programs.keys():
            self.execute(key)

    def execute_CALL(self):
        for item in self.program_state:
            if item.startswith('fpgm'):
                self.program_state[item] = []
        top = self.environment.program_stack[-1]
        #if top not in self.program.call_function_set:
        self.program.call_function_set.append(top)
        if top not in global_fucntion_table:
            global_fucntion_table[top] = 1
        else:
            global_fucntion_table[top] += 1 
        logger.info('ADD CALL SET:%s', top)
        logger.info('ADD CALL SET:%s', self.program.call_function_set)
        self.environment.set_currentInstruction(self.program_ptr)
        intermediateCodes = self.environment.execute()
        self.intermediateCodes = self.intermediateCodes+ intermediateCodes
        self.program_ptr = self.font.function_table[top].start()
        
        logger.info("jump to call function "+self.program_ptr.mnemonic)

    def execute(self,tag):
        self.program = self.font.programs[tag]
        self.program_ptr = self.program.start()
        is_back_ptr = False
        back_ptr = []
        successors_index = []
        top_if = None
        self.program_state = {}
        self.intermediateCodes = setGSDefaults()

        while self.program_ptr is not None:
            if self.program_ptr.data is not None:
                logger.info("%s->%s%s",self.program_ptr.id,self.program_ptr.mnemonic,self.program_ptr.data)
            else:
                logger.info("%s->%s",self.program_ptr.id,self.program_ptr.mnemonic)

            if not is_back_ptr:
                if self.program_ptr.mnemonic == 'CALL':
                    back_ptr.append((self.program_ptr,None))
                    self.execute_CALL()
            
                self.environment.set_currentInstruction(self.program_ptr)
                intermediateCodes = self.environment.execute()
                if self.conditionBlock is None:
                    self.intermediateCodes = self.intermediateCodes+ intermediateCodes
                else:
                    self.conditionBlock.appendStatements(intermediateCodes)

            if (len(self.environment.program_stack) > self.maximum_stack_depth):
                self.maximum_stack_depth = len(self.environment.program_stack)
            
            if self.program_ptr.mnemonic == 'IF':
                newBlock = IR.IfElseBlock(self.environment.variables[-1])
                self.environment.program_stack.pop()
                self.environment.variables.pop()
                newBlock.setParent(self.conditionBlock)
                self.conditionBlock = newBlock
                self.conditionBlock.mode = 'IF'
                top_if = self.program_ptr
                successors_index.append(0)
                back_ptr.append((self.program_ptr, copy.deepcopy(self.environment)))
            
            if self.program_ptr.mnemonic == 'ELSE':
                self.conditionBlock.mode = 'else'

            if self.program_ptr.mnemonic == 'EIF':
                if self.conditionBlock.parentBlock == None:
                    self.intermediateCodes.append(self.conditionBlock)
                else:
                    self.conditionBlock.parentBlock.appendStatement(self.conditionBlock)
                self.conditionBlock = self.conditionBlock.parentBlock
            
            logger.info(self.environment)
            if len(back_ptr) > 1:
                s = ''
                for back in back_ptr:
                    s = s + str(back[0].id) +'->'+ str(back[0].mnemonic) + ' '
                logger.info('back%s',s)
        
            if len(self.program_ptr.successors) == 0 or self.program_ptr.mnemonic == 'EIF':
                if top_if is not None:
                    if top_if.id not in self.program_state or len(self.program_state[top_if.id])==0:
                        logger.warn("STORE %s program state ", top_if.id)
                        self.program_state[top_if.id] = [self.environment]
                    elif not (self.program_ptr.mnemonic == 'EIF' and len(self.program_state[top_if.id])==2):
                        logger.warn("APPEND %s program state ", top_if.id)
                        self.program_state[top_if.id].append(self.environment)
                        logger.warn("program environment will be merged")
                        logger.info('len%s',len(self.program_state[top_if.id]))
                        self.program_state[top_if.id][0].merge(self.program_state[top_if.id][1])
                        self.environment = self.program_state[top_if.id][0]
                        logger.info(self.environment)
            if len(back_ptr)>0 and len(self.program_ptr.successors) == 0:
                self.program_ptr = back_ptr[-1][0]
                logger.info("program pointer back to %s %s", str(self.program_ptr),str(self.program_ptr.id))
                if len(back_ptr)>0 and back_ptr[-1][0].mnemonic == 'IF':
                    top_if = back_ptr[-1][0]
                is_back_ptr = True
                if back_ptr[-1][1] is None:
                    back_ptr.pop()

            if len(self.program_ptr.successors) > 1:
                self.program_ptr = self.program_ptr.successors[successors_index[-1]]
                if successors_index[-1]>0 and (self.program_ptr.mnemonic != 'EIF' or successors_index[-1] != 2):
                    logger.warn("program environment recover to")
                    self.environment = back_ptr[-1][1]
                    logger.info(self.environment)
                logger.info("traverse another branch %s->%s", self.program_ptr.id, self.program_ptr.mnemonic)
                is_back_ptr = False
                if self.program_ptr.mnemonic == 'EIF':
                    successors_index.pop()
                    back_ptr.pop()
                    top_if = None
                else:
                    successors_index[-1] = successors_index[-1] + 1
                    
                continue
            
            if len(self.program_ptr.successors) == 1:
                self.program_ptr = self.program_ptr.successors[0]
                is_back_ptr = False
                continue
            if len(self.program_ptr.successors) == 0 and len(back_ptr)==0:
                self.program_ptr = None

        for intermediateCode in self.intermediateCodes:
            try:
                print intermediateCode
            except:
                pass
        print self.program.call_function_set
        for item in global_fucntion_table.items():
            print item
