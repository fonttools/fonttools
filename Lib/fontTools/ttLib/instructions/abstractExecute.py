from fontTools.ttLib.data import dataType
import logging
import copy
import IntermediateCode as IR
logger = logging.getLogger(" ")
class IdentifierGenerator(object):
    def generateIdentifier(self, tag, number):
        return '$' + tag + '_' + str(number)

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

    The cvt consists of a dict mapping locations to 16-bit signed
    integers.

    The storage_area consists of a dict mapping locations to 32-bit numbers
    [again, same comment as for cvt_table].

    The program stack abstractly represents the program stack. This is the
    critical part of the abstract state, since TrueType consists of an
    stack-based virtual machine.

    """
    def __init__(self, bytecodeContainer, tag):
        self.bytecodeContainer = bytecodeContainer
        # cvt: location -> Value
        self.cvt = copy.copy(bytecodeContainer.cvt_table)
        self.tag = tag
        # storage_area: location -> Value
        self.storage_area = {}
        self.set_graphics_state_to_default()
        # this is the TT VM stack, not the call stack
        self.program_stack = []
        self.minimum_stack_depth = None
        self.current_instruction = None
        self.current_instruction_intermediate = []
        self.keep_abstract = True

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

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'bytecodeContainer':
                setattr(result, k, copy.copy(v))
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

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

    def write_storage_area(self, index, value):
        self.storage_area[index] = value

    def read_storage_area(self, index):
        return self.storage_area[index]

    def stack_top_name(self, offset = 0):
        return identifierGenerator.generateIdentifier(self.tag, self.stack_depth() + offset)

    def generate_assign_variable(self, var, data):
        self.current_instruction_intermediate.append(IR.CopyStatement(var, data))

    def stack_depth(self):
        return len(self.program_stack)

    def program_stack_push(self, data = None, assign = True, customVar = None):
        if customVar is not None:
            tempVariable = customVar
        else:
            tempVariableName = self.stack_top_name(1)
            tempVariable = IR.Variable(tempVariableName, data)
        if data is not None and assign:
            self.generate_assign_variable(tempVariable, data)
        self.program_stack.append(tempVariable)
        return tempVariable

    def program_stack_pop(self):
        val = self.program_stack.pop()
        if self.stack_depth() < self.minimum_stack_depth:
            self.minimum_stack_depth = self.stack_depth()
        return val

    def program_stack_pop_many(self, num):
        last_val = []
        for i in range(num):
            last_val.append(self.program_stack_pop())
        if self.stack_depth() < self.minimum_stack_depth:
            self.minimum_stack_depth = self.stack_depth()
        return last_val

    def replace_locals_with_formals(self):
        new_stack = []
        stack_depth = len(self.program_stack)
        for i in range(0, len(self.program_stack)):
            s = self.program_stack[i]
            if isinstance(s, IR.Variable):
                new_stack.append(IR.Variable("arg$%d" % (stack_depth - i - 1), s.data))
            else:
                new_stack.append(s)
        self.program_stack = new_stack

    def unary_operation(self, action):
        v_name = self.stack_top_name()
        arg = self.program_stack_pop()
        v = IR.Variable(v_name, arg)

        if action is 'ceil':
            e = IR.CEILMethodCall([arg])
        elif action is 'floor':
            e = IR.FLOORMethodCall([arg])
        elif action is 'abs':
            e = IR.ABSMethodCall([arg])
        elif action is 'not':
            e = IR.NOTMethodCall([arg])
        res = e.eval(self.keep_abstract)
        self.program_stack_push(res, False)
        self.current_instruction_intermediate.append(IR.OperationAssignmentStatement(v, res))
        return res

    def binary_operation(self, action):
        op1_var = self.stack_top_name()
        op1_val = self.program_stack_pop()
        op2_var = self.stack_top_name()
        op2_val = self.program_stack_pop()
        op1 = op1_val.eval(self.keep_abstract)
        op2 = op2_val.eval(self.keep_abstract)

        expression = None
        if action is 'MAX' or action is 'MIN':
            e = IR.PrefixBinaryExpression
        else:
            e = IR.InfixBinaryExpression
        if isinstance(op1,dataType.AbstractValue) or isinstance(op2,dataType.AbstractValue):
            res = dataType.Expression(op1, op2, action)
            expression = e(op1_var, op2_var, getattr(IR, action+'Operator')())
        elif action is 'ADD':
            res = op1 + op2
            expression = e(op1,op2,IR.ADDOperator())
        elif action is 'SUB':
            res = op1 - op2
            expression = e(op1,op2,IR.SUBOperator())
        elif action is 'GT':
            res = op1 > op2
            expression = e(op1,op2,IR.GTOperator())
        elif action is 'GTEQ':
            res = op1 >= op2
            expression = e(op1,op2,IR.GTEQOperator())
        elif action is 'AND':
            res = op1 and op2
            expression = e(op1,op2,IR.ANDOperator())
        elif action is 'OR':
            res = op1 or op2
            expression = e(op1,op2,IR.OROperator())
        elif action is 'MUL':
            res = op1 * op2
            expression = e(op1,op2,IR.MULOperator())
        elif action is 'DIV':
            res = op1 / op2
            expression = e(op1,op2,IR.DIVOperator())
        elif action is 'EQ':
            res = op1 == op2
            expression = e(op1,op2,IR.EQOperator())
        elif action is 'NEQ':
            res = op1 != op2
            expression = e(op1,op2,IR.NEQOperator())
        elif action is 'LT':
            res = op1 < op2
            expression = e(op1,op2,IR.LTOperator())
        elif action is 'LTEQ':
            res = op1 <= op2
            expression = e(op1,op2,IR.LTEQOperator())
        elif action is 'MAX':
            res = max(op1,op2)
            expression = e(op1,op2,IR.MAXOperator())
        elif action is 'MIN':
            res = min(op1,op2)
            expression = e(op1,op2,IR.MINOperator())
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
        raise NotImplementedError

    def exec_ABS(self):#Absolute
        self.unary_operation('abs')

    def exec_ADD(self):
        self.binary_operation('ADD')
        
    def exec_ALIGNPTS(self):
        '''
        move to points, has no further effect on the stack
        '''
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_ALIGNRP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        assert len(self.program_stack) >= loopValue, "IP: stack underflow"
        pts = self.program_stack_pop_many(loopValue)
        self.current_instruction_intermediate.append(IR.ALIGNRPMethodCall(pts))

    def exec_AND(self):
        self.binary_operation('AND')

    def exec_CEILING(self):
        self.unary_operation('ceil')

    def exec_CINDEX(self):#CopyXToTopStack
        # index starts from 1
        index = self.program_stack_pop().eval(False)
        new_top = self.program_stack[-index].eval(self.keep_abstract)
        self.program_stack_push(new_top)

    def exec_CLEAR(self):#ClearStack
        self.program_stack = []

    def exec_DEBUG(self):#DebugCall
        self.program_stack_pop()
        raise NotImplementedError

    def exec_DELTA(self, op):
        # we need this number concretely to proceed
        number = self.program_stack_pop().eval(False)
        assert not isinstance(number, dataType.AbstractValue)
        loopValue = (2*number)
        args = self.program_stack_pop_many(loopValue)
        self.current_instruction_intermediate.append(IR.DELTAMethodCall(op, args))

    def exec_DELTAC1(self):#DeltaExceptionC1
        self.exec_DELTA("C1")

    def exec_DELTAC2(self):#DeltaExceptionC2
        self.exec_DELTA("C2")

    def exec_DELTAC3(self):#DeltaExceptionC3
        self.exec_DELTA("C3")

    def exec_DELTAP1(self):#DeltaExceptionC1
        self.exec_DELTA("P1")

    def exec_DELTAP2(self):#DeltaExceptionC2
        self.exec_DELTA("P2")

    def exec_DELTAP3(self):#DeltaExceptionC3
        self.exec_DELTA("P3")

    def exec_DEPTH(self):#GetDepthStack
        # is incorrect in the presence of method calls
        depth = len(self.program_stack)
        self.program_stack_push(depth)
        raise NotImplementedError
    
    def exec_DIV(self):#Divide
        self.binary_operation('DIV')

    def exec_DUP(self):
        v = IR.Variable(self.stack_top_name())
        top = self.program_stack[-1].eval(self.keep_abstract)
        self.program_stack_push(top, False)
        vnew = IR.Variable(self.stack_top_name())
        self.current_instruction_intermediate.append(IR.CopyStatement(vnew, v))

    def exec_FLIPOFF(self):
        self.graphics_state['autoFlip'] = False
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('false')))

    def exec_FLIPON(self):
        self.graphics_state['autoFlip'] = True
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('true')))

    def exec_FLIPPT(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        assert len(self.program_stack) >= loopValue, "IP: stack underflow"
        self.program_stack_pop_many(loopValue)
        raise NotImplementedError

    def exec_FLIPRGOFF(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_FLIPRGON(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_FLOOR(self):
        self.unary_operation('floor')

    def exec_GC(self):
        arg = self.program_stack_pop()
        var = self.program_stack_push(dataType.AbstractValue(), False)
        self.current_instruction_intermediate.append(IR.GCMethodCall([arg],var))
    
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
        v = IR.Variable(self.stack_top_name())
        op = self.program_stack_pop()
        e = IR.GETINFOMethodCall([v])
        res = e.eval(self.keep_abstract)
        self.program_stack_push(v, False)
        self.current_instruction_intermediate.append(IR.OperationAssignmentStatement(v, res))

    def exec_GPV(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.graphics_state['pv'] = (op1.data,op2.data)
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_GFV(self):
        op1 = self.graphics_state['fv'][0]
        op2 = self.graphics_state['fv'][1]
        self.program_stack_push(op1)
        self.program_stack_push(op2)
        raise NotImplementedError

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
        self.program_stack_pop_many(2)
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.InstructControl(selector), value))
    
    def exec_IP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        assert len(self.program_stack) >= loopValue, "IP: stack underflow"
        pts = self.program_stack_pop_many(loopValue)
        self.current_instruction_intermediate.append(IR.IPMethodCall(pts))

    def exec_ISECT(self):
        self.program_stack_pop_many(5)
        raise NotImplementedError

    def exec_IUP(self): # drawing-only
        self.current_instruction_intermediate.append(IR.IUPMethodCall(self.current_instruction.data[0]))

    def fetch_body_for_tag(self, tag):
        fpgm_prefix = "fpgm_"
        if tag.startswith(fpgm_prefix):
            fn = int(tag[len(fpgm_prefix):len(tag)-1])
            return self.bytecodeContainer.function_table[fn].body
        else:
            return self.bytecodeContainer.tag_to_programs[self.tag].body

    def adjust_succ_for_relative_jump(self, arg, only_succ):
        # now we need to find the instructions and set the PC
        assert not isinstance(arg, dataType.AbstractValue)
        ins = self.fetch_body_for_tag(self.tag).instructions
        pc = 0
        # note use of 'is' rather than normal equality
        for i in range(len(ins)):
            if self.current_instruction is ins[i]:
                break
            pc += 1
        assert pc < len(ins)

        target = ins[pc+arg]
        if only_succ:
            self.current_instruction.successors = []
        if not target in self.current_instruction.successors:
            self.current_instruction.successors.append(target)

    def exec_JMPR(self):
        arg = self.program_stack_pop().eval(False)
        assert not isinstance(arg, dataType.AbstractValue)
        self.adjust_succ_for_relative_jump(arg, True)
        # todo also emit JMPR etc
    def exec_JROF(self):
        e = self.program_stack_pop().eval(self.keep_abstract)
        arg = self.program_stack_pop().eval(False)
        assert not isinstance(arg, dataType.AbstractValue)
        self.adjust_succ_for_relative_jump(arg, False)
    def exec_JROT(self):
        e = self.program_stack_pop().eval(self.keep_abstract)
        arg = self.program_stack_pop().eval(False)
        assert not isinstance(arg, dataType.AbstractValue)
        self.adjust_succ_for_relative_jump(arg, False)

    def exec_LT(self):
        self.binary_operation('LT')

    def exec_LTEQ(self):
        self.binary_operation('LTEQ')

    def exec_MAX(self):
        self.binary_operation('MAX')

    def exec_MD(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop_many(2)
        #assert isinstance(op1, dataType.PointValue) and (op1, dataType.PointValue)
        res = dataType.Distance()
        self.program_stack_push(res)
        raise NotImplementedError

    def exec_MDAP(self):
        arg = self.program_stack_pop().eval(self.keep_abstract)
        self.current_instruction_intermediate.append(IR.MDAPMethodCall(self.current_instruction.data[0], [arg]))

    def exec_MDRP(self):
        arg = self.program_stack_pop().eval(self.keep_abstract)
        self.current_instruction_intermediate.append(IR.MDAPMethodCall(self.current_instruction.data[0], [arg]))

    def exec_MIAP(self):
        args = self.program_stack_pop_many(2)
        self.current_instruction_intermediate.append(IR.MIAPMethodCall(self.current_instruction.data[0], args))

    def exec_MIN(self):
        self.binary_operation('MIN')

    def exec_MINDEX(self):
        index = self.program_stack_pop().eval(False)
        assert not isinstance(index, dataType.AbstractValue)
        top = self.program_stack[-index].eval(self.keep_abstract)
        del self.program_stack[-index]
        self.program_stack_push(top)
        raise NotImplementedError

    def exec_MIRP(self):
        args = self.program_stack_pop_many(2)
        self.current_instruction_intermediate.append(IR.MIRPMethodCall(self.current_instruction.data[0], args))

    def exec_MPPEM(self):
        if self.graphics_state['pv'] == (0, 1):
            self.program_stack_push(dataType.PPEM_Y())
        else:
            self.program_stack_push(dataType.PPEM_X())
    
    def exec_MPS(self):
        self.program_stack_push(dataType.PointSize())

    def exec_MSIRP(self):
        args = self.program_stack_pop_many(2)
        self.current_instruction_intermediate.append(IR.MSIRPMethodCall(self.current_instruction.data[0], args))

    def exec_MUL(self):
        self.binary_operation('MUL')

    def exec_NEG(self):
        op = self.program_stack[-1].data
        if isinstance(op, dataType.AbstractValue):
            # xxx can do better here
            raise NotImplementedError
        else:
            self.program_stack_pop()
            self.program_stack_push(-op)

    def exec_NEQ(self):
        self.binary_operation('NEQ')

    def exec_NOT(self):
        self.unary_operation('not')

    def exec_NROUND(self):
        raise NotImplementedError

    def exec_ODD(self):
        raise NotImplementedError

    def exec_OR(self):
        self.binary_operation('OR')

    def exec_POP(self):
        self.program_stack_pop()

    def exec_RCVT(self):
        op = self.program_stack_pop().eval(self.keep_abstract)
        # XXX should be done from dataType & eval
        # or, we could accept that we basically never really know the CVT table.
        res_var = IR.ReadFromIndexedStorage("cvt_table", op)
        if self.keep_abstract or isinstance(op, dataType.AbstractValue):
            res = IR.ReadFromIndexedStorage("cvt_table", op)
        else:
            res = self.cvt[op]
        self.program_stack_push(res, False)
        self.current_instruction_intermediate.append(IR.CopyStatement
                                                     (IR.Variable(self.stack_top_name()),
                                                      res_var))

    def exec_RDTG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_DTG()))

    def exec_ROFF(self):
        raise NotImplementedError

    def exec_ROLL(self):
        tmp = self.program_stack[-1]
        self.program_stack[-1] = self.program_stack[-3]
        self.program_stack[-3] = self.program_stack[-2]
        self.program_stack[-2] = tmp

        tmp_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth() + 1)
        arg1_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth())
        arg2_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth() - 1)
        arg3_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth() - 2)

        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(tmp_name),
                                                                      IR.Variable(arg1_name)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(arg1_name),
                                                                      IR.Variable(arg3_name)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(arg3_name),
                                                                      IR.Variable(arg2_name)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(arg2_name),
                                                                      IR.Variable(tmp_name)))

    def exec_ROUND(self):
        var = self.program_stack_pop()
        res = self.program_stack_push(dataType.F26Dot6(var), False)
        self.current_instruction_intermediate.append(IR.ROUNDMethodCall
                                                     (self.current_instruction.data[0],
                                                      [var], res))

    def exec_RS(self):
        arg = self.program_stack_pop().eval(self.keep_abstract)
        if self.keep_abstract:
            self.program_stack_push(dataType.AbstractValue(), False)
            self.current_instruction_intermediate.append(
                IR.CopyStatement(IR.Variable(self.stack_top_name()),
                                 IR.ReadFromIndexedStorage("storage_area", arg)))
        else:
            res = self.read_storage_area(op)
            self.program_stack_push(res)
        
    def exec_RTDG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_DG()))
    def exec_RTG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_G()))
    def exec_RTHG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_HG()))
    def exec_RUTG(self):
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.RoundState(), dataType.RoundState_UG()))

    def exec_S45ROUND(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SANGW(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SCANCTRL(self):
        value = self.program_stack[-1].data
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.ScanControl(), value))
 
    def exec_SCANTYPE(self):
        value = self.program_stack[-1].data
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.ScanType(), value))

    def exec_SCFS(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SCVTCI(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SDB(self):
        arg = self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.SDBMethodCall([arg]))

    def exec_SDPVTL(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SDS(self):
        arg = self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.SDSMethodCall([arg]))

    def exec_SFVFS(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SFVTCA(self):#Set Freedom Vector To Coordinate Axis
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['fv'] = (0, 1)
        if data == 1:
            self.graphics_state['fv'] = (1, 0)
        raise NotImplementedError
           
    def exec_SFVTL(self):#Set Freedom Vector To Line
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SFVTPV(self):#Set Freedom Vector To Projection Vector
        self.graphics_state['fv'] = self.graphics_state['pv']
        raise NotImplementedError

    def exec_SHC(self):
        arg = self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.SHCMethodCall(self.current_instruction.data[0], [arg]))
 
    def exec_SHP(self):
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        assert len(self.program_stack) >= loopValue, "IP: stack underflow"
        pts = self.program_stack_pop_many(loopValue)
        self.current_instruction_intermediate.append(IR.SHPMethodCall(pts))

    def exec_SHPIX(self):
        self.program_stack_pop()
        loopValue = self.graphics_state['loop']
        self.graphics_state['loop'] = 1
        assert len(self.program_stack) >= loopValue, "IP: stack underflow"
        pts = self.program_stack_pop_many(loopValue)
        self.current_instruction_intermediate.append(IR.SHPIXMethodCall(pts))

    def exec_SHZ(self):
        self.program_stack_pop()
        raise NotImplementedError
  
    def exec_SLOOP(self):
        self.graphics_state['loop'] = self.program_stack[-1].data
        arg = self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.SLOOPMethodCall([arg]))

    def exec_SMD(self):
        arg = self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.SMDMethodCall([arg]))

    def exec_SPVFS(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SPVTCA(self):
        data = int(self.current_instruction.data[0])
        assert (data is 1 or data is 0)
        if data == 0:
            self.graphics_state['pv'] = (0, 1)
            self.graphics_state['dv'] = (0, 1)
        if data == 1:
            self.graphics_state['pv'] = (1, 0)
            self.graphics_state['dv'] = (1, 0)
        raise NotImplementedError

    def exec_SPVTL(self):
        self.program_stack_pop_many()
        raise NotImplementedError

    def exec_SROUND(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SSW(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SSWCI(self):
        self.program_stack_pop()
        raise NotImplementedError

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

        tmp_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth() + 1)
        arg1_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth())
        arg2_name = identifierGenerator.generateIdentifier(self.tag, self.stack_depth()-1)

        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(tmp_name),
                                                                      IR.Variable(arg1_name)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(arg1_name),
                                                                      IR.Variable(arg2_name)))
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.Variable(arg2_name),
                                                                      IR.Variable(tmp_name)))

    def exec_SZP0(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SZP1(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SZP2(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SZPS(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_UTP(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_WCVTF(self):
        self.exec_WCVTP()

    def exec_WCVTP(self):
        res = self.getOpandVar()
        self.cvt[res[0]] = res[1]
        self.current_instruction_intermediate.append(IR.CVTStorageStatement(res[2],res[3]))
       
    def getOpandVar(self):
        op1 = self.program_stack[-2]
        op2 = self.program_stack[-1]
        self.program_stack_pop_many(2)

        return [op1.eval(self.keep_abstract),op2.eval(self.keep_abstract),op1,op2]

    def exec_WS(self):
        res = self.getOpandVar()
        self.current_instruction_intermediate.append(IR.WriteStorageStatement(res[2],res[3]))
        self.write_storage_area(res[0], res[1])

    def exec_EQ(self):
        self.binary_operation('EQ')
       
    def exec_SRP(self,index):#SetRefPoint
        #self.graphics_state['rp'][index] = self.program_stack[-1]
        return self.program_stack_pop()

    def exec_SRP0(self):
        arg = self.exec_SRP(0)
        self.current_instruction_intermediate.append(IR.SRP0MethodCall([arg]))
    
    def exec_SRP1(self):
        arg = self.exec_SRP(1)
        self.current_instruction_intermediate.append(IR.SRP1MethodCall([arg]))

    def exec_SRP2(self):
        arg = self.exec_SRP(2)
        self.current_instruction_intermediate.append(IR.SRP2MethodCall([arg]))

    def exec_S45ROUND(self):
        self.program_stack_pop()
        raise NotImplementedError

    def exec_SANGW(self):
        self.program_stack_pop()
        raise NotImplementedError
    
    def exec_SCFS(self):
        self.program_stack_pop_many(2)
        raise NotImplementedError

    def exec_SCVTCI(self):
        arg_name = self.stack_top_name()
        data = self.program_stack[-1].data
        self.program_stack_pop()
        self.graphics_state['controlValueCutIn'] = data
        self.current_instruction_intermediate.append(IR.CopyStatement(IR.SingleWidthCutIn(), arg_name))
    
    def exec_LOOPCALL(self):
        fn = self.program_stack_pop().eval(False)
        count = self.program_stack_pop().eval(False)
        self.current_instruction_intermediate.append(IR.LoopCallStatement(fn, count))

    def exec_CALL(self):
        var = self.program_stack[-1]
        self.program_stack_pop()
        self.current_instruction_intermediate.append(IR.CallStatement(var))

    def execute_current_instruction(self, ins):
        self.current_instruction_intermediate = []
        self.current_instruction = ins
        getattr(self,"exec_"+self.current_instruction.mnemonic)()
        return self.current_instruction_intermediate

class Executor(object):
    """
    Given a TrueType instruction, abstractly transform the global state.

    Produces a new global state accounting for the effects of that
    instruction. Modifies the stack, CVT table, and storage area.

    As a side effect, puts intermediate code in field "intermediateCodes".
    """
    def __init__(self,bc):
        self.bytecodeContainer = bc
        self.environment = Environment(bc, "")
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
        self.visited_functions = set()

    def initialize_graphics_state(self):
        self.intermediateCodes = []
        self.intermediateCodes.append(IR.CopyStatement(IR.AutoFlip(),IR.Boolean('true')))
        self.intermediateCodes.append(IR.CopyStatement(IR.ScanControl(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.ScanType(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.SingleWidthCutIn(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.SingleWidthValue(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.FreedomVector(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.ProjectionVector(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.LoopValue(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.InstructControl(IR.Constant(0)),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.InstructControl(IR.Constant(1)),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.MinimumDistance(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.RoundState(),dataType.RoundState_G()))
        self.intermediateCodes.append(IR.CopyStatement(IR.ZP0(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.ZP1(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.ZP2(),IR.Constant(1)))
        self.intermediateCodes.append(IR.CopyStatement(IR.RP0(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.RP1(),IR.Constant(0)))
        self.intermediateCodes.append(IR.CopyStatement(IR.RP2(),IR.Constant(0)))

    class If_else_stack(object):
        def __init__(self, IR, env, state):
            self.IR = IR
            self.env = env
            self.state = state

    def stack_depth(self):
        return self.environment.stack_depth()

    def appendIntermediateCode(self, ins):
        if len(self.if_else.IR) > 0:
            self.if_else.IR[-1].appendStatements(ins)
        else:
            self.intermediateCodes.extend(ins)

    def execute_LOOPCALL(self):
        count = self.environment.program_stack[-2].eval(False)
        if isinstance(count, dataType.AbstractValue):
            # oops. execute once, hope it doesn't modify the stack.
            # we could also record the effects & replay them if it did.
            self.execute_CALL()
        else:
            for i in range(count):
                self.execute_CALL()

    def execute_CALL(self):
        # actually we *always* want to get the concrete callee
        callee = self.environment.program_stack[-1].eval(False)
        assert not isinstance(callee, dataType.AbstractValue)

        # update call graph counts
        self.program.call_function_set.append(callee)
        if callee not in self.global_function_table:
            self.global_function_table[callee] = 1
        else:
            self.global_function_table[callee] += 1

        # execute the call instruction itself
        self.environment.execute_current_instruction(self.pc)

        self.environment.minimum_stack_depth = self.stack_depth()
        # set call stack & jump
        # yuck should regularize the CFG to avoid needing this hack
        if (len(self.pc.successors) == 0):
            succ = None
        else:
            succ = self.pc.successors[0]
        self.call_stack.append((callee, succ, self.intermediateCodes,
                                self.environment.tag, copy.copy(self.environment.program_stack),
                                self.stored_environments, self.if_else))
        self.if_else = self.If_else_stack([], [], [])
        logger.info("calling function %d" % callee)
        self.pc = self.bytecodeContainer.function_table[callee].start()
        self.intermediateCodes = []
        self.environment.tag = "fpgm_%s" % callee
        self.environment.replace_locals_with_formals()
        self.stored_environments = {}

    def execute(self, tag):
        logger.info("execute; tag is %s", tag)
        self.environment.tag = tag
        self.program = self.bytecodeContainer.tag_to_programs[tag]
        self.pc = self.program.start()

        self.if_else = self.If_else_stack([], [], [])
        self.intermediateCodes = []
        self.environment.minimum_stack_depth = 0

        if tag == 'prep':
            self.initialize_graphics_state()

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
            elif self.pc.mnemonic == 'LOOPCALL':
                self.execute_LOOPCALL()
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
                    logger.info("entering if block for %s, stack height is %d" % (str(cond), self.stack_depth()))
                    newBlock = IR.IfElseBlock(cond,
                                              len(self.if_else.env) + 1)

                    environment_copy = self.environment.make_copy(self.bytecodeContainer)
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

            intermediateCodes = self.environment.execute_current_instruction(self.pc)
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
                    if self.environment.tag in self.visited_functions:
                        # assert that self.intermediateCodes == bytecodeContainer.IRs[tag]
                        pass
                    else:
                        self.bytecodeContainer.IRs[self.environment.tag] = self.intermediateCodes
                    self.visited_functions.add(self.environment.tag)
                    (callee, self.pc, self.intermediateCodes, self.environment.tag,
                     caller_program_stack, self.stored_environments,
                     self.if_else) = self.call_stack.pop()

                    stack_depth_upon_call = len(caller_program_stack)
                    stack_used = stack_depth_upon_call - self.environment.minimum_stack_depth
                    stack_additional = self.stack_depth() - stack_depth_upon_call
                    self.environment.program_stack = caller_program_stack
                    if stack_additional > 0:
                        for i in range(stack_additional):
                            rv_val = dataType.AbstractValue()
                            rv = IR.Variable("$rv%d" % i, rv_val)
                            self.environment.program_stack_push(rv_val, False, rv)
                    if stack_additional < 0:
                        for i in range(-stack_additional):
                            self.environment.program_stack.pop()

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
                            call_rv += self.environment.program_stack[-(i+1)].identifier
                        call_rv += ') := '

                    self.appendIntermediateCode(['%sCALL %s%s' % (call_rv, str(callee), call_args)])

                    logger.info("pop call stack, next is %s", str(self.pc))
                    logger.info("stack used was %d", stack_used)
                    logger.info("stack additional was %d", stack_additional)
                # ok, we really are all done here!
                else:
                    assert len(self.if_else.env)==0
                    self.pc = None
        self.bytecodeContainer.IRs[tag] = self.intermediateCodes
