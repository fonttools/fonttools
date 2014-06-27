#instructions classes are generated from instructionList
class root_statement(object):
    def __init__(self):
	self.data = []
        #one instruction may have mutiple successors
        self.successors = [] 
        #one instruction has one predecessor
        self.predecessor = None
        self.top = None
    def add_successor(self,successor):
        self.successors.append(successor)
    def set_predecessor(self, predecessor):
        self.predecessor = predecessor
    def add_data(self,new_data):
        self.data.append(new_data.value)
    def get_pop_num(self):
        return self.pop_num
    def get_push_num(self):
        return self.push_num
    def set_input(self,data):
        self.data = data
    def get_result(self):
        return self.data
    def prettyPrint(self):
        print(self.__class__.__name__,self.data)
class all():
    class PUSH_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self)
            self.push_num = len(self.data)
            self.pop_num = 0
        def get_push_num(self):
            return len(self.data)
        def action(self):
            pass 

    class AA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class ABS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class ADD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class ALIGNPTS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class ALIGNRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class AND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class CALL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class CEILING_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class CINDEX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class CLEAR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DEBUG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class DELTAC1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAC2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAC3_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DELTAP3_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class DEPTH_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class DIV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class DUP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  1 
            self.total_num = 1
        def action(self, input):
            pass 

    class EIF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ELSE_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ENDF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class EQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class EVEN_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class FDEF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class FLIPOFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class FLIPON_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class FLIPPT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class FLIPRGOFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class FLIPRGON_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class FLOOR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GC_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GETINFO_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class GFV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
        def action(self, input):
            pass 

    class GPV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
        def action(self, input):
            pass 

    class GT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class GTEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class IDEF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class IF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class INSTCTRL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class IP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class ISECT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  5 
            self.total_num = -5
        def action(self, input):
            pass 

    class IUP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class JMPR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class JROF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class JROT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class LOOPCALL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class LT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class LTEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MAX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MDAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class MDRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class MIAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MIN_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class MINDEX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class MIRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MPPEM_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class MPS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'None'
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
        def action(self, input):
            pass 

    class MSIRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class MUL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class NEG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class NEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class NOT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class NROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class ODD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class OR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class POP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class RCVT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RDTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROLL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  3 
            self.pop_num =  3 
            self.total_num = 0
        def action(self, input):
            pass 

    class ROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTDG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RTHG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class RUTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class S45ROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SANGW_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCANCTRL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCANTYPE_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SCFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SCVTCI_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SDB_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SDPVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SDS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SFVFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SFVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SFVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SFVTPV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SHC_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SHP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class SHPIX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =   'ALL' 
        def action(self, input):
            pass 

    class SHZ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SLOOP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SMD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SPVFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SPVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SPVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class SROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP0_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SRP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SSW_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SSWCI_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SUB_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
        def action(self, input):
            pass 

    class SVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'self'
            self.out_source = 'graphic_state'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
        def action(self, input):
            pass 

    class SWAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack' 
            self.out_source = 'program_stack'
            self.push_num =  2 
            self.pop_num =  2 
            self.total_num = 0
        def action(self, input):
            pass 

    class SZP0_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class SZPS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class UTP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
        def action(self, input):
            pass 

    class WCVTF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class WCVTP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

    class WS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.in_source = 'program_stack'
            self.out_source = 'None'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
        def action(self, input):
            pass 

