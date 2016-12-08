from fontTools.ttLib.data import dataType
import math
import copy

class Boolean(object):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value

class Constant(object):
    def __init__(self, value):
        self.value = value
    def eval(self, keep_abstract):
        return self.value
    def __repr__(self):
        return str(self.value)

class Variable(dataType.AbstractValue):
    def __init__(self, identifier, data = None):
        self.identifier = identifier
        self.data = data
    def eval(self, keep_abstract):
        if keep_abstract or self.data is None:
            return self
        if isinstance(self.data, dataType.AbstractValue):
            return self.data.eval(keep_abstract)
        else:
            return self.data
    def __repr__(self):
        return self.identifier
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

class GraphicsStateVariable(Variable):
    def __repr__(self):
        return 'GS['+self.identifier+']'

class AutoFlip(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[auto_flip]'
    
class DeltaBase(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[delta_base]'

class DeltaShift(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[delta_shift]'

class FreedomVector(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[freedom_vector]'

class FreedomVectorByComponent(GraphicsStateVariable):
    def __init__(self, selector):
        self.data = None
        self.selector = selector
        self.identifier = 'GS[freedom_vector_%s]' % self.selector

class DualProjectionVector(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[dual_projection_vector]'

class InstructControl(GraphicsStateVariable):
    def __init__(self, selector):
        self.selector = selector
        self.data = None
        self.identifier = 'GS[instruction_control_%s]' % self.selector

class LoopValue(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[loop]'

class MinimumDistance(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[minimum_distance]'

class ControlValueCutIn(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[control_value_cutin]'

class RoundState(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[round_state]'

class RP0(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[rp0]'

class RP1(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[rp1]'

class RP2(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[rp2]'

class ScanControl(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[scan_control]'

class ScanType(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[scan_type]'

class SingleWidthCutIn(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[single_width_cutin]'

class SingleWidthValue(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[single_width_value]'

class ZP0(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[zp0]'

class ZP1(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[zp1]'

class ZP2(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[zp2]'

class ProjectionVector(GraphicsStateVariable):
    def __init__(self):
        self.data = None
        self.identifier = 'GS[projection_vector]'

class GlobalDictionary(Variable):
    def __init__(self):
        self.storage = {}
    def read(self,index):
        return self.storage[index]
    def write(self, index, val):
        self.storage[index] = val
class CVTTable(GlobalDictionary):
    pass
class StorageArea(GlobalDictionary):
    pass

class InputVariable(Variable):
    pass

class Operator(object):
    pass

class AssignOperator(Operator):
    def __repr__(self):
        return ":="
class ADDOperator(Operator):
    def __repr__(self):
        return "+"
class SUBOperator(Operator):
    def __repr__(self):
        return "-"
class MULOperator(Operator):
    def __repr__(self):
        return "*"
class DIVOperator(Operator):
    def __repr__(self):
        return "/"
class MAXOperator(Operator):
    def __repr__(self):
        return "max"
class MINOperator(Operator):
    def __repr__(self):
        return "min"

class ANDOperator(Operator):
    def __repr__(self):
        return "AND"
class OROperator(Operator):
    def __repr__(self):
        return "OR"
class GTOperator(Operator):
    def __repr__(self):
        return "GT"
class GTEQOperator(Operator):
    def __repr__(self):
        return "GE"
class LTOperator(Operator):
    def __repr__(self):
        return "LT"
class LTEQOperator(Operator):
    def __repr__(self):
        return "LE"
class EQOperator(Operator):
    def __repr__(self):
        return "EQ"
class NEQOperator(Operator):
    def __repr__(self):
        return "NE"

class NEGOperator(Operator):
    def __repr__(self):
        return "NEG"

class Expression(dataType.AbstractValue):
    pass

class UnaryExpression(Expression):
    def __init__(self, arg, op):
	self.arg = arg
	self.operator = op
    def eval(self, keep_abstract):
        if (keep_abstract):
            return self
        ue = copy.copy(self)
        ue.arg = ue.arg.eval(keep_abstract)
        return ue
    def __repr__(self):
	return "%s %s" % (str(self.operator), self.arg)

class BinaryExpression(Expression):
    def __init__(self, left, right, op):
	self.left = left
	self.right = right
	self.operator = op
    def eval(self, keep_abstract):
        if (keep_abstract):
            return self
        be = copy.copy(self)
        be.left = be.left.eval(keep_abstract)
        be.right = be.right.eval(keep_abstract)
        return be

class InfixBinaryExpression(BinaryExpression):
    def __init__(self, left, right, op):
        super(InfixBinaryExpression, self).__init__(left, right, op)
    def __repr__(self):
	return "%s %s %s" % (self.left, str(self.operator), self.right)

class PrefixBinaryExpression(BinaryExpression):
    def __init__(self, left, right, op):
        super(PrefixBinaryExpression, self).__init__(left, right, op)
    def __repr__(self):
	return "%s(%s, %s)" % (str(self.operator), self.left, self.right)

class MethodCallStatement(object):
    def __init__(self, parameters = [], returnVal=None):
    	self.parameters = parameters
        self.returnVal = returnVal
    def setParameters(self, parameters):
        self.parameters = parameters
    def setReturnVal(self, returnVal):
        self.returnVal = returnVal
    def __repr__(self):
        repS = ''
        if self.returnVal is not None:
            repS = str(self.returnVal) + ' := '
    	repS += '{}('.format(self.methodName)
        repS += ','.join(map(lambda x: str(x.identifier), self.parameters))
        repS += ')'
	return repS

class SDBMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SDBMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SDB'

class DELTAMethodCall(MethodCallStatement):
    def __init__(self, op, parameters = [], returnVal=None):
        super(DELTAMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'DELTA' + op

class MINMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(MINMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MIN'

class MAXMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(MAXMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MAX'

class ALIGNPTSMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(ALIGNPTSMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'ALIGNPT'

class ABSMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(ABSMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'ABS'
    def eval(self, keep_abstract):
        p = self.parameters[0].eval(keep_abstract)
        if isinstance(p, dataType.AbstractValue):
            return self
        return math.fabs(p)

class CEILMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(CEILINGMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'CEIL'
    def eval(self, keep_abstract):
        p = self.parameters[0].eval(keep_abstract)
        if isinstance(p, dataType.AbstractValue):
            return self
        return math.ceil(p)

class FLOORMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(FLOORMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'FLOOR'
    def eval(self, keep_abstract):
        p = self.parameters[0].eval(keep_abstract)
        if isinstance(p, dataType.AbstractValue):
            return self
        return math.floor(p)

class NOTMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(NOTMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'NOT'
    def eval(self, keep_abstract):
        p = self.parameters[0].eval(keep_abstract)
        if p == 0:
            return 1
        elif p == 1:
            return 0
        return self

class MIRPMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(MIRPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MIRP'

class GCMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(GCMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'GC_'+data

class GETINFOMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(GETINFOMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'GETINFO'
    def eval(self, keep_abstract):
        return self

class ALIGNRPMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(ALIGNRPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'ALIGNRP'

class IPMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(IPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'IP'

class ROUNDMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(ROUNDMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'ROUND_'+data.value

class SHPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(SHPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SHP_'+data.value

class SHPIXMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SHPIXMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SHPIX'

class IUPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(IUPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'IUP_'+data.value

class MDMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MDMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MD_'+data.value

class MDAPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MDAPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MDAP_'+data.value

class MDRPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MDRPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MDRP_'+data.value

class MIAPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MIAPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MIAP_'+data.value

class MIRPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MIRPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MIRP_'+data.value

class MSIRPMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(MSIRPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'MSIRP_'+data.value

class SCFSMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SCFSMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SCFS'

class SDPVTLMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(SDPVTLMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SDPVTL_'+data.value

class SDSMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SDSMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SDS'

class SFVFSMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SFVFSMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SFVFS'

class SFVTLMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(SFVTLMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SFVTL_'+data.value

class SHCMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(SHCMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SHC_'+data.value

class SHZMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(SHZMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SHZ_'+data.value

class SLOOPMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SLOOPMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SLOOP'

class SMDMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SMDMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SMD'

class SRP0MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SRP0MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SRP0'

class SRP1MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SRP1MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SRP1'

class SRP2MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SRP2MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SRP2'

class SZP0MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SZP0MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SZP0'

class SZP1MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SZP1MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SZP1'

class SZP2MethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(SZP2MethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'SZP2'

class AssignmentStatement(dataType.AbstractValue):
    def __init__(self):
        self.operator = AssignOperator()
    def __repr__(self):
        return "%s %s %s" % (self.left, self.operator, str(self.right))

class OperationAssignmentStatement(AssignmentStatement):
    def __init__(self, variable, expression):
        super(OperationAssignmentStatement,self).__init__()
        self.left = variable
        self.right = expression

class CopyStatement(AssignmentStatement):
    def __init__(self, variable, data):
        super(CopyStatement,self).__init__()
        self.left = variable.identifier
        if variable.data == None:
            variable.data = data
        self.right = variable.data
        
class CallStatement(MethodCallStatement):
    def __init__(self, variable):
        super(CallStatement, self).__init__([variable])
        self.methodName = "CALL"

class LoopCallStatement(MethodCallStatement):
    def __init__(self, variable, count):
        super(LoopCallStatement, self).__init__([variable])
        self.count = count
        self.methodName = "LOOPCALL_"
    def __repr__(self):
        return "%s_%s" % (self.methodName, self.count)

class IndexedAssignment(AssignmentStatement):
    def __init__(self, index, var):
        self.index = index
        self.var = var
        self.storage = None
    def __repr__(self):
        return "%s[%s] := %s" % (self.storage, self.index, self.var)

class WriteStorageStatement(IndexedAssignment):
    def __init__(self, index, var):
        super(WriteStorageStatement,self).__init__(index, var)
        self.storage = "storage_area"

class CVTStorageStatement(IndexedAssignment):
    def __init__(self, index, var):
        super(CVTStorageStatement,self).__init__(index, var)
        self.storage = "cvt_table"

class ReadFromIndexedStorage(AssignmentStatement):
    def __init__(self, storage, index):
        self.storage = storage
        self.index = index
    def __repr__(self):
        return "%s[%s]" % (self.storage, self.index)
    def eval(self, keep_abstract):
        if keep_abstract:
            return self
        ris = copy.copy(self)
        ris.index = ris.index.eval(keep_abstract)
        return ris

class EmptyStatement(object):
    def __repr__(self):
        return "NOP"

class ReturnStatement(object):
    def __repr__(self):
        return "RET"

class JmpStatement(object):
    def __init__(self, dest):
        self.bytecode_dest = dest
        self.inst_dest = None
    def __repr__(self):
        return "JMPR %s" % (self.inst_dest)

class JROxStatement(object):
    def __init__(self, onTrue, e, dest):
        self.onTrue = onTrue
        self.e = e
        self.bytecode_dest = dest
        self.inst_dest = None
    def __repr__(self):
        op = 'JROT' if self.onTrue else 'JROF'
        d = "self" if self == self.inst_dest else str(self.inst_dest)
        return "%s (%s, %s)" % (op, self.e, d)

class IfElseBlock(object):
    def __init__(self, condition = None, nesting_level = 1):
        self.condition = condition
        # IR
        self.if_branch = []
        self.else_branch = []
        self.nesting_level = nesting_level

        # bytecode
        self.if_instructions = []
        self.else_instructions = []

        # random crap
        self.mode = 'THEN'
        self.jump_targets = {}
    def __str__(self):
        c = self.condition.eval(True)
        if isinstance(c, dataType.UncertainValue):
            c = self.condition
        res_str = 'if ('+str(c)+') {\n'
        for inst in self.if_branch:
            if inst in self.jump_targets:
                res_str += "%s:" % self.jump_targets[inst] + '\n'
            if hasattr(inst, 'jump_targets'):
                inst.jump_targets = jump_targets
            res_str += (self.nesting_level * 4 * ' ') + str(inst) + '\n'
        res_str += (self.nesting_level-1) * 4 * ' ' + '}'
        if len(self.else_branch) > 0:
            res_str += ' else {\n'
            for inst in self.else_branch:
                if inst in self.jump_targets:
                    res_str += "%s:" % self.jump_targets[inst] + '\n'
                if hasattr(inst, 'jump_targets'):
                    inst.jump_targets = jump_targets
                res_str += (self.nesting_level * 4 * ' ') + str(inst) + '\n'
            res_str += (self.nesting_level-1) * 4 * ' ' + '}'
        return res_str
