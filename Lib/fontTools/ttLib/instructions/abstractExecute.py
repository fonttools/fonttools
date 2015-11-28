from fontTools.ttLib.data import dataType
import logging
import copy
import IntermediateCode as IR
logger = logging.getLogger(" ")
class IdentifierGenerator(object):
    def generateIdentifier(self, tag, number):
        return '$' + tag + str(number)

class DataFlowRegion(object):
    def __init__(self):
        self.condition = None
        self.outRegion = []
        self.inRegion = None

identifierGenerator = IdentifierGenerator()
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
    def __init__(self, ttFont, tag):
        self.function_table = ttFont.function_table
        # cvt: location -> Value
        self.cvt = ttFont.cvt_table
        self.tag = tag
        # storage_area: location -> Value
        self.storage_area = {}
        self.set_graphics_state_to_default()
        # this is the TT VM stack, not the call stack
        self.program_stack = []
        self.minimum_stack_depth = None
        self.current_instruction = None
        self.current_instruction_intermediate = []

    def __repr__(self):
        stackVars = []
        for i in self.program_stack[-3:]:
            stackVars.append(i.data)
        stackRep = str(stackVars[-3:])
        if (len(self.program_stack) > 3):
            stackRep = '[..., ' + stackRep[1:]
        return str('storage = ' + str(self.storage_area) + 
            ', graphics_state = ' + str(self.graphics_state) 
            + ', program_stack = ' + stackRep + ', program_stack_length = ' + str(len(self.program_stack)))

    def make_copy(self, font):
        new_env = Environment(font, self.tag)
        for key, value in self.__dict__.iteritems():
            setattr(new_env, key, copy.copy(value))
        return new_env
    
    def merge(self,environment2):
        '''
        merge environment2 into this one; used at if-else merge.
        '''
        if len(environment2.program_stack)!=len(self.program_stack):
            print "impending assertion failure; here's the mismatched environments"
            environment2.pretty_print()
            self.pretty_print()
        assert len(environment2.program_stack)==len(self.program_stack)

        new_stack = []
        for (v1, v2) in zip(self.program_stack, environment2.program_stack):
            if (v1 == v2):
                new_stack.append(v1)
            else:
                new_stack.append(dataType.UncertainValue([v1, v2]))
        self.program_stack = new_stack

        for item in environment2.storage_area:
            if item not in self.storage_area:
                self.append(item)
        '''
        deal with Graphics state
        '''
        for gs_key in self.graphics_state:
            if self.graphics_state[gs_key] != environment2.graphics_state[gs_key]:
                logger.info("graphics_state %s became uncertain", gs_key)
                new_graphics_state = set()
                if(type(self.graphics_state[gs_key]) is dataType.UncertainValue):
                    new_graphics_state.update(self.graphics_state[gs_key].possibleValues)
                else:
                    new_graphics_state.add(self.graphics_state[gs_key])
                if(type(environment2.graphics_state[gs_key]) is dataType.UncertainValue):
                    new_graphics_state.update(environment2.graphics_state[gs_key].possibleValues)
                else:
                    new_graphics_state.add(environment2.graphics_state[gs_key])
                self.graphics_state[gs_key] = dataType.UncertainValue(list(new_graphics_state))
                logger.info("possible values are %s", str(self.graphics_state[gs_key].possibleValues))

    def pretty_print(self):
        print self.__repr__()

    def set_current_instruction(self, instruction):
        self.current_instruction = instruction

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

    def stack_top_name(self):
        return identifierGenerator.generateIdentifier(self.tag, self.stack_depth())

    def generate_assign_variable(self, var, data):
        self.current_instruction_intermediate.append(IR.CopyStatement(var, data))

    def stack_depth(self):
        return len(self.program_stack)
        
    def program_stack_push(self, data = None, assign = True):
        tempVariableName = self.stack_top_name()
        tempVariable = IR.Variable(tempVariableName, data)
        if data is not None and assign:
            self.generate_assign_variable(tempVariable, data)
        self.program_stack.append(tempVariable)
        return tempVariable

    def program_stack_pop(self, num=1):
        last_val = None
        for i in range(num):
            last_val = self.program_stack.pop()
        if self.stack_depth() < self.minimum_stack_depth:
            self.minimum_stack_depth = self.stack_depth()
        return last_val

    def unary_operation(self, action):
        op = self.program_stack_pop()
        v = IR.Variable(self.stack_top_name(), op)

        if action is 'ceil':
            e = IR.CEILMethodCall([v])
        elif action is 'floor':
            e = IR.FLOORMethodCall([v])
        elif action is 'abs':
            e = IR.ABSMethodCall([v])
        elif action is 'not':
            e = IR.NOTMethodCall([v])
        res = e.eval()
        self.program_stack_push(res, False)
        self.current_instruction_intermediate.append(IR.OperationAssignmentStatement(v, res))
        return res

    def binary_operation(self, action):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)

        expression = None
        if isinstance(op1.data,dataType.AbstractValue) or isinstance(op2.data,dataType.AbstractValue):
            res = dataType.Expression(op1.data, op2.data, action)
            if action is not 'MAX' and action is not 'MIN':
                expression = IR.BinaryExpression(op1, op2, getattr(IR,action+'Operator')())
            else:
                expression = getattr(IR, action+'MethodCall')([op1.data,op2.data])
        elif action is 'ADD':
            res = op1.data + op2.data
            expression = IR.BinaryExpression(op1,op2,IR.ADDOperator())
        elif action is 'GT':
            res = op1.data > op2.data
            expression = IR.BinaryExpression(op1,op2,IR.GTOperator())
        elif action is 'GTEQ':
            res = op1.data >= op2.data
            expression = IR.BinaryExpression(op1,op2,IR.GTEQOperator())
        elif action is 'AND':
            res = op1.data and op2.data
            expression = IR.BinaryExpression(op1,op2,IR.ANDOperator())
        elif action is 'OR':
            res = op1.data or op2.data
            expression = IR.BinaryExpression(op1,op2,IR.OROperator())
        elif action is 'MUL':
            res = op1.data * op2.data
            expression = IR.BinaryExpression(op1,op2,IR.MULOperator())
        elif action is 'DIV':
            res = op1.data / op2.data
            expression = IR.BinaryExpression(op1,op2,IR.DIVOperator())
        elif action is 'EQ':
            res = op1.data == op2.data
            expression = IR.BinaryExpression(op1,op2,IR.EQOperator())
        elif action is 'NEQ':
            res = op1.data != op2.data
            expression = IR.BinaryExpression(op1,op2,IR.NEQOperator())
        elif action is 'LT':
            res = op1.data < op2.data
            expression = IR.BinaryExpression(op1,op2,IR.LTOperator())
        elif action is 'LTEQ':
            res = op1.data <= op2.data
            expression = IR.BinaryExpression(op1,op2,IR.LTEQOperator())
        elif action is 'MAX':
            res = max(op1.data,op2.data)
            expression = getattr(IR, action+'MethodCall')([op1,op2])
        elif action is 'MIN':
            res = min(op1.data,op2.data)
            expression = getattr(IR, action+'MethodCall')([op1,op2])
        elif action is 'SUB':
            res = op1.data - op2.data
            expression = IR.BinaryExpression(op1,op2,IR.SUBOperator())
        else:
            raise NotImplementedError
        
        var = self.program_stack_push(res, False)
        self.current_instruction_intermediate.append(IR.OperationAssignmentStatement(var, expression))

    def exec_PUSH(self):
        for item in self.current_instruction.data:
            self.program_stack_push(item)

    # Don't execute any cfg-related instructions
    # This has the effect of "executing both branches".
    def exec_IF(self):
        pass
    def exec_EIF(self):
        pass
    def exec_ELSE(self):
        pass

    def exec_AA(self):#AdjustAngle
        self.program_stack_pop()

    def exec_ABS(self):#Absolute
        self.unary_operation('abs')

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
        self.unary_operation('ceil')

    def exec_CINDEX(self):#CopyXToTopStack
        index = self.program_stack[-1].data
        self.program_stack_pop()
        #the index start from 1
        top = self.program_stack[-index].data
        self.program_stack_push(top)

    def exec_CLEAR(self):#ClearStack
        self.program_stack = []

    def exec_DEBUG(self):#DebugCall
        self.program_stack_pop()

    def exec_DELTA(self):
        number = self.program_stack[-1].data
        loopValue = 1 + (2*number)
        self.program_stack_pop(loopValue)

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
        self.program_stack_push(depth)
    
    def exec_DIV(self):#Divide
        self.binary_operation('DIV')

    def exec_DUP(self):
        top = self.program_stack[-1].eval()
        self.program_stack_push(top)

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
        self.unary_operation('floor')

    def exec_GC(self):
        op1 = self.program_stack[-1]
        self.program_stack_pop()
        var = self.program_stack_push(dataType.AbstractValue(), False)
        self.current_instruction_intermediate.append(IR.GCMethodCall([op1],var))
    
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
        var = self.program_stack[-1]
        self.program_stack_pop()
        new_var = self.program_stack_push(dataType.EngineInfo(),False)
        self.current_instruction_intermediate.append(IR.GETINFOMethodCall([var],new_var))

    def exec_GPV(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.graphics_state['pv'] = (op1.data,op2.data)
        self.program_stack_pop(2)

    def exec_GFV(self):
        op1 = self.graphics_state['fv'][0]
        op2 = self.graphics_state['fv'][1]
        self.program_stack_push(op1)
        self.program_stack_push(op2)

    def exec_GT(self):
        self.binary_operation('GT')

    def exec_GTEQ(self):
        self.binary_operation('GTEQ')

    def exec_IDEF(self):
        #self.program_stack_pop()
        raise NotImplementedError

    def exec_INSTCTRL(self):
        selector = self.program_stack[-1].data
        value = self.program_stack[-2].data
        self.program_stack_pop(2)
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.InstructControl(selector), value))
    
    def exec_IP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        if len(self.program_stack)<loopValue:
            raise Exception("truetype: hinting: stack underflow")
        self.program_stack_pop(loopValue)

    def exec_ISECT(self):
        self.program_stack_pop(5)

    def exec_IUP(self): # drawing-only
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
        self.program_stack_push(res)

    def exec_MDAP(self):
        op = int(self.program_stack[-1].data)
        #assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)

    def exec_MDRP(self):
        op = self.program_stack[-1].data
        #assert isinstance(op, dataType.PointValue)
        self.program_stack_pop(1)

    def exec_MIAP(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop(2)

    def exec_MIN(self):
        self.binary_operation('MIN')

    def exec_MINDEX(self):
        index = self.program_stack[-1].data
        self.program_stack_pop()
        #the index start from 1
        top = self.program_stack[-index].data
        del self.program_stack[-index]
        self.program_stack_push(top)

    def exec_MIRP(self):
        self.program_stack_pop(2)

    def exec_MPPEM(self):
        if self.graphics_state['pv'] == (0, 1):
            self.program_stack_push(dataType.PPEM_Y())
        else:
            self.program_stack_push(dataType.PPEM_X())
    
    def exec_MPS(self):
        self.program_stack_push(dataType.PointSize())

    def exec_MSIRP(self):
        self.program_stack_pop(2)

    def exec_MUL(self):
        self.binary_operation('MUL')

    def exec_NEG(self):
        op = self.program_stack[-1].data
        if isinstance(op, dataType.AbstractValue):
            pass
        else:
            self.program_stack_pop()
            self.program_stack_push(-op)

    def exec_NEQ(self):
        self.binary_operation('NEQ')

    def exec_NOT(self):
        self.unary_operation('not')

    def exec_NROUND(self):
        pass

    def exec_ODD(self):
        raise NotImplementedError

    def exec_OR(self):
        self.binary_operation('OR')

    def exec_POP(self):
        self.program_stack_pop()

    def exec_RCVT(self):
        op = self.program_stack_pop().eval()
        if isinstance(op, dataType.AbstractValue):
            res = IR.ReadFromIndexedStorage("cvt_table", op)
        else:
            res = self.cvt[op]
        self.program_stack_push(res)

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
        var = self.program_stack_pop()
        new_var = self.program_stack_push(dataType.F26Dot6(var), False)
        self.current_instruction_intermediate.append(IR.ROUNDMethodCall([var],new_var))

    def exec_RS(self):
        op = self.program_stack[-1].data
        self.program_stack_pop()
        res = self.storage_area[op]
        self.program_stack_push(res)
        
    def exec_RTDG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_DG()))
        pass
    def exec_RTG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_G()))
        pass
    def exec_RTHG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_HG()))
        pass
    def exec_RUTG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_UG()))
        pass

    def exec_S45ROUND(self):
        self.program_stack_pop()

    def exec_SANGW(self):
        self.program_stack_pop()

    def exec_SCANCTRL(self):
        value = self.program_stack[-1].data
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.ScanControl(), value))
 
    def exec_SCANTYPE(self):
        value = self.program_stack[-1].data
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.ScanType(), value))

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
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['fv'] = (0, 1)
        if data == 1:
            self.graphics_state['fv'] = (1, 0)
           
    def exec_SFVTL(self):#Set Freedom Vector To Line
        self.program_stack_pop(2)

    def exec_SFVTPV(self):#Set Freedom Vector To Projection Vector
        self.graphics_state['fv'] = self.graphics_state['pv']

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
        self.graphics_state['loop'] = self.program_stack[-1].data
        self.program_stack_pop()

    def exec_SMD(self):
        self.program_stack_pop()

    def exec_SPVFS(self):
        self.program_stack_pop(2)

    def exec_SPVTCA(self):
        data = int(self.current_instruction.data[0])
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
        data = int(self.current_instruction.data[0])
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

        return [op1.data,op2.data,op1,op2]

    def exec_WS(self):
        res = self.getOpandVar()
        self.current_instruction_intermediate.append(IR.WriteStorageStatement(res[2],res[3]))

        assert not isinstance(res[0], dataType.AbstractValue)

        self.storage_area[res[0]] = res[1]

    def exec_EQ(self):
        self.binary_operation('EQ')
       
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
        data = self.program_stack[-1].data
        self.program_stack_pop()
        self.graphics_state['controlValueCutIn'] = data
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.SingleWidthCutIn(), self.stack_top_name()))
    
    def exec_SDB(self):
        self.program_stack_pop()

    def exec_CALL(self):
        var = self.program_stack[-1]
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CallStatement(var))

    def execute_current_instruction(self):
        self.current_instruction_intermediate = []
        getattr(self,"exec_"+self.current_instruction.mnemonic)()
        return self.current_instruction_intermediate

def setGSDefaults():
    intermediateCodes = []
    intermediateCodes.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('true')))
    intermediateCodes.append(IR.CopyStatement(IR.ScanControl(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.ScanType(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.SingleWidthCutIn(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.SingleWidthValue(),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.FreedomVector(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.ProjectionVector(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.LoopValue(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.InstructControl(IR.Constant(0)),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.InstructControl(IR.Constant(1)),IR.Constant(0)))
    intermediateCodes.append(IR.CopyStatement(IR.MinimumDistance(),IR.Constant(1)))
    intermediateCodes.append(IR.CopyStatement(IR.RoundState(),dataType.RoundState_G()))
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

    As a side effect, puts intermediate code in field "intermediateCodes".

    This class manages the program pointer like jump to function call
    """
    def __init__(self,font):
        self.font = font
        self.program = None
        self.pc = None
        self.maximum_stack_depth = 0
        self.conditionBlock = None
        self.call_stack = []
        self.stored_environments = {}
        self.if_else = None
        # generated as a side effect:
        self.intermediateCodes = []
        self.global_function_table = {}

    class If_else_stack(object):
        def __init__(self, IR, env, state):
            self.IR = IR
            self.env = env
            self.state = state

    def stack_depth(self):
        return self.environment.stack_depth()

    def appendIntermediateCode(self, ins):
        if len(self.call_stack) == 0:
            if len(self.if_else.IR) > 0:
                self.if_else.IR[-1].appendStatements(ins)
            else:
                self.intermediateCodes.extend(ins)

    def execute_CALL(self):
        callee = self.environment.program_stack[-1].eval()
        assert not isinstance(callee, dataType.AbstractValue)

        # update call graph counts
        self.program.call_function_set.append(callee)
        if callee not in self.global_function_table:
            self.global_function_table[callee] = 1
        else:
            self.global_function_table[callee] += 1
        logger.info('ADD CALL SET: %s | %s' % (callee, self.program.call_function_set))

        # execute the call instruction itself
        self.environment.set_current_instruction(self.pc)
        self.environment.execute_current_instruction()

        logger.info("stack depth into call is %s", self.stack_depth())
        self.environment.minimum_stack_depth = self.stack_depth()
        # set call stack & jump
        # yuck should regularize the CFG to avoid needing this hack
        if (len(self.pc.successors) == 0):
            self.call_stack.append((callee, None, self.stack_depth(),
                                    self.stored_environments, self.if_else))
        else:
            self.call_stack.append((callee, self.pc.successors[0], self.stack_depth(),
                                    self.stored_environments,
                                    self.if_else))
        self.if_else = self.If_else_stack([], [], [])
        self.pc = self.font.function_table[callee].start()
        self.stored_environments = {}
        
        logger.info("jump to callee function, starting with "+self.pc.mnemonic)

    def execute(self,tag):
        self.environment = Environment(self.font, tag)
        self.program = self.font.programs[tag]
        self.pc = self.program.start()

        self.if_else = self.If_else_stack([], [], [])
        self.intermediateCodes = setGSDefaults()
        self.environment.minimum_stack_depth = 0

        while self.pc is not None:
            if self.pc.data is not None:
                logger.info("[pc] %s->%s|%s",self.pc.id,self.pc.mnemonic,self.pc.data)
            else:
                logger.info("[pc] %s->%s",self.pc.id,self.pc.mnemonic)
            logger.info("succs are %s", self.pc.successors)
            logger.info("call_stack is %s", self.call_stack)

            if self.pc.mnemonic == 'CALL':
                self.execute_CALL()
                continue

            if self.pc.mnemonic == 'IF':
                if len(self.if_else.env) > 0 and self.if_else.env[-1][0] == self.pc:
                    # back at the if and ready to traverse next branch...
                    top_if = self.if_else.env[-1][0]
                    if top_if.id not in self.stored_environments:
                        logger.warn("STORE %s program state ", top_if.id)
                        self.stored_environments[top_if.id] = [self.environment]
                    else:
                        logger.warn("APPEND %s program state ", top_if.id)
                        self.stored_environments[top_if.id].append(self.environment)
                        self.stored_environments[top_if.id][0].merge(self.stored_environments[top_if.id][1])
                        self.environment = self.stored_environments[top_if.id][0]
                else:
                    # first time round at this if statement...
                    cond = self.environment.program_stack.pop()
                    newBlock = IR.IfElseBlock(IR.Variable(self.environment.stack_top_name(), cond),
                                              len(self.if_else.env) + 1)

                    environment_copy = self.environment.make_copy(self.font)
                    self.if_else.IR.append(newBlock)
                    self.if_else.env.append((self.pc, environment_copy))
                    self.if_else.state.append(0)

            if self.pc.mnemonic == 'ELSE':
                block = self.if_else.IR[-1]
                block.mode = 'ELSE'

            if self.pc.mnemonic == 'EIF':
                assert len(self.if_else.IR) > 0
                block = self.if_else.IR.pop()
                self.appendIntermediateCode([block])

            self.environment.set_current_instruction(self.pc)
            intermediateCodes = self.environment.execute_current_instruction()
            if self.stack_depth() > self.maximum_stack_depth:
                self.maximum_stack_depth = self.stack_depth()

            self.appendIntermediateCode(intermediateCodes)

            # normal case: 1 succ
            if len(self.pc.successors) == 1:
                self.pc = self.pc.successors[0]
            # multiple succs, store the alternate succ for later
            elif len(self.pc.successors) > 1:
                self.pc = self.pc.successors[self.if_else.state[-1]]
                if self.if_else.state[-1]>0 and (self.pc.mnemonic != 'EIF' or self.if_else.state[-1] != 2):
                    logger.warn("program environment recover to")
                    self.environment = self.if_else.env[-1][1]
                    logger.info(self.environment)
                logger.info("traverse another branch %s->%s", self.pc.id, self.pc.mnemonic)
                if self.pc.mnemonic == 'EIF':
                    self.if_else.env.pop()
                    self.if_else.state.pop()
                else:
                    self.if_else.state[-1] = self.if_else.state[-1] + 1
            # ok, no succs
            else:
                assert len(self.pc.successors) == 0
                # reached end of function, still have if/else succs to explore
                if len(self.if_else.env) > 0:
                    # return to the closest enclosing IF
                    self.pc = self.if_else.env[-1][0]
                    logger.info("program pointer back to %s %s", str(self.pc),str(self.pc.id))
                # reached end of function, but we're still in a call
                elif len(self.call_stack) > 0:
                    logger.info("call stack is %s", self.call_stack)
                    (callee, self.pc, stack_depth_upon_call,
                     self.stored_environments, self.if_else) = self.call_stack.pop()

                    stack_used = stack_depth_upon_call - self.environment.minimum_stack_depth
                    stack_additional = self.stack_depth() - stack_depth_upon_call

                    call_args = '('
                    for i in range(stack_used):
                        if i > 0:
                            call_args += ', '
                        call_args += identifierGenerator.generateIdentifier(tag, stack_depth_upon_call - i - 1)
                    call_args += ')'

                    call_rv = ''
                    if stack_additional > 0:
                        call_rv += '('
                        for i in range(stack_additional):
                            if i > 0:
                                call_rv += ', '
                            call_rv += identifierGenerator.generateIdentifier(tag, stack_depth_upon_call + i)
                        call_rv += ') := '

                    self.appendIntermediateCode(['%sCALL %s%s' % (call_rv, str(callee), call_args)])

                    logger.info("pop call stack, next is %s", str(self.pc))
                    logger.info("stack used was %d", stack_used)
                    logger.info("new entries on stack are %d", stack_additional)
                # ok, we really are all done here!
                else:
                    assert len(self.if_else.env)==0
                    self.pc = None

        for intermediateCode in self.intermediateCodes:
            print intermediateCode
