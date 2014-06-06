import os
import sys
# next, the list of "normal" instructions
'''
five categories of instructions:
   Pushing data onto the interpreter stack
   Managing the Storage Area
   Managing the Control Value Table
   Modifying Graphics State settings
   Managing outlines
   General purpose instructions
'''

instructions = [
#   ------  -----------  -----  ------------------------ ---  ------ ----- ------ ------- ----------------------------------  --------------
#   opcode     mnemonic  argBits        descriptive name pops pushes input output acticion                               pops          pushes
#   ------  -----------  -----  ------------------------ ---  ------ ----- ------ ------- ----------------------------------  --------------
    (0x7f,        'AA',     0,            'AdjustAngle',  1,  0), #                                    p               -
    (0x64,       'ABS',     0,               'Absolute',  1,  1), #                                    n             |n|
    (0x60,       'ADD',     0,                    'Add',  2,  1), #                               n2, n1       (n1 + n2)
    (0x27,  'ALIGNPTS',     0,               'AlignPts',  2,  0), #                               p2, p1               -
    (0x3c,   'ALIGNRP',     0,        'AlignRelativePt', -1,  0), #             p1, p2, ... , ploopvalue               -
    (0x5a,       'AND',     0,             'LogicalAnd',  2,  1), #                               e2, e1               b
    (0x2b,      'CALL',     0,           'CallFunction',  1,  0), #                                    f               -
    (0x67,   'CEILING',     0,                'Ceiling',  1,  1), #                                    n         ceil(n)
    (0x25,    'CINDEX',     0,        'CopyXToTopStack',  1,  1), #                                    k              ek
    (0x22,     'CLEAR',     0,             'ClearStack', -1,  0), #               all items on the stack               -
    (0x4f,     'DEBUG',     0,              'DebugCall',  1,  0), #                                    n               -
    (0x73,   'DELTAC1',     0,       'DeltaExceptionC1', -1,  0), #    argn, cn, argn-1,cn-1, , arg1, c1               -
    (0x74,   'DELTAC2',     0,       'DeltaExceptionC2', -1,  0), #    argn, cn, argn-1,cn-1, , arg1, c1               -
    (0x75,   'DELTAC3',     0,       'DeltaExceptionC3', -1,  0), #    argn, cn, argn-1,cn-1, , arg1, c1               -
    (0x5d,   'DELTAP1',     0,       'DeltaExceptionP1', -1,  0), #   argn, pn, argn-1, pn-1, , arg1, p1               -
    (0x71,   'DELTAP2',     0,       'DeltaExceptionP2', -1,  0), #   argn, pn, argn-1, pn-1, , arg1, p1               -
    (0x72,   'DELTAP3',     0,       'DeltaExceptionP3', -1,  0), #   argn, pn, argn-1, pn-1, , arg1, p1               -
    (0x24,     'DEPTH',     0,          'GetDepthStack',  0,  1), #                                    -               n
    (0x62,       'DIV',     0,                 'Divide',  2,  1), #                               n2, n1   (n1 * 64)/ n2
    (0x20,       'DUP',     0,      'DuplicateTopStack',  1,  2), #                                    e            e, e
    (0x59,       'EIF',     0,                  'EndIf',  0,  0), #                                    -               -
    (0x1b,      'ELSE',     0,                   'Else',  0,  0), #                                    -               -
    (0x2d,      'ENDF',     0,  'EndFunctionDefinition',  0,  0), #                                    -               -
    (0x54,        'EQ',     0,                  'Equal',  2,  1), #                               e2, e1               b
    (0x57,      'EVEN',     0,                   'Even',  1,  1), #                                    e               b
    (0x2c,      'FDEF',     0,     'FunctionDefinition',  1,  0), #                                    f               -
    (0x4e,   'FLIPOFF',     0,         'SetAutoFlipOff',  0,  0), #                                    -               -
    (0x4d,    'FLIPON',     0,          'SetAutoFlipOn',  0,  0), #                                    -               -
    (0x80,    'FLIPPT',     0,              'FlipPoint', -1,  0), #              p1, p2, ..., ploopvalue               -
    (0x82, 'FLIPRGOFF',     0,           'FlipRangeOff',  2,  0), #                                 h, l               -
    (0x81,  'FLIPRGON',     0,            'FlipRangeOn',  2,  0), #                                 h, l               -
    (0x66,     'FLOOR',     0,                  'Floor',  1,  1), #                                    n        floor(n)
    (0x46,        'GC',     1,      'GetCoordOnPVector',  1,  1), #                                    p               c
    (0x88,   'GETINFO',     0,                'GetInfo',  1,  1), #                             selector          result
    (0x0d,       'GFV',     0,             'GetFVector',  0,  2), #                                    -          px, py
    (0x0c,       'GPV',     0,             'GetPVector',  0,  2), #                                    -          px, py
    (0x52,        'GT',     0,            'GreaterThan',  2,  1), #                               e2, e1               b
    (0x53,      'GTEQ',     0,     'GreaterThanOrEqual',  2,  1), #                               e2, e1               b
    (0x89,      'IDEF',     0,  'InstructionDefinition',  1,  0), #                                    f               -
    (0x58,        'IF',     0,                     'If',  1,  0), #                                    e               -
    (0x8e,  'INSTCTRL',     0,    'SetInstrExecControl',  2,  0), #                                 s, v               -
    (0x39,        'IP',     0,         'InterpolatePts', -1,  0), #             p1, p2, ... , ploopvalue               -
    (0x0f,     'ISECT',     0,      'MovePtToIntersect',  5,  0), #                    a1, a0, b1, b0, p               -
    (0x30,       'IUP',     1,      'InterpolateUntPts',  0,  0), #                                    -               -
    (0x1c,      'JMPR',     0,                   'Jump',  1,  0), #                               offset               -
    (0x79,      'JROF',     0,    'JumpRelativeOnFalse',  2,  0), #                            e, offset               -
    (0x78,      'JROT',     0,     'JumpRelativeOnTrue',  2,  0), #                            e, offset               -
    (0x2a,  'LOOPCALL',     0,    'LoopAndCallFunction',  2,  0), #                             f, count               -
    (0x50,        'LT',     0,               'LessThan',  2,  1), #                               e2, e1               b
    (0x51,      'LTEQ',     0,        'LessThenOrEqual',  2,  1), #                               e2, e1               b
    (0x8b,       'MAX',     0,                'Maximum',  2,  1), #                               e2, e1     max(e1, e2)
    (0x49,        'MD',     1,        'MeasureDistance',  2,  1), #                                p2,p1               d
    (0x2e,      'MDAP',     1,        'MoveDirectAbsPt',  1,  0), #                                    p               -
    (0xc0,      'MDRP',     5,        'MoveDirectRelPt',  1,  0), #                                    p               -
    (0x3e,      'MIAP',     1,      'MoveIndirectAbsPt',  2,  0), #                                 n, p               -
    (0x8c,       'MIN',     0,                'Minimum',  2,  1), #                               e2, e1     min(e1, e2)
    (0x26,    'MINDEX',     0,        'MoveXToTopStack',  1,  1), #                                    k              ek
    (0xe0,      'MIRP',     5,      'MoveIndirectRelPt',  2,  0), #                                 n, p               -
    (0x4b,     'MPPEM',     0,      'MeasurePixelPerEm',  0,  1), #                                    -            ppem
    (0x4c,       'MPS',     0,       'MeasurePointSize',  0,  1), #                                    -       pointSize
    (0x3a,     'MSIRP',     1,    'MoveStackIndirRelPt',  2,  0), #                                 d, p               -
    (0x63,       'MUL',     0,               'Multiply',  2,  1), #                               n2, n1    (n1 * n2)/64
    (0x65,       'NEG',     0,                 'Negate',  1,  1), #                                    n              -n
    (0x55,       'NEQ',     0,               'NotEqual',  2,  1), #                               e2, e1               b
    (0x5c,       'NOT',     0,             'LogicalNot',  1,  1), #                                    e       ( not e )
    (0x6c,    'NROUND',     2,                'NoRound',  1,  1), #                                   n1              n2
    (0x56,       'ODD',     0,                    'Odd',  1,  1), #                                    e               b
    (0x5b,        'OR',     0,              'LogicalOr',  2,  1), #                               e2, e1               b
    (0x21,       'POP',     0,            'PopTopStack',  1,  0), #                                    e               -
    (0x45,      'RCVT',     0,                'ReadCVT',  1,  1), #                             location           value
    (0x7d,      'RDTG',     0,        'RoundDownToGrid',  0,  0), #                                    -               -
    (0x7a,      'ROFF',     0,               'RoundOff',  0,  0), #                                    -               -
    (0x8a,      'ROLL',     0,      'RollTopThreeStack',  3,  3), #                                a,b,c           b,a,c
    (0x68,     'ROUND',     2,                  'Round',  1,  1), #                                   n1              n2
    (0x43,        'RS',     0,              'ReadStore',  1,  1), #                                    n               v
    (0x3d,      'RTDG',     0,      'RoundToDoubleGrid',  0,  0), #                                    -               -
    (0x18,       'RTG',     0,            'RoundToGrid',  0,  0), #                                    -               -
    (0x19,      'RTHG',     0,        'RoundToHalfGrid',  0,  0), #                                    -               -
    (0x7c,      'RUTG',     0,          'RoundUpToGrid',  0,  0), #                                    -               -
    (0x77,  'S45ROUND',     0,    'SuperRound45Degrees',  1,  0), #                                    n               -
    (0x7e,     'SANGW',     0,         'SetAngleWeight',  1,  0), #                               weight               -
    (0x85,  'SCANCTRL',     0,  'ScanConversionControl',  1,  0), #                                    n               -
    (0x8d,  'SCANTYPE',     0,               'ScanType',  1,  0), #                                    n               -
    (0x48,      'SCFS',     0,    'SetCoordFromStackFP',  2,  0), #                                 c, p               -
    (0x1d,    'SCVTCI',     0,            'SetCVTCutIn',  1,  0), #                                    n               -
    (0x5e,       'SDB',     0,   'SetDeltaBaseInGState',  1,  0), #                                    n               -
    (0x86,    'SDPVTL',     1,   'SetDualPVectorToLine',  2,  0), #                               p2, p1               -
    (0x5f,       'SDS',     0,  'SetDeltaShiftInGState',  1,  0), #                                    n               -
    (0x0b,     'SFVFS',     0,    'SetFVectorFromStack',  2,  0), #                                 y, x               -
    (0x04,    'SFVTCA',     1,       'SetFVectorToAxis',  0,  0), #                                    -               -
    (0x08,     'SFVTL',     1,       'SetFVectorToLine',  2,  0), #                               p2, p1               -
    (0x0e,    'SFVTPV',     0,    'SetFVectorToPVector',  0,  0), #                                    -               -
    (0x34,       'SHC',     1,   'ShiftContourByLastPt',  1,  0), #                                    c               -
    (0x32,       'SHP',     1,  'ShiftPointByLastPoint', -1,  0), #              p1, p2, ..., ploopvalue               -
    (0x38,     'SHPIX',     0,       'ShiftZoneByPixel', -1,  0), #           d, p1, p2, ..., ploopvalue               -
    (0x36,       'SHZ',     1,   'ShiftZoneByLastPoint',  1,  0), #                                    e               -
    (0x17,     'SLOOP',     0,        'SetLoopVariable',  1,  0), #                                    n               -
    (0x1a,       'SMD',     0,     'SetMinimumDistance',  1,  0), #                             distance               -
    (0x0a,     'SPVFS',     0,    'SetPVectorFromStack',  2,  0), #                                 y, x               -
    (0x02,    'SPVTCA',     1,       'SetPVectorToAxis',  0,  0), #                                    -               -
    (0x06,     'SPVTL',     1,       'SetPVectorToLine',  2,  0), #                               p2, p1               -
    (0x76,    'SROUND',     0,             'SuperRound',  1,  0), #                                    n               -
    (0x10,      'SRP0',     0,           'SetRefPoint0',  1,  0), #                                    p               -
    (0x11,      'SRP1',     0,           'SetRefPoint1',  1,  0), #                                    p               -
    (0x12,      'SRP2',     0,           'SetRefPoint2',  1,  0), #                                    p               -
    (0x1f,       'SSW',     0,         'SetSingleWidth',  1,  0), #                                    n               -
    (0x1e,     'SSWCI',     0,    'SetSingleWidthCutIn',  1,  0), #                                    n               -
    (0x61,       'SUB',     0,               'Subtract',  2,  1), #                               n2, n1       (n1 - n2)
    (0x00,     'SVTCA',     1,      'SetFPVectorToAxis',  0,  0), #                                    -               -
    (0x23,      'SWAP',     0,           'SwapTopStack',  2,  2), #                               e2, e1          e1, e2
    (0x13,      'SZP0',     0,        'SetZonePointer0',  1,  0), #                                    n               -
    (0x14,      'SZP1',     0,        'SetZonePointer1',  1,  0), #                                    n               -
    (0x15,      'SZP2',     0,        'SetZonePointer2',  1,  0), #                                    n               -
    (0x16,      'SZPS',     0,        'SetZonePointerS',  1,  0), #                                    n               -
    (0x29,       'UTP',     0,              'UnTouchPt',  1,  0), #                                    p               -
    (0x70,     'WCVTF',     0,       'WriteCVTInFUnits',  2,  0), #                                 n, l               -
    (0x44,     'WCVTP',     0,       'WriteCVTInPixels',  2,  0), #                                 v, l               -
    (0x42,        'WS',     0,             'WriteStore',  2,  0), #                                 v, l               -
#   ------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
]
cvt_table_related = ['RCVT','WCVTF','WCVTP','SCVTCI']
storage_area_related = ['WS','RS']
graphics_state_related = ['SVTCA','SPVTCA','SFVTCA','SPVTL','SFVTL','SFVTPV','SDPVTL','SVPTL','SPVFS','SFVFS','SRP0'
function_table_related = ['FDEF','ENDF']
def emit(stream, line, level=0):
        indent = "    "*level
        stream.write(indent + line + "\n")
def constructInstructionClasses(instructionList):
	HEAD = """#instructions classes are generated from instructionList
class root_instruct(object):
    def __init__(self):
	self.data = []
        self.successor = None 
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
    def get_successor(self):
        return self.successor
    def set_successor(self,successor):
        self.successor = successor
    def get_result(self):
        return self.data
    def prettyPrinter(self):
        print(self.__class__.__name__,self.data,self.top)
class all():
"""

        here = os.path.dirname(__file__)
   	out_file = os.path.join(here, ".", "instructions_abstract.py")
	fp = open(out_file, "w")
        try:
            fp.write(HEAD)
            emit(fp,"class PUSH(root_instruct):",1)
            emit(fp,"def __init__(self):",2)
            emit(fp,"root_instruct.__init__(self)",3)
            emit(fp,"self.push_num = len(self.data)",3)
            emit(fp,"self.pop_num = 0",3)
            emit(fp,"def action(self):",2)
            emit(fp,"pass ",3)
            emit(fp,"")
            for op, mnemonic, argBits, name, pops, pushes in instructionList:
                emit(fp,"class %s(root_instruct):" % (mnemonic),1)
                emit(fp,"def __init__(self):", 2)
                emit(fp,"root_instruct.__init__(self) ", 3)
                if pops != 0 and pushes != 0:
                    emit(fp, "self.in_source = 'program_stack' ",3)
                    emit(fp, "self.out_source = 'program_stack'",3)
                elif pops == 0 and pushes != 0:
                    if op in cvt_related_instructions:
                        emit(fp,"self.in_source = 'cvt'",3)
                    elif op in storage_area_related_instructions:
                        emit(fp,"self.in_source = 'storage_area'",3)
                    else:
                        emit(fp,"self.in_source = 'None'",3)
                    emit(fp,"self.out_source = 'program_stack'",3)
                elif pushes == 0 and pops != 0:
                    emit(fp,"self.in_source = 'program_stack'",3)
                    if op in cvt_related_instructions:
                        emit(fp,"self.out_source = 'cvt'",3)
                    elif op in storage_area_related_instructions:
                        emit(fp,"self.out_source = 'storage_area'",3)
                    else:
                        emit(fp,"self.in_source = 'None'",3)
                else:
                    emit(fp,"self.in_source = 'self'",3)
                    emit(fp,"self.out_source = 'graphic_state'",3)
                emit(fp,"self.push_num =  %s "  %(pushes), 3)
                emit(fp,"self.pop_num =  %s "  %(pops), 3)
                emit(fp,"def action(self, input):", 2)
                emit(fp,"pass ", 3)
                emit(fp,"")
        finally:
            fp.close()

if __name__ == "__main__":
    constructInstructionClasses(instructions)
