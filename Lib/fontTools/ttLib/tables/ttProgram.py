"""ttLib.tables.ttProgram.py -- Assembler/disassembler for TrueType bytecode programs."""

import array


# first, the list of instructions that eat bytes or words from the instruction stream

streamInstructions = [
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
#	opcode     mnemonic argbits         descriptive name pops pushes        eats from instruction stream          pushes
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
	(0x40,    'NPUSHB',     0,             'PushNBytes',  0, -1), #                      n, b1, b2,...bn      b1,b2...bn
	(0x41,    'NPUSHW',     0,             'PushNWords',  0, -1), #                       n, w1, w2,...w      w1,w2...wn
	(0xb0,     'PUSHB',     3,              'PushBytes',  0, -1), #                          b0, b1,..bn  b0, b1, ...,bn
	(0xb8,     'PUSHW',     3,              'PushWords',  0, -1), #                           w0,w1,..wn   w0 ,w1, ...wn
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
]


# next, the list of "normal" instructions

instructions = [
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
#	opcode     mnemonic  argbits        descriptive name pops pushes                                pops          pushes
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
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
	(0x26,    'MINDEX',     0,        'MoveXToTopStack',  2,  1), #                                    k              ek
	(0xe0,      'MIRP',     5,      'MoveIndirectRelPt',  1,  0), #                                 n, p               -
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
#	------  -----------  -----  ------------------------ ---  ------  ----------------------------------  --------------
]


def bitRepr(value, bits):
	s = ""
	for i in range(bits):
		s = "01"[value & 0x1] + s
		value = value >> 1
	return s

def makeOpcodeDict(instructionList):
	opcodeDict = {}
	for op, mnemonic, argbits, name, pops, pushes in instructionList:
		if argbits:
			argoffset = op
			for i in range(1 << argbits):
				opcodeDict[op+i] = mnemonic, argbits, argoffset, name
		else:
				opcodeDict[op] = mnemonic, 0, 0, name
	return opcodeDict

streamOpcodeDict = makeOpcodeDict(streamInstructions)
opcodeDict = makeOpcodeDict(instructions)

tt_instructions_error = "TT instructions error"


class Program:
	
	def __init__(self):
		pass
	
	def fromBytecode(self, bytecode):
		self.bytecode = array.array("B")
		self.bytecode.fromstring(bytecode)
	
	def fromAssembly(self, assembly):
		self.assembly = assembly
	
	def getBytecode(self):
		if not hasattr(self, "bytecode"):
			self._assemble()
		return self.bytecode.tostring()
	
	def getAssembly(self):
		if not hasattr(self, "assembly"):
			self._disassemble()
		return self.assembly
	
	def _assemble(self):
		xxx
	
	def _disassemble(self):
		assembly = []
		i = 0
		bytecode = self.bytecode
		numBytecode = len(bytecode)
		while i < numBytecode:
			op = bytecode[i]
			arg = 0
			try:
				mnemonic, argbits, argoffset, name = opcodeDict[op]
			except KeyError:
				try:
					mnemonic, argbits, argoffset, name = streamOpcodeDict[op]
				except KeyError:
					raise tt_instructions_error, "illegal opcode: 0x%.2x" % op
				pushbytes = pushwords = 0
				if argbits:
					if mnemonic == "PUSHB":
						pushbytes = op - argoffset + 1
					else:
						pushwords = op - argoffset + 1
				else:
					i = i + 1
					if mnemonic == "NPUSHB":
						pushbytes = bytecode[i]
					else:
						pushwords = bytecode[i]
				i = i + 1
				assembly.append(mnemonic + "[ ]")
				for j in range(pushbytes):
					assembly.append(`bytecode[i]`)
					i = i + 1
				for j in range(0, pushwords, 2):
					assembly.append(`(bytecode[i] << 8) + bytecode[i+1]`)
					i = i + 2
			else:
				if argbits:
					assembly.append(mnemonic + "[%s]" % bitRepr(op - argoffset, argbits))
				else:
					assembly.append(mnemonic + "[ ]")
				i = i + 1
		self.assembly = assembly
		del self.bytecode


fpgm = '@\01476&%\037\023\022\015\014\005\004\002, \260\003%E#E#ah\212 Eh \212#D`D-,KRXED\033!!Y-,  EhD \260\001` E\260Fvh\030\212E`D-,\260\022+\260\002%E\260\002%Ej\260@\213`\260\002%#D!!!-,\260\023+\260\002%E\260\002%Ej\270\377\300\214`\260\002%#D!!!-,\261\000\003%EhTX\260\003%E\260\003%E`h \260\004%#D\260\004%#D\033\260\003% Eh \212#D\260\003%Eh`\260\003%#DY-,\260\003% Eh \212#D\260\003%Eh`\260\003%#D-,KRXED\033!!Y-,F#F`\212\212F# F\212`\212a\270\377\200b# \020#\212\261KK\212pE` \260\000PX\260\001a\270\377\272\213\033\260F\214Y\260\020`h\001:-, E\260\003%FRX?\033!\021Y-,KS#KQZX E\212`D\033!!Y-,KS#KQZX8\033!!Y-'
gpgm = '@\022\011\003\207@\005\200\004\207\000\010\007\202\001\010\004\202\000\010\000\020\320\355\020\336\355\001\020\336\375\032}\336\032\030\375\31610'

p = Program()
p.fromBytecode(fpgm)
for line in p.getAssembly():
	print line

