"""psCharStrings.py -- module implementing various kinds of CharStrings: 
CFF dictionary data and Type1/Type2 CharStrings.
"""

import types
import struct
import string


DEBUG = 0


t1OperandEncoding = [None] * 256
t1OperandEncoding[0:32] = (32) * ["do_operator"]
t1OperandEncoding[32:247] = (247 - 32) * ["read_byte"]
t1OperandEncoding[247:251] = (251 - 247) * ["read_smallInt1"]
t1OperandEncoding[251:255] = (255 - 251) * ["read_smallInt2"]
t1OperandEncoding[255] = "read_longInt"
assert len(t1OperandEncoding) == 256

t2OperandEncoding = t1OperandEncoding[:]
t2OperandEncoding[28] = "read_shortInt"

cffDictOperandEncoding = t2OperandEncoding[:]
cffDictOperandEncoding[29] = "read_longInt"
cffDictOperandEncoding[30] = "read_realNumber"
cffDictOperandEncoding[255] = "reserved"


realNibbles = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
		'.', 'E', 'E-', None, '-']
realNibblesDict = {}
for _i in range(len(realNibbles)):
	realNibblesDict[realNibbles[_i]] = _i


class ByteCodeBase:
	
	def read_byte(self, b0, data, index):
		return b0 - 139, index
	
	def read_smallInt1(self, b0, data, index):
		b1 = ord(data[index])
		return (b0-247)*256 + b1 + 108, index+1
	
	def read_smallInt2(self, b0, data, index):
		b1 = ord(data[index])
		return -(b0-251)*256 - b1 - 108, index+1
	
	def read_shortInt(self, b0, data, index):
		bin = data[index] + data[index+1]
		value, = struct.unpack(">h", bin)
		return value, index+2
	
	def read_longInt(self, b0, data, index):
		bin = data[index] + data[index+1] + data[index+2] + data[index+3]
		value, = struct.unpack(">l", bin)
		return value, index+4
	
	def read_realNumber(self, b0, data, index):
		number = ''
		while 1:
			b = ord(data[index])
			index = index + 1
			nibble0 = (b & 0xf0) >> 4
			nibble1 = b & 0x0f
			if nibble0 == 0xf:
				break
			number = number + realNibbles[nibble0]
			if nibble1 == 0xf:
				break
			number = number + realNibbles[nibble1]
		return float(number), index


def buildOperatorDict(operatorList):
	oper = {}
	opc = {}
	for item in operatorList:
		if len(item) == 2:
			oper[item[0]] = item[1]
		else:
			oper[item[0]] = item[1:]
		if type(item[0]) == types.TupleType:
			opc[item[1]] = item[0]
		else:
			opc[item[1]] = (item[0],)
	return oper, opc


t2Operators = [
#	opcode     name
	(1,        'hstem'),
	(3,        'vstem'),
	(4,        'vmoveto'),
	(5,        'rlineto'),
	(6,        'hlineto'),
	(7,        'vlineto'),
	(8,        'rrcurveto'),
	(10,       'callsubr'),
	(11,       'return'),
	(14,       'endchar'),
	(16,       'blend'),
	(18,       'hstemhm'),
	(19,       'hintmask'),
	(20,       'cntrmask'),
	(21,       'rmoveto'),
	(22,       'hmoveto'),
	(23,       'vstemhm'),
	(24,       'rcurveline'),
	(25,       'rlinecurve'),
	(26,       'vvcurveto'),
	(27,       'hhcurveto'),
#	(28,       'shortint'),  # not really an operator
	(29,       'callgsubr'),
	(30,       'vhcurveto'),
	(31,       'hvcurveto'),
	((12, 3),  'and'),
	((12, 4),  'or'),
	((12, 5),  'not'),
	((12, 8),  'store'),
	((12, 9),  'abs'),
	((12, 10), 'add'),
	((12, 11), 'sub'),
	((12, 12), 'div'),
	((12, 13), 'load'),
	((12, 14), 'neg'),
	((12, 15), 'eq'),
	((12, 18), 'drop'),
	((12, 20), 'put'),
	((12, 21), 'get'),
	((12, 22), 'ifelse'),
	((12, 23), 'random'),
	((12, 24), 'mul'),
	((12, 26), 'sqrt'),
	((12, 27), 'dup'),
	((12, 28), 'exch'),
	((12, 29), 'index'),
	((12, 30), 'roll'),
	((12, 34), 'hflex'),
	((12, 35), 'flex'),
	((12, 36), 'hflex1'),
	((12, 37), 'flex1'),
]


def getIntEncoder(format):
	fourByteOp = chr(255)
	isT1 = 0
	if format == "cff":
		fourByteOp = chr(29)
	elif format == "t1":
		isT1 = 1
	else:
		assert format == "t2"
	
	def encodeInt(value, fourByteOp=fourByteOp, isT1=isT1,
			chr=chr, pack=struct.pack, unpack=struct.unpack):
		if -107 <= value <= 107:
			code = chr(value + 139)
		elif 108 <= value <= 1131:
			value = value - 108
			code = chr((value >> 8) + 247) + chr(value & 0xFF)
		elif -1131 <= value <= -108:
			value = -value - 108
			code = chr((value >> 8) + 251) + chr(value & 0xFF)
		elif not isT1 and -32768 <= value <= 32767:
			code = chr(28) + pack(">h", value)
		else:
			code = fourByteOp + pack(">l", value)
		return code
	
	return encodeInt


encodeIntCFF = getIntEncoder("cff")
encodeIntT1 = getIntEncoder("t1")
encodeIntT2 = getIntEncoder("t2")

def encodeFloat(f):
	s = str(f).upper()
	if s[:2] == "0.":
		s = s[1:]
	elif s[:3] == "-0.":
		s = "-" + s[2:]
	nibbles = []
	while s:
		c = s[0]
		s = s[1:]
		if c == "E" and s[:1] == "-":
			s = s[1:]
			c = "E-"
		nibbles.append(realNibblesDict[c])
	nibbles.append(0xf)
	if len(nibbles) % 2:
		nibbles.append(0xf)
	d = chr(30)
	for i in range(0, len(nibbles), 2):
		d = d + chr(nibbles[i] << 4 | nibbles[i+1])
	return d


class CharStringCompileError(Exception): pass


class T2CharString(ByteCodeBase):
	
	operandEncoding = t2OperandEncoding
	operators, opcodes = buildOperatorDict(t2Operators)
	
	def __init__(self, bytecode=None, program=None, subrs=None, globalSubrs=None):
		if program is None:
			program = []
		self.bytecode = bytecode
		self.program = program
		self.subrs = subrs
		self.globalSubrs = globalSubrs
	
	def __repr__(self):
		if self.bytecode is None:
			return "<%s (source) at %x>" % (self.__class__.__name__, id(self))
		else:
			return "<%s (bytecode) at %x>" % (self.__class__.__name__, id(self))
	
	def decompile(self):
		if not self.needsDecompilation():
			return
		decompiler = SimpleT2Decompiler(self.subrs, self.globalSubrs)
		decompiler.reset()
		decompiler.execute(self)
	
	def compile(self):
		if self.bytecode is not None:
			return
		if self.program[-1] not in ("endchar", "return", "callsubr", "callgsubr", "seac"):
			print "XXX", self.program
			assert 0, "illegal CharString"
		bytecode = []
		opcodes = self.opcodes
		program = self.program
		i = 0
		end = len(program)
		while i < end:
			token = program[i]
			i = i + 1
			tp = type(token)
			if tp == types.StringType:
				try:
					bytecode.extend(map(chr, opcodes[token]))
				except KeyError:
					raise CharStringCompileError, "illegal operator: %s" % token
				if token in ('hintmask', 'cntrmask'):
					bytecode.append(program[i])  # hint mask
					i = i + 1
			elif tp == types.IntType:
				bytecode.append(encodeIntT2(token))
			else:
				assert 0, "unsupported type: %s" % tp
		try:
			bytecode = "".join(bytecode)
		except TypeError:
			print bytecode
			raise
		self.setBytecode(bytecode)
	
	def needsDecompilation(self):
		return self.bytecode is not None
	
	def setProgram(self, program):
		self.program = program
		self.bytecode = None
	
	def setBytecode(self, bytecode):
		self.bytecode = bytecode
		self.program = None
	
	def getToken(self, index, 
			len=len, ord=ord, getattr=getattr, type=type, StringType=types.StringType):
		if self.bytecode is not None:
			if index >= len(self.bytecode):
				return None, 0, 0
			b0 = ord(self.bytecode[index])
			index = index + 1
			code = self.operandEncoding[b0]
			handler = getattr(self, code)
			token, index = handler(b0, self.bytecode, index)
		else:
			if index >= len(self.program):
				return None, 0, 0
			token = self.program[index]
			index = index + 1
		isOperator = type(token) == StringType
		return token, isOperator, index
	
	def getBytes(self, index, nBytes):
		if self.bytecode is not None:
			newIndex = index + nBytes
			bytes = self.bytecode[index:newIndex]
			index = newIndex
		else:
			bytes = self.program[index]
			index = index + 1
		assert len(bytes) == nBytes
		return bytes, index
	
	def do_operator(self, b0, data, index):
		if b0 == 12:
			op = (b0, ord(data[index]))
			index = index+1
		else:
			op = b0
		operator = self.operators[op]
		return operator, index
	
	def toXML(self, xmlWriter):
		from fontTools.misc.textTools import num2binary
		if self.bytecode is not None:
			xmlWriter.dumphex(self.bytecode)
		else:
			index = 0
			args = []
			while 1:
				token, isOperator, index = self.getToken(index)
				if token is None:
					break
				if isOperator:
					args = map(str, args)
					if token in ('hintmask', 'cntrmask'):
						hintMask, isOperator, index = self.getToken(index)
						bits = []
						for byte in hintMask:
							bits.append(num2binary(ord(byte), 8))
						hintMask = string.join(bits, "")
						line = string.join(args + [token, hintMask], " ")
					else:
						line = string.join(args + [token], " ")
					xmlWriter.write(line)
					xmlWriter.newline()
					args = []
				else:
					args.append(token)
	
	def fromXML(self, (name, attrs, content)):
		from fontTools.misc.textTools import binary2num
		content = "".join(content)
		content = content.split()
		program = []
		end = len(content)
		i = 0
		while i < end:
			token = content[i]
			i = i + 1
			try:
				token = int(token)
			except ValueError:
				program.append(token)
				if token in ('hintmask', 'cntrmask'):
					mask = content[i]
					maskBytes = ""
					for j in range(0, len(mask), 8):
						maskBytes = maskBytes + chr(binary2num(mask[j:j+8]))
					program.append(maskBytes)
					i = i + 1
			else:
				program.append(token)
		self.setProgram(program)


t1Operators = [
#	opcode     name
	(1,        'hstem'),
	(3,        'vstem'),
	(4,        'vmoveto'),
	(5,        'rlineto'),
	(6,        'hlineto'),
	(7,        'vlineto'),
	(8,        'rrcurveto'),
	(9,        'closepath'),
	(10,       'callsubr'),
	(11,       'return'),
	(13,       'hsbw'),
	(14,       'endchar'),
	(21,       'rmoveto'),
	(22,       'hmoveto'),
	(30,       'vhcurveto'),
	(31,       'hvcurveto'),
	((12, 0),  'dotsection'),
	((12, 1),  'vstem3'),
	((12, 2),  'hstem3'),
	((12, 6),  'seac'),
	((12, 7),  'sbw'),
	((12, 12), 'div'),
	((12, 16), 'callothersubr'),
	((12, 17), 'pop'),
	((12, 33), 'setcurrentpoint'),
]

class T1CharString(T2CharString):
	
	operandEncoding = t1OperandEncoding
	operators, opcodes = buildOperatorDict(t1Operators)
	
	def decompile(self):
		if self.program is not None:
			return
		program = []
		index = 0
		while 1:
			token, isOperator, index = self.getToken(index)
			if token is None:
				break
			program.append(token)
		self.setProgram(program)


class SimpleT2Decompiler:
	
	def __init__(self, localSubrs, globalSubrs):
		self.localSubrs = localSubrs
		self.localBias = calcSubrBias(localSubrs)
		self.globalSubrs = globalSubrs
		self.globalBias = calcSubrBias(globalSubrs)
		self.reset()
	
	def reset(self):
		self.callingStack = []
		self.operandStack = []
		self.hintCount = 0
		self.hintMaskBytes = 0
	
	def execute(self, charString):
		self.callingStack.append(charString)
		needsDecompilation = charString.needsDecompilation()
		if needsDecompilation:
			program = []
			pushToProgram = program.append
		else:
			pushToProgram = lambda x: None
		pushToStack = self.operandStack.append
		index = 0
		while 1:
			token, isOperator, index = charString.getToken(index)
			if token is None:
				break  # we're done!
			pushToProgram(token)
			if isOperator:
				handlerName = "op_" + token
				if hasattr(self, handlerName):
					handler = getattr(self, handlerName)
					rv = handler(index)
					if rv:
						hintMaskBytes, index = rv
						pushToProgram(hintMaskBytes)
				else:
					self.popall()
			else:
				pushToStack(token)
		if needsDecompilation:
			charString.setProgram(program)
			if program[-1] not in ("endchar", "return", "callsubr", "callgsubr", "seac"):
				print "XXX", program
			assert program[-1] in ("endchar", "return", "callsubr", "callgsubr", "seac")
		del self.callingStack[-1]
	
	def pop(self):
		value = self.operandStack[-1]
		del self.operandStack[-1]
		return value
	
	def popall(self):
		stack = self.operandStack[:]
		self.operandStack[:] = []
		return stack
	
	def push(self, value):
		self.operandStack.append(value)
	
	def op_return(self, index):
		if self.operandStack:
			pass
	
	def op_endchar(self, index):
		pass
	
	def op_callsubr(self, index):
		subrIndex = self.pop()
		subr = self.localSubrs[subrIndex+self.localBias]
		self.execute(subr)
	
	def op_callgsubr(self, index):
		subrIndex = self.pop()
		subr = self.globalSubrs[subrIndex+self.globalBias]
		self.execute(subr)
	
	def op_hstem(self, index):
		self.countHints()
	def op_vstem(self, index):
		self.countHints()
	def op_hstemhm(self, index):
		self.countHints()
	def op_vstemhm(self, index):
		self.countHints()
	
	def op_hintmask(self, index):
		if not self.hintMaskBytes:
			self.countHints()
			self.hintMaskBytes = (self.hintCount + 7) / 8
		hintMaskBytes, index = self.callingStack[-1].getBytes(index, self.hintMaskBytes)
		return hintMaskBytes, index
	
	op_cntrmask = op_hintmask
	
	def countHints(self):
		args = self.popall()
		self.hintCount = self.hintCount + len(args) / 2


class T2OutlineExtractor(SimpleT2Decompiler):
	
	def __init__(self, localSubrs, globalSubrs, nominalWidthX, defaultWidthX):
		SimpleT2Decompiler.__init__(self, localSubrs, globalSubrs)
		self.nominalWidthX = nominalWidthX
		self.defaultWidthX = defaultWidthX
	
	def reset(self):
		import Numeric
		SimpleT2Decompiler.reset(self)
		self.hints = []
		self.gotWidth = 0
		self.width = 0
		self.currentPoint = Numeric.array((0, 0), Numeric.Int16)
		self.contours = []
	
	def getContours(self):
		return self.contours
	
	def newPath(self):
		self.contours.append([[], [], 0])
	
	def closePath(self):
		if self.contours and self.contours[-1][2] == 0:
			self.contours[-1][2] = 1
	
	def appendPoint(self, point, isPrimary):
		import Numeric
		point = self.currentPoint + Numeric.array(point, Numeric.Int16)
		if not self.contours or self.contours[-1][2]:
			# The subpath doesn't start with a moveto. Not sure whether
			# this is legal, but apparently it usually works.
			self.newPath()
			self.appendPoint((0, 0), 1)
		self.currentPoint = point
		points, flags, isClosed = self.contours[-1]
		points.append(point)
		flags.append(isPrimary)
	
	def popallWidth(self, evenOdd=0):
		args = self.popall()
		if not self.gotWidth:
			if evenOdd ^ (len(args) % 2):
				self.width = self.nominalWidthX + args[0]
				args = args[1:]
			else:
				self.width = self.defaultWidthX
			self.gotWidth = 1
		return args
	
	def countHints(self):
		args = self.popallWidth()
		self.hintCount = self.hintCount + len(args) / 2
	
	#
	# hint operators
	#
	#def op_hstem(self, index):
	#	self.countHints()
	#def op_vstem(self, index):
	#	self.countHints()
	#def op_hstemhm(self, index):
	#	self.countHints()
	#def op_vstemhm(self, index):
	#	self.countHints()
	#def op_hintmask(self, index):
	#	self.countHints()
	#def op_cntrmask(self, index):
	#	self.countHints()
	
	#
	# path constructors, moveto
	#
	def op_rmoveto(self, index):
		self.closePath()
		self.newPath()
		self.appendPoint(self.popallWidth(), 1)
	def op_hmoveto(self, index):
		self.closePath()
		self.newPath()
		self.appendPoint((self.popallWidth(1)[0], 0), 1)
	def op_vmoveto(self, index):
		self.closePath()
		self.newPath()
		self.appendPoint((0, self.popallWidth(1)[0]), 1)
	def op_endchar(self, index):
		self.closePath()
	
	#
	# path constructors, lines
	#
	def op_rlineto(self, index):
		args = self.popall()
		for i in range(0, len(args), 2):
			point = args[i:i+2]
			self.appendPoint(point, 1)
	
	def op_hlineto(self, index):
		self.alternatingLineto(1)
	def op_vlineto(self, index):
		self.alternatingLineto(0)
	
	#
	# path constructors, curves
	#
	def op_rrcurveto(self, index):
		"""{dxa dya dxb dyb dxc dyc}+ rrcurveto"""
		args = self.popall()
		for i in range(0, len(args), 6):
			dxa, dya, dxb, dyb, dxc, dyc, = args[i:i+6]
			self.rrcurveto((dxa, dya), (dxb, dyb), (dxc, dyc))
	
	def op_rcurveline(self, index):
		"""{dxa dya dxb dyb dxc dyc}+ dxd dyd rcurveline"""
		args = self.popall()
		for i in range(0, len(args)-2, 6):
			dxb, dyb, dxc, dyc, dxd, dyd = args[i:i+6]
			self.rrcurveto((dxb, dyb), (dxc, dyc), (dxd, dyd))
		self.appendPoint(args[-2:], 1)
	
	def op_rlinecurve(self, index):
		"""{dxa dya}+ dxb dyb dxc dyc dxd dyd rlinecurve"""
		args = self.popall()
		lineArgs = args[:-6]
		for i in range(0, len(lineArgs), 2):
			self.appendPoint(lineArgs[i:i+2], 1)
		dxb, dyb, dxc, dyc, dxd, dyd = args[-6:]
		self.rrcurveto((dxb, dyb), (dxc, dyc), (dxd, dyd))
	
	def op_vvcurveto(self, index):
		"dx1? {dya dxb dyb dyc}+ vvcurveto"
		args = self.popall()
		if len(args) % 2:
			dx1 = args[0]
			args = args[1:]
		else:
			dx1 = 0
		for i in range(0, len(args), 4):
			dya, dxb, dyb, dyc = args[i:i+4]
			self.rrcurveto((dx1, dya), (dxb, dyb), (0, dyc))
			dx1 = 0
	
	def op_hhcurveto(self, index):
		"""dy1? {dxa dxb dyb dxc}+ hhcurveto"""
		args = self.popall()
		if len(args) % 2:
			dy1 = args[0]
			args = args[1:]
		else:
			dy1 = 0
		for i in range(0, len(args), 4):
			dxa, dxb, dyb, dxc = args[i:i+4]
			self.rrcurveto((dxa, dy1), (dxb, dyb), (dxc, 0))
			dy1 = 0
	
	def op_vhcurveto(self, index):
		"""dy1 dx2 dy2 dx3 {dxa dxb dyb dyc dyd dxe dye dxf}* dyf? vhcurveto (30)
		{dya dxb dyb dxc dxd dxe dye dyf}+ dxf? vhcurveto
		"""
		args = self.popall()
		while args:
			args = self.vcurveto(args)
			if args:
				args = self.hcurveto(args)
	
	def op_hvcurveto(self, index):
		"""dx1 dx2 dy2 dy3 {dya dxb dyb dxc dxd dxe dye dyf}* dxf?
		{dxa dxb dyb dyc dyd dxe dye dxf}+ dyf?
		"""
		args = self.popall()
		while args:
			args = self.hcurveto(args)
			if args:
				args = self.vcurveto(args)
	
	#
	# path constructors, flex
	#
	def op_hflex(self, index):
		XXX
	def op_flex(self, index):
		XXX
	def op_hflex1(self, index):
		XXX
	def op_flex1(self, index):
		XXX
	
	#
	# MultipleMaster. Well...
	#
	def op_blend(self, index):
		XXX
	
	# misc
	def op_and(self, index):
		XXX
	def op_or(self, index):
		XXX
	def op_not(self, index):
		XXX
	def op_store(self, index):
		XXX
	def op_abs(self, index):
		XXX
	def op_add(self, index):
		XXX
	def op_sub(self, index):
		XXX
	def op_div(self, index):
		num2 = self.pop()
		num1 = self.pop()
		d1 = num1/num2
		d2 = float(num1)/num2
		if d1 == d2:
			self.push(d1)
		else:
			self.push(d2)
	def op_load(self, index):
		XXX
	def op_neg(self, index):
		XXX
	def op_eq(self, index):
		XXX
	def op_drop(self, index):
		XXX
	def op_put(self, index):
		XXX
	def op_get(self, index):
		XXX
	def op_ifelse(self, index):
		XXX
	def op_random(self, index):
		XXX
	def op_mul(self, index):
		XXX
	def op_sqrt(self, index):
		XXX
	def op_dup(self, index):
		XXX
	def op_exch(self, index):
		XXX
	def op_index(self, index):
		XXX
	def op_roll(self, index):
		XXX
	
	#
	# miscelaneous helpers
	#
	def alternatingLineto(self, isHorizontal):
		args = self.popall()
		for arg in args:
			if isHorizontal:
				point = (arg, 0)
			else:
				point = (0, arg)
			self.appendPoint(point, 1)
			isHorizontal = not isHorizontal
	
	def rrcurveto(self, p1, p2, p3):
		self.appendPoint(p1, 0)
		self.appendPoint(p2, 0)
		self.appendPoint(p3, 1)
	
	def vcurveto(self, args):
		dya, dxb, dyb, dxc = args[:4]
		args = args[4:]
		if len(args) == 1:
			dyc = args[0]
			args = []
		else:
			dyc = 0
		self.rrcurveto((0, dya), (dxb, dyb), (dxc, dyc))
		return args
	
	def hcurveto(self, args):
		dxa, dxb, dyb, dyc = args[:4]
		args = args[4:]
		if len(args) == 1:
			dxc = args[0]
			args = []
		else:
			dxc = 0
		self.rrcurveto((dxa, 0), (dxb, dyb), (dxc, dyc))
		return args


class T1OutlineExtractor(T2OutlineExtractor):
	
	def __init__(self, subrs):
		self.subrs = subrs
		self.reset()
	
	def reset(self):
		self.flexing = 0
		self.width = 0
		self.sbx = 0
		T2OutlineExtractor.reset(self)
	
	def popallWidth(self, evenOdd=0):
		return self.popall()
	
	def exch(self):
		stack = self.operandStack
		stack[-1], stack[-2] = stack[-2], stack[-1]
	
	#
	# path constructors
	#
	def op_rmoveto(self, index):
		if self.flexing:
			return
		self.newPath()
		self.appendPoint(self.popall(), 1)
	def op_hmoveto(self, index):
		if self.flexing:
			# We must add a parameter to the stack if we are flexing
			self.push(0)
			return
		self.newPath()
		self.appendPoint((self.popall()[0], 0), 1)
	def op_vmoveto(self, index):
		if self.flexing:
			# We must add a parameter to the stack if we are flexing
			self.push(0)
			self.exch()
			return
		self.newPath()
		self.appendPoint((0, self.popall()[0]), 1)
	def op_closepath(self, index):
		self.closePath()
	def op_setcurrentpoint(self, index):
		args = self.popall()
		x, y = args
		self.currentPoint[0] = x
		self.currentPoint[1] = y
	
	def op_endchar(self, index):
		self.closePath()
	
	def op_hsbw(self, index):
		sbx, wx = self.popall()
		self.width = wx
		self.sbx = sbx
		self.currentPoint[0] = sbx
	def op_sbw(self, index):
		self.popall()  # XXX
	
	#
	def op_callsubr(self, index):
		subrIndex = self.pop()
		subr = self.subrs[subrIndex]
		self.execute(subr)
	def op_callothersubr(self, index):
		subrIndex = self.pop()
		nArgs = self.pop()
		#print nArgs, subrIndex, "callothersubr"
		if subrIndex == 0 and nArgs == 3:
			self.doFlex()
			self.flexing = 0
		elif subrIndex == 1 and nArgs == 0:
			self.flexing = 1
		# ignore...
	def op_pop(self, index):
		pass  # ignore...
	
	def doFlex(self):
		finaly = self.pop()
		finalx = self.pop()
		self.pop()	# flex height is unused
		
		p3y = self.pop()
		p3x = self.pop()
		bcp4y = self.pop()
		bcp4x = self.pop()
		bcp3y = self.pop()
		bcp3x = self.pop()
		p2y = self.pop()
		p2x = self.pop()
		bcp2y = self.pop()
		bcp2x = self.pop()
		bcp1y = self.pop()
		bcp1x = self.pop()
		rpy = self.pop()
		rpx = self.pop()
		
		# call rrcurveto
		self.push(bcp1x+rpx)
		self.push(bcp1y+rpy)
		self.push(bcp2x)
		self.push(bcp2y)
		self.push(p2x)
		self.push(p2y)
		self.op_rrcurveto(None)
		
		# call rrcurveto
		self.push(bcp3x)
		self.push(bcp3y)
		self.push(bcp4x)
		self.push(bcp4y)
		self.push(p3x)
		self.push(p3y)
		self.op_rrcurveto(None)
		
		# Push back final coords so subr 0 can find them
		self.push(finalx)
		self.push(finaly)
	
	def op_dotsection(self, index):
		self.popall()  # XXX
	def op_hstem3(self, index):
		self.popall()  # XXX
	def op_seac(self, index):
		"asb adx ady bchar achar seac"
		asb, adx, ady, bchar, achar = self.popall()  # XXX
		self.contours.append([(asb, adx, ady, bchar, achar), None, -1])
	def op_vstem3(self, index):
		self.popall()  # XXX


class DictDecompiler(ByteCodeBase):
	
	operandEncoding = cffDictOperandEncoding
	
	def __init__(self, strings):
		self.stack = []
		self.strings = strings
		self.dict = {}
	
	def getDict(self):
		assert len(self.stack) == 0, "non-empty stack"
		return self.dict
	
	def decompile(self, data):
		index = 0
		lenData = len(data)
		push = self.stack.append
		while index < lenData:
			b0 = ord(data[index])
			index = index + 1
			code = self.operandEncoding[b0]
			handler = getattr(self, code)
			value, index = handler(b0, data, index)
			if value is not None:
				push(value)
	
	def pop(self):
		value = self.stack[-1]
		del self.stack[-1]
		return value
	
	def popall(self):
		all = self.stack[:]
		del self.stack[:]
		return all
	
	def do_operator(self, b0, data, index):
		if b0 == 12:
			op = (b0, ord(data[index]))
			index = index+1
		else:
			op = b0
		operator, argType = self.operators[op]
		self.handle_operator(operator, argType)
		return None, index
	
	def handle_operator(self, operator, argType):
		if type(argType) == type(()):
			value = ()
			for i in range(len(argType)-1, -1, -1):
				arg = argType[i]
				arghandler = getattr(self, "arg_" + arg)
				value = (arghandler(operator),) + value
		else:
			arghandler = getattr(self, "arg_" + argType)
			value = arghandler(operator)
		self.dict[operator] = value
	
	def arg_number(self, name):
		return self.pop()
	def arg_SID(self, name):
		return self.strings[self.pop()]
	def arg_array(self, name):
		return self.popall()
	def arg_delta(self, name):
		out = []
		current = 0
		for v in self.popall():
			current = current + v
			out.append(current)
		return out


def calcSubrBias(subrs):
	nSubrs = len(subrs)
	if nSubrs < 1240:
		bias = 107
	elif nSubrs < 33900:
		bias = 1131
	else:
		bias = 32768
	return bias

