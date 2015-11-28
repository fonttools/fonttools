'''
introduce a type system into font tools analysis
that point values won't affect the control flow graph
'''
class Value(object):
    """Represents either a concrete or abstract TrueType value."""
    pass

class AbstractValue(Value):
    def __init__(self):
        self.value = None
    def __repr__(self):
        return self.__class__.__name__
    def eval(self):
        return self

class UncertainValue(AbstractValue):
    def __init__(self, inputValue = None):
        self.possibleValues = inputValue
    def __repr__(self):
        return str(self.possibleValues)

class F26Dot6(AbstractValue):
    def __init__(self, value=None):
        self.value = value
    
class PPEM_X(AbstractValue):
    pass

class PPEM_Y(AbstractValue):
    pass

class PointSize(AbstractValue):
    pass
class EngineInfo(AbstractValue):
    pass
class Distance(AbstractValue):
    pass

class RoundState_DG(AbstractValue):
    pass
class RoundState_G(AbstractValue):
    pass
class RoundState_HG(AbstractValue):
    pass
class RoundState_UG(AbstractValue):
    pass

class Expression(AbstractValue):
    def __init__(self,op1 = None,op2 = None,operation = None):
        self.op1 = op1
        self.op2 = op2
        self.operation = operation
    def __repr__(self):
    	return str(self.op1) + ' '+ str(self.operation) + ' ' + str(self.op2)

    def eval(self):
        def equal(op1,op2):
            return op1 == op2
        def less(op1,op2):
            return op1 < op2
        def lessEqual(op1,op2):
            return op1 <= op2
        def greater(op1,op2):
            return op1 > op2
        def greaterEqual(op1,op2):
            return op1 >= op2
        def logicalAnd(op1,op2):
            return (op1 and op2)
        def logicalOr(op1,op2):
            return (op1 or op2)
        operations = {'LT':less,
                      'LTEQ':lessEqual,
                      'GT':greater,
                      'GTEQ':greaterEqual,
                      'EQ':equal,
                      'AND':logicalAnd,
                      'OR':logicalOr}
        if isinstance(self.op1, AbstractValue) or isinstance(self.op2, AbstractValue):
            return self
        return operations[self.operation](self.op1,self.op2)

class UnaryExpression(Expression):
    def __init__(self, operand = None, operation = None):
        self.operand = operand
        self.operation = operation
    def __repr__(self):
        return str(self.operation) + ' ' + str(self.operand)
