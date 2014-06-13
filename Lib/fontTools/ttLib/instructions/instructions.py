#instructions classes are generated from instructionList
class root_instruct(object):
    def __init__(self):
	self.data = []
        self.successor = [] 
        self.top = None
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def set_top(self,value):
        self.top = value
    def get_pop_num(self):
        return self.pop_num
    def get_push_num(self):
        return self.push_num
    def set_input(self,data):
        self.data = data

    def get_result(self):
        return self.data
    def prettyPrint(self):
        print(self.__class__.__name__,self.data,self.top)
class all():
    class PUSH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self)
            self.push_num = len(self.data)
            self.pop_num = 0
        def get_push_num(self):
            return len(self.data)
        def action(self):
            pass 

    class AA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class ABS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class ADD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class ALIGNPTS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class ALIGNRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class AND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class CALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class CEILING(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class CINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class CLEAR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DEBUG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class DELTAC1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAC2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAC3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP3(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DEPTH(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class DIV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class DUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  1 
            self.total_num = 1
        def action(self, input):
            pass 

    class EIF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ELSE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ENDF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class EQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class EVEN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class FDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class FLIPOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class FLIPON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class FLIPPT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class FLIPRGOFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class FLIPRGON(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class FLOOR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GETINFO(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GFV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
        def action(self, input):
            pass 

    class GPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
        def action(self, input):
            pass 

    class GT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class GTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class IDEF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class IF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class INSTCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class IP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class ISECT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  5 
            self.total_num = -5
        def action(self, input):
            pass 

    class IUP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class JMPR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class JROF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class JROT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class LOOPCALL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class LT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class LTEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MAX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MDAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class MDRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class MIAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MIN(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MINDEX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class MIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MPPEM(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class MPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class MSIRP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MUL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class NEG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class NEQ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class NOT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class NROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class ODD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class OR(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class POP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class RCVT(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RDTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROFF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROLL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  3 
            self.pop_num =  3 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTDG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTHG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RUTG(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class S45ROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SANGW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCANCTRL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCANTYPE(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SCVTCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SDB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SDPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SDS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SFVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SFVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SFVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SFVTPV(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SHC(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SHP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class SHPIX(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class SHZ(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SLOOP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SMD(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SPVFS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SPVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SPVTL(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SROUND(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SSW(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SSWCI(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SUB(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class SVTCA(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SWAP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  2 
            self.total_num = 0
        def action(self, input):
            pass 

    class SZP0(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZP1(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZP2(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZPS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class UTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class WCVTF(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class WCVTP(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class WS(root_instruct):
        def __init__(self):
            root_instruct.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

