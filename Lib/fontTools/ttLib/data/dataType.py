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
        #currently there are greater->[] equal->[] greater or equal->[]
        self.conditions = {};
    def __repr__(self):
        return self.__class__.__name__
    def __str__(self):
        return self.__class__.__name__
class UncertainValue(AbstractValue):
    def __init__(self, inputValue= None):
        self.possibleValues = inputValue
class F26Dot6(AbstractValue):
    def __init__(self, value=None):
        self.value = value
    
class PPEM_X(AbstractValue):
    pass

class PPEM_Y(AbstractValue):
    pass

class PointValue(AbstractValue):
    pass
class EngineInfo(AbstractValue):
    pass
class Distance(AbstractValue):
    pass

class Expression(AbstractValue):
    def __init__(self,op1 = None,op2 = None,operation = None):
        self.op1 = op1
        self.op2 = op2
        self.operation = operation
    def __repr__(self):
    	return str(self.op1) + ' '+ str(self.operation) + ' ' + str(self.op2)

    def eval(self):
        options = {'LT':less,
                'LTEQ':lessEqual,
                'GT':greater,
                'GTEQ':greaterEqual,
                'EQ':equal,
                'AND':logicAnd,
                'OR':logicOr}
        if isinstance(op1, AbstractValue) or isinstance(op2, AbstractValue):
            return 'uncertain'
        return options[self.operation](self.op1,self.op2)
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
class UnaryExpression(Expression):
    def __init__(self, op = None, operation = None):
        self.op = op
        self.operation = operation
    def __repr(self):
        return str(self.operation) + ' ' + str(self.op)
