from fontTools.ttLib.data import dataType
import math

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

class Expression(object):
    pass

class UnaryExpression(Expression):
    pass

class BinaryExpression(Expression):
    def __init__(self, left, right, op):
	self.left = left
	self.right = right
	self.operator = op

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
    def __init__(self, parameters = [], returnVal=None):
        super(GCMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'GC'

class GETINFOMethodCall(MethodCallStatement):
    def __init__(self, parameters = [], returnVal=None):
        super(GETINFOMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'GETINFO'
    def eval(self, keep_abstract):
        return self
        
class ROUNDMethodCall(MethodCallStatement):
    def __init__(self, data, parameters = [], returnVal=None):
        super(ROUNDMethodCall, self).__init__(parameters, returnVal)
        self.methodName = 'ROUND_'+data

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

class EmptyStatement(object):
    def __repr__(self):
        return "Empty"

class GotoStatement(object):
    def __init__(self, label):
        self.gotoLabel = label
    def __repr__(self):
        return "GOTO "+self.gotoLabel

class LabelBlock(object):
    def __init__(self,label):
        self.label = label
        self.statements = []
    def __repr__(self):
        resStr = ""
        resStr += self.label+'\n'
        for statement in self.statements:
            resStr += str(statement)+'\n'
        return resStr

class IfElseBlock(object):
    def __init__(self, condition = None, nesting_level = 1):
        self.condition = condition
        self.if_branch = []
        self.else_branch = []
        self.nesting_level = nesting_level
        self.mode = 'IF'
    def appendStatements(self, statements):
        if self.mode == 'IF':
            self.if_branch += statements
        else:
            self.else_branch += statements
    def __str__(self):
        c = self.condition.eval(True)
        if isinstance(c, dataType.UncertainValue):
            c = self.condition
        res_str = 'if ('+str(c)+') {\n'
        for line in self.if_branch:
            res_str += (self.nesting_level * 4 * ' ') + str(line) + '\n'
        res_str += (self.nesting_level-1) * 4 * ' ' + '}'
        if len(self.else_branch) > 0:
            res_str += ' else {\n'
            for line in self.else_branch:
                res_str += (self.nesting_level * 4 * ' ') + str(line) + '\n'
            res_str += (self.nesting_level-1) * 4 * ' ' + '}'
        return res_str

class ConditionalJumpBlock(object):
    def __init__(self, label, condition = None):
        self.label = label
        self.parentBlock = None
        self.gotoBlock = None
        self.condition = ""
        self.statements = []
        self.mode = 'if' 
        self.gotoClause = None
    def appendStatements(self, statements):
        if self.mode == 'if':
            self.statements += statements
        else:
            if self.gotoBlock == None:
                self.gotoBlock = LabelBlock(self.label+'E1')
            self.gotoBlock.statements += statements

    def appendStatement(self, statement):
        if self.mode == 'if':
            self.statements.append(statement)
        else:
            if self.gotoBlock == None:
                if self.label!=None:
                    self.gotoBlock = ConditionalJumpBlock(self.label+'E1')
                else:
                    self.gotoBlock = ConditionalJumpBlock('E1')
            self.gotoBlock.statements.append(statement)

    def setParent(self, parent):
        self.parentBlock = parent

    def finishBlock(self):
        if self.gotoBlock == None:
            self.gotoBlock = ConditionalJumpBlock(self.label+'E1')
            self.gotoBlock.statements = [EmptyStatement()]

    def __repr__(self):
        resStr = ""
        resStr += self.label+':'+'\n'
        resStr += 'IF'
        resStr += '('+self.condition+')'
        resStr += 'GOTO'
        if self.gotoBlock != None:
            resStr += str(self.gotoBlock.label)
        resStr += '\n'
        for statement in self.statements:
            resStr += str(statement)+'\n'
        resStr += str(self.gotoBlock)
        return resStr
