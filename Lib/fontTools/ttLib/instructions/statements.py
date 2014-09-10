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
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__.split("_")[0],self.data)
class all():
    class PUSH_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self)
            self.push_num = len(self.data)
            self.mnemonic = 'PUSH'
            self.pop_num = 0
        def get_push_num(self):
            return len(self.data)
    class AA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 127
            self.mnemonic = 'AA'
            self.name = 'AdjustAngle'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class ABS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 100
            self.mnemonic = 'ABS'
            self.name = 'Absolute'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class ADD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 96
            self.mnemonic = 'ADD'
            self.name = 'Add'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class ALIGNPTS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 39
            self.mnemonic = 'ALIGNPTS'
            self.name = 'AlignPts'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class ALIGNRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 60
            self.mnemonic = 'ALIGNRP'
            self.name = 'AlignRelativePt'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class AND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 90
            self.mnemonic = 'AND'
            self.name = 'LogicalAnd'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class CALL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 43
            self.mnemonic = 'CALL'
            self.name = 'CallFunction'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class CEILING_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 103
            self.mnemonic = 'CEILING'
            self.name = 'Ceiling'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class CINDEX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 37
            self.mnemonic = 'CINDEX'
            self.name = 'CopyXToTopStack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class CLEAR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 34
            self.mnemonic = 'CLEAR'
            self.name = 'ClearStack'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DEBUG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 79
            self.mnemonic = 'DEBUG'
            self.name = 'DebugCall'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class DELTAC1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 115
            self.mnemonic = 'DELTAC1'
            self.name = 'DeltaExceptionC1'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DELTAC2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 116
            self.mnemonic = 'DELTAC2'
            self.name = 'DeltaExceptionC2'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DELTAC3_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 117
            self.mnemonic = 'DELTAC3'
            self.name = 'DeltaExceptionC3'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DELTAP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 93
            self.mnemonic = 'DELTAP1'
            self.name = 'DeltaExceptionP1'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DELTAP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 113
            self.mnemonic = 'DELTAP2'
            self.name = 'DeltaExceptionP2'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DELTAP3_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 114
            self.mnemonic = 'DELTAP3'
            self.name = 'DeltaExceptionP3'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class DEPTH_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 36
            self.mnemonic = 'DEPTH'
            self.name = 'GetDepthStack'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
    class DIV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 98
            self.mnemonic = 'DIV'
            self.name = 'Divide'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class DUP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 32
            self.mnemonic = 'DUP'
            self.name = 'DuplicateTopStack'
            self.push_num =  2 
            self.pop_num =  1 
            self.total_num = 1
    class EIF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 89
            self.mnemonic = 'EIF'
            self.name = 'EndIf'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class ELSE_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 27
            self.mnemonic = 'ELSE'
            self.name = 'Else'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class ENDF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 45
            self.mnemonic = 'ENDF'
            self.name = 'EndFunctionDefinition'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class EQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 84
            self.mnemonic = 'EQ'
            self.name = 'Equal'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class EVEN_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 87
            self.mnemonic = 'EVEN'
            self.name = 'Even'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class FDEF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 44
            self.mnemonic = 'FDEF'
            self.name = 'FunctionDefinition'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class FLIPOFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 78
            self.mnemonic = 'FLIPOFF'
            self.name = 'SetAutoFlipOff'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class FLIPON_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 77
            self.mnemonic = 'FLIPON'
            self.name = 'SetAutoFlipOn'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class FLIPPT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 128
            self.mnemonic = 'FLIPPT'
            self.name = 'FlipPoint'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class FLIPRGOFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 130
            self.mnemonic = 'FLIPRGOFF'
            self.name = 'FlipRangeOff'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class FLIPRGON_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 129
            self.mnemonic = 'FLIPRGON'
            self.name = 'FlipRangeOn'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class FLOOR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 102
            self.mnemonic = 'FLOOR'
            self.name = 'Floor'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class GC_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 70
            self.mnemonic = 'GC'
            self.name = 'GetCoordOnPVector'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class GETINFO_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 136
            self.mnemonic = 'GETINFO'
            self.name = 'GetInfo'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class GFV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 13
            self.mnemonic = 'GFV'
            self.name = 'GetFVector'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
    class GPV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 12
            self.mnemonic = 'GPV'
            self.name = 'GetPVector'
            self.push_num =  2 
            self.pop_num =  0 
            self.total_num = 2
    class GT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 82
            self.mnemonic = 'GT'
            self.name = 'GreaterThan'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class GTEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 83
            self.mnemonic = 'GTEQ'
            self.name = 'GreaterThanOrEqual'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class IDEF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 137
            self.mnemonic = 'IDEF'
            self.name = 'InstructionDefinition'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class IF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 88
            self.mnemonic = 'IF'
            self.name = 'If'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class INSTCTRL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 142
            self.mnemonic = 'INSTCTRL'
            self.name = 'SetInstrExecControl'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class IP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 57
            self.mnemonic = 'IP'
            self.name = 'InterpolatePts'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class ISECT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 15
            self.mnemonic = 'ISECT'
            self.name = 'MovePtToIntersect'
            self.push_num =  0 
            self.pop_num =  5 
            self.total_num = -5
    class IUP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 48
            self.mnemonic = 'IUP'
            self.name = 'InterpolateUntPts'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class JMPR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 28
            self.mnemonic = 'JMPR'
            self.name = 'Jump'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class JROF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 121
            self.mnemonic = 'JROF'
            self.name = 'JumpRelativeOnFalse'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class JROT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 120
            self.mnemonic = 'JROT'
            self.name = 'JumpRelativeOnTrue'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class LOOPCALL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 42
            self.mnemonic = 'LOOPCALL'
            self.name = 'LoopAndCallFunction'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class LT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 80
            self.mnemonic = 'LT'
            self.name = 'LessThan'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class LTEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 81
            self.mnemonic = 'LTEQ'
            self.name = 'LessThenOrEqual'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class MAX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 139
            self.mnemonic = 'MAX'
            self.name = 'Maximum'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class MD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 73
            self.mnemonic = 'MD'
            self.name = 'MeasureDistance'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class MDAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 46
            self.mnemonic = 'MDAP'
            self.name = 'MoveDirectAbsPt'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class MDRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 192
            self.mnemonic = 'MDRP'
            self.name = 'MoveDirectRelPt'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class MIAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 62
            self.mnemonic = 'MIAP'
            self.name = 'MoveIndirectAbsPt'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class MIN_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 140
            self.mnemonic = 'MIN'
            self.name = 'Minimum'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class MINDEX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 38
            self.mnemonic = 'MINDEX'
            self.name = 'MoveXToTopStack'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class MIRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 224
            self.mnemonic = 'MIRP'
            self.name = 'MoveIndirectRelPt'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class MPPEM_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 75
            self.mnemonic = 'MPPEM'
            self.name = 'MeasurePixelPerEm'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
    class MPS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 76
            self.mnemonic = 'MPS'
            self.name = 'MeasurePointSize'
            self.push_num =  1 
            self.pop_num =  0 
            self.total_num = 1
    class MSIRP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 58
            self.mnemonic = 'MSIRP'
            self.name = 'MoveStackIndirRelPt'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class MUL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 99
            self.mnemonic = 'MUL'
            self.name = 'Multiply'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class NEG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 101
            self.mnemonic = 'NEG'
            self.name = 'Negate'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class NEQ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 85
            self.mnemonic = 'NEQ'
            self.name = 'NotEqual'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class NOT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 92
            self.mnemonic = 'NOT'
            self.name = 'LogicalNot'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class NROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 108
            self.mnemonic = 'NROUND'
            self.name = 'NoRound'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class ODD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 86
            self.mnemonic = 'ODD'
            self.name = 'Odd'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class OR_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 91
            self.mnemonic = 'OR'
            self.name = 'LogicalOr'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class POP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 33
            self.mnemonic = 'POP'
            self.name = 'PopTopStack'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class RCVT_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 69
            self.mnemonic = 'RCVT'
            self.name = 'ReadCVT'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class RDTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 125
            self.mnemonic = 'RDTG'
            self.name = 'RoundDownToGrid'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class ROFF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 122
            self.mnemonic = 'ROFF'
            self.name = 'RoundOff'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class ROLL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 138
            self.mnemonic = 'ROLL'
            self.name = 'RollTopThreeStack'
            self.push_num =  3 
            self.pop_num =  3 
            self.total_num = 0
    class ROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 104
            self.mnemonic = 'ROUND'
            self.name = 'Round'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class RS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 67
            self.mnemonic = 'RS'
            self.name = 'ReadStore'
            self.push_num =  1 
            self.pop_num =  1 
            self.total_num = 0
    class RTDG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 61
            self.mnemonic = 'RTDG'
            self.name = 'RoundToDoubleGrid'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class RTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 24
            self.mnemonic = 'RTG'
            self.name = 'RoundToGrid'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class RTHG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 25
            self.mnemonic = 'RTHG'
            self.name = 'RoundToHalfGrid'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class RUTG_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 124
            self.mnemonic = 'RUTG'
            self.name = 'RoundUpToGrid'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class S45ROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 119
            self.mnemonic = 'S45ROUND'
            self.name = 'SuperRound45Degrees'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SANGW_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 126
            self.mnemonic = 'SANGW'
            self.name = 'SetAngleWeight'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SCANCTRL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 133
            self.mnemonic = 'SCANCTRL'
            self.name = 'ScanConversionControl'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SCANTYPE_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 141
            self.mnemonic = 'SCANTYPE'
            self.name = 'ScanType'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SCFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 72
            self.mnemonic = 'SCFS'
            self.name = 'SetCoordFromStackFP'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SCVTCI_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 29
            self.mnemonic = 'SCVTCI'
            self.name = 'SetCVTCutIn'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SDB_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 94
            self.mnemonic = 'SDB'
            self.name = 'SetDeltaBaseInGState'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SDPVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 134
            self.mnemonic = 'SDPVTL'
            self.name = 'SetDualPVectorToLine'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SDS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 95
            self.mnemonic = 'SDS'
            self.name = 'SetDeltaShiftInGState'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SFVFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 11
            self.mnemonic = 'SFVFS'
            self.name = 'SetFVectorFromStack'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SFVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 4
            self.mnemonic = 'SFVTCA'
            self.name = 'SetFVectorToAxis'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class SFVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 8
            self.mnemonic = 'SFVTL'
            self.name = 'SetFVectorToLine'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SFVTPV_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 14
            self.mnemonic = 'SFVTPV'
            self.name = 'SetFVectorToPVector'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class SHC_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 52
            self.mnemonic = 'SHC'
            self.name = 'ShiftContourByLastPt'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SHP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 50
            self.mnemonic = 'SHP'
            self.name = 'ShiftPointByLastPoint'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class SHPIX_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 56
            self.mnemonic = 'SHPIX'
            self.name = 'ShiftZoneByPixel'
            self.push_num =  0 
            self.pop_num =   'ALL' 
    class SHZ_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 54
            self.mnemonic = 'SHZ'
            self.name = 'ShiftZoneByLastPoint'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SLOOP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 23
            self.mnemonic = 'SLOOP'
            self.name = 'SetLoopVariable'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SMD_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 26
            self.mnemonic = 'SMD'
            self.name = 'SetMinimumDistance'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SPVFS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 10
            self.mnemonic = 'SPVFS'
            self.name = 'SetPVectorFromStack'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SPVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 2
            self.mnemonic = 'SPVTCA'
            self.name = 'SetPVectorToAxis'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class SPVTL_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 6
            self.mnemonic = 'SPVTL'
            self.name = 'SetPVectorToLine'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class SROUND_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 118
            self.mnemonic = 'SROUND'
            self.name = 'SuperRound'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SRP0_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 16
            self.mnemonic = 'SRP0'
            self.name = 'SetRefPoint0'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SRP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 17
            self.mnemonic = 'SRP1'
            self.name = 'SetRefPoint1'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SRP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 18
            self.mnemonic = 'SRP2'
            self.name = 'SetRefPoint2'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SSW_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 31
            self.mnemonic = 'SSW'
            self.name = 'SetSingleWidth'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SSWCI_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 30
            self.mnemonic = 'SSWCI'
            self.name = 'SetSingleWidthCutIn'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SUB_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 97
            self.mnemonic = 'SUB'
            self.name = 'Subtract'
            self.push_num =  1 
            self.pop_num =  2 
            self.total_num = -1
    class SVTCA_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 0
            self.mnemonic = 'SVTCA'
            self.name = 'SetFPVectorToAxis'
            self.push_num =  0 
            self.pop_num =  0 
            self.total_num = 0
    class SWAP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 35
            self.mnemonic = 'SWAP'
            self.name = 'SwapTopStack'
            self.push_num =  2 
            self.pop_num =  2 
            self.total_num = 0
    class SZP0_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 19
            self.mnemonic = 'SZP0'
            self.name = 'SetZonePointer0'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SZP1_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 20
            self.mnemonic = 'SZP1'
            self.name = 'SetZonePointer1'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SZP2_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 21
            self.mnemonic = 'SZP2'
            self.name = 'SetZonePointer2'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class SZPS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 22
            self.mnemonic = 'SZPS'
            self.name = 'SetZonePointerS'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class UTP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 41
            self.mnemonic = 'UTP'
            self.name = 'UnTouchPt'
            self.push_num =  0 
            self.pop_num =  1 
            self.total_num = -1
    class WCVTF_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 112
            self.mnemonic = 'WCVTF'
            self.name = 'WriteCVTInFUnits'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class WCVTP_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 68
            self.mnemonic = 'WCVTP'
            self.name = 'WriteCVTInPixels'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
    class WS_Statement(root_statement):
        def __init__(self):
            root_statement.__init__(self) 
            self.opcode = 66
            self.mnemonic = 'WS'
            self.name = 'WriteStore'
            self.push_num =  0 
            self.pop_num =  2 
            self.total_num = -2
