"""cffLib.py -- read/write tools for Adobe CFF fonts."""

#
# $Id: cffLib.py,v 1.21 2002-05-23 21:50:36 jvr Exp $
#

import struct, sstruct
import string
from types import FloatType, ListType, TupleType
from fontTools.misc import psCharStrings


DEBUG = 0


cffHeaderFormat = """
	major:   B
	minor:   B
	hdrSize: B
	offSize: B
"""

class CFFFontSet:
	
	def __init__(self):
		pass
	
	def decompile(self, file):
		sstruct.unpack(cffHeaderFormat, file.read(4), self)
		assert self.major == 1 and self.minor == 0, \
				"unknown CFF format: %d.%d" % (self.major, self.minor)
		
		file.seek(self.hdrSize)
		self.fontNames = list(Index(file, "fontNames"))
		self.topDictIndex = TopDictIndex(file)
		self.strings = IndexedStrings(file)
		self.GlobalSubrs = GlobalSubrsIndex(file, name="GlobalSubrsIndex")
		self.topDictIndex.strings = self.strings
		self.topDictIndex.GlobalSubrs = self.GlobalSubrs
	
	def __len__(self):
		return len(self.fontNames)
	
	def keys(self):
		return self.fontNames[:]
	
	def values(self):
		return self.topDictIndex
	
	def __getitem__(self, name):
		try:
			index = self.fontNames.index(name)
		except ValueError:
			raise KeyError, name
		return self.topDictIndex[index]
	
	def compile(self, file):
		strings = IndexedStrings()
		writer = CFFWriter()
		writer.add(sstruct.pack(cffHeaderFormat, self))
		fontNames = Index()
		for name in self.fontNames:
			fontNames.append(name)
		writer.add(fontNames.getCompiler(strings, None))
		topCompiler = self.topDictIndex.getCompiler(strings, None)
		writer.add(topCompiler)
		writer.add(strings.getCompiler())
		writer.add(self.GlobalSubrs.getCompiler(strings, None))
		
		for child in topCompiler.getChildren(strings):
			writer.add(child)
		
		print writer.data
		
		writer.toFile(file)
	
	def toXML(self, xmlWriter, progress=None):
		xmlWriter.newline()
		for fontName in self.fontNames:
			xmlWriter.begintag("CFFFont", name=fontName)
			xmlWriter.newline()
			font = self[fontName]
			font.toXML(xmlWriter, progress)
			xmlWriter.endtag("CFFFont")
			xmlWriter.newline()
		xmlWriter.newline()
		xmlWriter.begintag("GlobalSubrs")
		xmlWriter.newline()
		self.GlobalSubrs.toXML(xmlWriter, progress)
		xmlWriter.endtag("GlobalSubrs")
		xmlWriter.newline()
		xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content)):
		xxx


class CFFWriter:
	
	def __init__(self):
		self.data = []
	
	def add(self, table):
		self.data.append(table)
	
	def toFile(self, file):
		lastPosList = None
		count = 1
		while 1:
			print "XXX iteration", count
			count += 1
			pos = 0
			posList = [pos]
			for item in self.data:
				if hasattr(item, "setPos"):
					item.setPos(pos)
				if hasattr(item, "getDataLength"):
					pos = pos + item.getDataLength()
				else:
					pos = pos + len(item)
				posList.append(pos)
			if posList == lastPosList:
				break
			lastPosList = posList
		begin = file.tell()
		posList = [0]
		for item in self.data:
			if hasattr(item, "toFile"):
				item.toFile(file)
			else:
				file.write(item)
			posList.append(file.tell() - begin)
		if posList != lastPosList:
			print "++++"
			print posList
			print lastPosList
		assert posList == lastPosList


def calcOffSize(largestOffset):
	if largestOffset < 0x100:
		offSize = 1
	elif largestOffset < 0x10000:
		offSize = 2
	elif largestOffset < 0x1000000:
		offSize = 3
	else:
		offSize = 4
	return offSize


class IndexCompiler:
	
	def __init__(self, items, strings, parent):
		self.items = self.getItems(items, strings)
		self.parent = parent
	
	def getItems(self, items, strings):
		return items
	
	def getOffsets(self):
		pos = 1
		offsets = [pos]
		for item in self.items:
			if hasattr(item, "getDataLength"):
				pos = pos + item.getDataLength()
			else:
				pos = pos + len(item)
			offsets.append(pos)
		return offsets
	
	def getDataLength(self):
		lastOffset = self.getOffsets()[-1]
		offSize = calcOffSize(lastOffset)
		dataLength = (
			2 +                                # count
			1 +                                # offSize
			(len(self.items) + 1) * offSize +  # the offsets
			lastOffset - 1                     # size of object data
		)
		return dataLength
	
	def toFile(self, file):
		size = self.getDataLength()
		start = file.tell()
		offsets = self.getOffsets()
		writeCard16(file, len(self.items))
		offSize = calcOffSize(offsets[-1])
		writeCard8(file, offSize)
		offSize = -offSize
		pack = struct.pack
		for offset in offsets:
			binOffset = pack(">l", offset)[offSize:]
			assert len(binOffset) == -offSize
			file.write(binOffset)
		for item in self.items:
			if hasattr(item, "toFile"):
				item.toFile(file)
			else:
				file.write(item)
		assert start + size == file.tell()


class IndexedStringsCompiler(IndexCompiler):
	
	def getItems(self, items, strings):
		return items.strings


class TopDictIndexCompiler(IndexCompiler):
	
	def getItems(self, items, strings):
		out = []
		for item in items:
			out.append(item.getCompiler(strings, self))
		return out
	
	def getChildren(self, strings):
		children = []
		for topDict in self.items:
			children.extend(topDict.getChildren(strings))
		return children


class GlobalSubrsCompiler(IndexCompiler):
	def getItems(self, items, strings):
		out = []
		for cs in items:
			cs.compile()
			out.append(cs.bytecode)
		return out

class SubrsCompiler(GlobalSubrsCompiler):
	def setPos(self, pos):
		offset = pos - self.parent.pos
		self.parent.rawDict["Subrs"] = offset

class CharStringsCompiler(GlobalSubrsCompiler):
	def setPos(self, pos):
		self.parent.rawDict["CharStrings"] = pos


class Index:
	
	"""This class represents what the CFF spec calls an INDEX."""
	
	compilerClass = IndexCompiler
	
	def __init__(self, file=None, name=None):
		if name is None:
			name = self.__class__.__name__
		if file is None:
			self.items = []
			return
		if DEBUG:
			print "loading %s at %s" % (name, file.tell())
		self.file = file
		count = readCard16(file)
		self.count = count
		self.items = [None] * count
		if count == 0:
			self.items = []
			return
		offSize = readCard8(file)
		if DEBUG:
			print "    index count: %s offSize: %s" % (count, offSize)
		assert offSize <= 4, "offSize too large: %s" % offSize
		self.offsets = offsets = []
		pad = '\0' * (4 - offSize)
		for index in range(count+1):
			chunk = file.read(offSize)
			chunk = pad + chunk
			offset, = struct.unpack(">L", chunk)
			offsets.append(int(offset))
		self.offsetBase = file.tell() - 1
		file.seek(self.offsetBase + offsets[-1])  # pretend we've read the whole lot
		if DEBUG:
			print "    end of %s at %s" % (name, file.tell())
	
	def __len__(self):
		return len(self.items)
	
	def __getitem__(self, index):
		item = self.items[index]
		if item is not None:
			return item
		offset = self.offsets[index] + self.offsetBase
		size = self.offsets[index+1] - self.offsets[index]
		file = self.file
		file.seek(offset)
		data = file.read(size)
		assert len(data) == size
		item = self.produceItem(index, data, file, offset, size)
		self.items[index] = item
		return item
	
	def produceItem(self, index, data, file, offset, size):
		return data
	
	def append(self, item):
		self.items.append(item)
	
	def getCompiler(self, strings, parent):
		return self.compilerClass(self, strings, parent)


class GlobalSubrsIndex(Index):
	
	compilerClass = GlobalSubrsCompiler
	
	def __init__(self, file=None, globalSubrs=None, private=None, fdSelect=None, fdArray=None,
			name=None):
		Index.__init__(self, file, name)
		self.globalSubrs = globalSubrs
		self.private = private
		self.fdSelect = fdSelect
		self.fdArray = fdArray
	
	def produceItem(self, index, data, file, offset, size):
		if self.private is not None:
			private = self.private
		elif self.fdArray is not None:
			private = self.fdArray[self.fdSelect[index]].Private
		else:
			private = None
		if hasattr(private, "Subrs"):
			subrs = private.Subrs
		else:
			subrs = []
		return psCharStrings.T2CharString(data, subrs=subrs, globalSubrs=self.globalSubrs)
	
	def toXML(self, xmlWriter, progress):
		fdSelect = self.fdSelect
		for i in range(len(self)):
			xmlWriter.begintag("CharString", index=i)
			xmlWriter.newline()
			self[i].toXML(xmlWriter)
			xmlWriter.endtag("CharString")
			xmlWriter.newline()
	
	def getItemAndSelector(self, index):
		fdSelect = self.fdSelect
		if fdSelect is None:
			sel = None
		else:
			sel = fdSelect[index]
		return self[index], sel

class SubrsIndex(GlobalSubrsIndex):
	compilerClass = SubrsCompiler


class TopDictIndex(Index):
	
	compilerClass = TopDictIndexCompiler
	
	def produceItem(self, index, data, file, offset, size):
		top = TopDict(self.strings, file, offset, self.GlobalSubrs)
		top.decompile(data)
		return top
	
	def toXML(self, xmlWriter, progress):
		for i in range(len(self)):
			xmlWriter.begintag("FontDict", index=i)
			xmlWriter.newline()
			self[i].toXML(xmlWriter, progress)
			xmlWriter.endtag("FontDict")
			xmlWriter.newline()


class CharStrings:
	
	def __init__(self, file, charset, globalSubrs, private, fdSelect, fdArray):
		self.charStringsIndex = SubrsIndex(file, globalSubrs, private, fdSelect, fdArray)
		self.nameToIndex = nameToIndex = {}
		for i in range(len(charset)):
			nameToIndex[charset[i]] = i
	
	def keys(self):
		return self.nameToIndex.keys()
	
	def values(self):
		return self.charStringsIndex
	
	def has_key(self, name):
		return self.nameToIndex.has_key(name)
	
	def __len__(self):
		return len(self.charStringsIndex)
	
	def __getitem__(self, name):
		index = self.nameToIndex[name]
		return self.charStringsIndex[index]
	
	def getItemAndSelector(self, name):
		index = self.nameToIndex[name]
		return self.charStringsIndex.getItemAndSelector(index)
	
	def toXML(self, xmlWriter, progress):
		names = self.keys()
		names.sort()
		for name in names:
			charStr, fdSelect = self.getItemAndSelector(name)
			if fdSelect is None:
				xmlWriter.begintag("CharString", name=name)
			else:
				xmlWriter.begintag("CharString",
						[('name', name), ('fdSelect', fdSelect)])
			xmlWriter.newline()
			self[name].toXML(xmlWriter)
			xmlWriter.endtag("CharString")
			xmlWriter.newline()


def readCard8(file):
	return ord(file.read(1))

def readCard16(file):
	value, = struct.unpack(">H", file.read(2))
	return value

def writeCard8(file, value):
	file.write(chr(value))

def writeCard16(file, value):
	file.write(struct.pack(">H", value))

def packCard8(value):
	return chr(value)

def packCard16(value):
	return struct.pack(">H", value)

def buildOperatorDict(table):
	d = {}
	for op, name, arg, default, conv in table:
		d[op] = (name, arg)
	return d

def buildOpcodeDict(table):
	d = {}
	for op, name, arg, default, conv in table:
		if type(op) == TupleType:
			op = chr(op[0]) + chr(op[1])
		else:
			op = chr(op)
		d[name] = (op, arg)
	return d

def buildOrder(table):
	l = []
	for op, name, arg, default, conv in table:
		l.append(name)
	return l

def buildDefaults(table):
	d = {}
	for op, name, arg, default, conv in table:
		if default is not None:
			d[name] = default
	return d

def buildConverters(table):
	d = {}
	for op, name, arg, default, conv in table:
		d[name] = conv
	return d


class BaseConverter:
	def read(self, parent, value):
		return value
	def write(self, parent, value):
		return value
	def xmlWrite(self, xmlWriter, name, value):
		xmlWriter.begintag(name)
		xmlWriter.newline()
		value.toXML(xmlWriter, None)
		xmlWriter.endtag(name)
		xmlWriter.newline()

class PrivateDictConverter(BaseConverter):
	def read(self, parent, value):
		size, offset = value
		file = parent.file
		pr = PrivateDict(parent.strings, file, offset)
		file.seek(offset)
		data = file.read(size)
		len(data) == size
		pr.decompile(data)
		return pr
	def write(self, parent, value):
		return (0, 0)  # dummy value

class SubrsConverter(BaseConverter):
	def read(self, parent, value):
		file = parent.file
		file.seek(parent.offset + value)  # Offset(self)
		return SubrsIndex(file, name="SubrsIndex")
	def write(self, parent, value):
		return 0  # dummy value

class CharStringsConverter(BaseConverter):
	def read(self, parent, value):
		file = parent.file
		charset = parent.charset
		globalSubrs = parent.GlobalSubrs
		if hasattr(parent, "ROS"):
			fdSelect, fdArray = parent.FDSelect, parent.FDArray
			private = None
		else:
			fdSelect, fdArray = None, None
			private = parent.Private
		file.seek(value)  # Offset(0)
		return CharStrings(file, charset, globalSubrs, private, fdSelect, fdArray)
	def write(self, parent, value):
		return 0  # dummy value

class CharsetConverter:
	def read(self, parent, value):
		isCID = hasattr(parent, "ROS")
		if value > 2:
			numGlyphs = parent.numGlyphs
			file = parent.file
			file.seek(value)
			if DEBUG:
				print "loading charset at %s" % value
			format = readCard8(file)
			if format == 0:
				charset =parseCharset0(numGlyphs, file, parent.strings)
			elif format == 1 or format == 2:
				charset = parseCharset(numGlyphs, file, parent.strings, isCID, format)
			else:
				raise NotImplementedError
			assert len(charset) == numGlyphs
			if DEBUG:
				print "    charset end at %s" % file.tell()
		else:
			if isCID or not hasattr(parent, "CharStrings"):
				assert value == 0
				charset = None
			elif value == 0:
				charset = ISOAdobe
			elif value == 1:
				charset = Expert
			elif value == 2:
				charset = ExpertSubset
			# self.charset:
			#   0: ISOAdobe (or CID font!)
			#   1: Expert
			#   2: ExpertSubset
			charset = None  # 
		return charset
	def write(self, parent, value):
		return 0  # dummy value
	def xmlWrite(self, xmlWriter, name, value):
		# XXX GlyphOrder needs to be stored *somewhere*, but not here...
		xmlWriter.simpletag("charset", value=value)
		xmlWriter.newline()


class CharsetCompiler:
	
	def __init__(self, strings, charset, parent):
		assert charset[0] == '.notdef'
		format = 0  # XXX!
		data = [packCard8(format)]
		for name in charset[1:]:
			data.append(packCard16(strings.getSID(name)))
		self.data = "".join(data)
		self.parent = parent
	
	def setPos(self, pos):
		self.parent.rawDict["charset"] = pos
	
	def getDataLength(self):
		return len(self.data)
	
	def toFile(self, file):
		file.write(self.data)


def parseCharset0(numGlyphs, file, strings):
	charset = [".notdef"]
	for i in range(numGlyphs - 1):
		SID = readCard16(file)
		charset.append(strings[SID])
	return charset

def parseCharset(numGlyphs, file, strings, isCID, format):
	charset = ['.notdef']
	count = 1
	if format == 1:
		nLeftFunc = readCard8
	else:
		nLeftFunc = readCard16
	while count < numGlyphs:
		first = readCard16(file)
		nLeft = nLeftFunc(file)
		if isCID:
			for CID in range(first, first+nLeft+1):
				charset.append(CID)
		else:
			for SID in range(first, first+nLeft+1):
				charset.append(strings[SID])
		count = count + nLeft + 1
	return charset


class FDArrayConverter(BaseConverter):
	def read(self, parent, value):
		file = parent.file
		file.seek(value)
		fdArray = TopDictIndex(file)
		fdArray.strings = parent.strings
		fdArray.GlobalSubrs = parent.GlobalSubrs
		return fdArray


class FDSelectConverter:
	def read(self, parent, value):
		file = parent.file
		file.seek(value)
		format = readCard8(file)
		numGlyphs = parent.numGlyphs
		if format == 0:
			from array import array
			fdSelect = array("B", file.read(numGlyphs)).tolist()
		elif format == 3:
			fdSelect = [None] * numGlyphs
			nRanges = readCard16(file)
			prev = None
			for i in range(nRanges):
				first = readCard16(file)
				if prev is not None:
					for glyphID in range(prev, first):
						fdSelect[glyphID] = fd
				prev = first
				fd = readCard8(file)
			if prev is not None:
				first = readCard16(file)
				for glyphID in range(prev, first):
					fdSelect[glyphID] = fd
		else:
			assert 0, "unsupported FDSelect format: %s" % format
		return fdSelect
	def xmlWrite(self, xmlWriter, name, value):
		pass


class ROSConverter(BaseConverter):
	def xmlWrite(self, xmlWriter, name, value):
		registry, order, supplement = value
		xmlWriter.simpletag(name, [('Registry', registry), ('Order', order),
			('Supplement', supplement)])
		xmlWriter.newline()


topDictOperators = [
#	opcode     name                  argument type   default    converter
	((12, 30), 'ROS',        ('SID','SID','number'), None,      ROSConverter()),
	((12, 20), 'SyntheticBase',      'number',       None,      None),
	(0,        'version',            'SID',          None,      None),
	(1,        'Notice',             'SID',          None,      None),
	((12, 0),  'Copyright',          'SID',          None,      None),
	(2,        'FullName',           'SID',          None,      None),
	((12, 38), 'FontName',           'SID',          None,      None),
	(3,        'FamilyName',         'SID',          None,      None),
	(4,        'Weight',             'SID',          None,      None),
	((12, 1),  'isFixedPitch',       'number',       0,         None),
	((12, 2),  'ItalicAngle',        'number',       0,         None),
	((12, 3),  'UnderlinePosition',  'number',       None,      None),
	((12, 4),  'UnderlineThickness', 'number',       50,        None),
	((12, 5),  'PaintType',          'number',       0,         None),
	((12, 6),  'CharstringType',     'number',       2,         None),
	((12, 7),  'FontMatrix',         'array',  [0.001,0,0,0.001,0,0],  None),
	(13,       'UniqueID',           'number',       None,      None),
	(5,        'FontBBox',           'array',  [0,0,0,0],       None),
	((12, 8),  'StrokeWidth',        'number',       0,         None),
	(14,       'XUID',               'array',        None,      None),
	(15,       'charset',            'number',       0,         CharsetConverter()),
	((12, 21), 'PostScript',         'SID',          None,      None),
	((12, 22), 'BaseFontName',       'SID',          None,      None),
	((12, 23), 'BaseFontBlend',      'delta',        None,      None),
	((12, 31), 'CIDFontVersion',     'number',       0,         None),
	((12, 32), 'CIDFontRevision',    'number',       0,         None),
	((12, 33), 'CIDFontType',        'number',       0,         None),
	((12, 34), 'CIDCount',           'number',       8720,      None),
	((12, 35), 'UIDBase',            'number',       None,      None),
	(16,       'Encoding',           'number',       0,         None), # XXX
	((12, 36), 'FDArray',            'number',       None,      FDArrayConverter()),
	((12, 37), 'FDSelect',           'number',       None,      FDSelectConverter()),
	(18,       'Private',       ('number','number'), None,      PrivateDictConverter()),
	(17,       'CharStrings',        'number',       None,      CharStringsConverter()),
]

privateDictOperators = [
#	opcode     name                  argument type   default    converter
	(6,        'BlueValues',         'delta',        None,      None),
	(7,        'OtherBlues',         'delta',        None,      None),
	(8,        'FamilyBlues',        'delta',        None,      None),
	(9,        'FamilyOtherBlues',   'delta',        None,      None),
	((12, 9),  'BlueScale',          'number',       0.039625,  None),
	((12, 10), 'BlueShift',          'number',       7,         None),
	((12, 11), 'BlueFuzz',           'number',       1,         None),
	(10,       'StdHW',              'number',       None,      None),
	(11,       'StdVW',              'number',       None,      None),
	((12, 12), 'StemSnapH',          'delta',        None,      None),
	((12, 13), 'StemSnapV',          'delta',        None,      None),
	((12, 14), 'ForceBold',          'number',       0,         None),
	((12, 15), 'ForceBoldThreshold', 'number',       None,      None),  # deprecated
	((12, 16), 'lenIV',              'number',       None,      None),  # deprecated
	((12, 17), 'LanguageGroup',      'number',       0,         None),
	((12, 18), 'ExpansionFactor',    'number',       0.06,      None),
	((12, 19), 'initialRandomSeed',  'number',       0,         None),
	(20,       'defaultWidthX',      'number',       0,         None),
	(21,       'nominalWidthX',      'number',       0,         None),
	(19,       'Subrs',              'number',       None,      SubrsConverter()),
]


class TopDictDecompiler(psCharStrings.DictDecompiler):
	operators = buildOperatorDict(topDictOperators)


class PrivateDictDecompiler(psCharStrings.DictDecompiler):
	operators = buildOperatorDict(privateDictOperators)


class DictCompiler:
	
	def __init__(self, dictObj, strings, parent):
		assert isinstance(strings, IndexedStrings)
		self.dictObj = dictObj
		self.strings = strings
		self.parent = parent
		rawDict = {}
		for name in dictObj.order:
			value = getattr(dictObj, name, None)
			if value is None:
				continue
			conv = dictObj.converters[name]
			if conv:
				value = conv.write(dictObj, value)
			if value == dictObj.defaults.get(name):
				continue
			rawDict[name] = value
		self.rawDict = rawDict
	
	def setPos(self, pos):
		pass
	
	def getDataLength(self):
		return len(self.compile())
	
	def compile(self):
		rawDict = self.rawDict
		data = []
		for name in self.dictObj.order:
			value = rawDict.get(name)
			if value is None:
				continue
			op, argType = self.opcodes[name]
			if type(argType) == TupleType:
				l = len(argType)
				assert len(value) == l, "value doesn't match arg type"
				for i in range(l):
					arg = argType[l - i - 1]
					v = value[i]
					arghandler = getattr(self, "arg_" + arg)
					data.append(arghandler(v))
			else:
				arghandler = getattr(self, "arg_" + argType)
				data.append(arghandler(value))
			data.append(op)
		return "".join(data)
	
	def toFile(self, file):
		file.write(self.compile())
	
	def arg_number(self, num):
		return encodeNumber(num)
	def arg_SID(self, s):
		return psCharStrings.encodeIntCFF(self.strings.getSID(s))
	def arg_array(self, value):
		data = []
		for num in value:
			data.append(encodeNumber(num))
		return "".join(data)
	def arg_delta(self, value):
		out = []
		last = 0
		for v in value:
			out.append(v - last)
			last = v
		data = []
		for num in out:
			data.append(encodeNumber(num))
		return "".join(data)


def encodeNumber(num):
	if type(num) == FloatType:
		return psCharStrings.encodeFloat(num)
	else:
		return psCharStrings.encodeIntCFF(num)


class TopDictCompiler(DictCompiler):
	
	opcodes = buildOpcodeDict(topDictOperators)
	
	def getChildren(self, strings):
		children = []
		if hasattr(self.dictObj, "charset"):
			children.append(CharsetCompiler(strings, self.dictObj.charset, self))
		if hasattr(self.dictObj, "CharStrings"):
			items = []
			charStrings = self.dictObj.CharStrings
			for name in self.dictObj.charset:
				items.append(charStrings[name])
			charStringsComp = CharStringsCompiler(items, strings, self)
			children.append(charStringsComp)
		if hasattr(self.dictObj, "Private"):
			privComp = self.dictObj.Private.getCompiler(strings, self)
			children.append(privComp)
			children.extend(privComp.getChildren(strings))
		return children


class PrivateDictCompiler(DictCompiler):
	
	opcodes = buildOpcodeDict(privateDictOperators)
	
	def setPos(self, pos):
		size = len(self.compile())
		self.parent.rawDict["Private"] = size, pos
		self.pos = pos
	
	def getChildren(self, strings):
		children = []
		if hasattr(self.dictObj, "Subrs"):
			children.append(self.dictObj.Subrs.getCompiler(strings, self))
		return children


class BaseDict:
	
	def __init__(self, strings, file, offset):
		self.rawDict = {}
		if DEBUG:
			print "loading %s at %s" % (self.__class__.__name__, offset)
		self.file = file
		self.offset = offset
		self.strings = strings
		self.skipNames = []
	
	def decompile(self, data):
		if DEBUG:
			print "    length %s is %s" % (self.__class__.__name__, len(data))
		dec = self.decompilerClass(self.strings)
		dec.decompile(data)
		self.rawDict = dec.getDict()
		self.postDecompile()
	
	def postDecompile(self):
		pass
	
	def getCompiler(self, strings, parent):
		return self.compilerClass(self, strings, parent)
	
	def __getattr__(self, name):
		value = self.rawDict.get(name)
		if value is None:
			value = self.defaults.get(name)
		if value is None:
			raise AttributeError, name
		conv = self.converters[name]
		if conv is not None:
			value = conv.read(self, value)
		setattr(self, name, value)
		return value
	
	def toXML(self, xmlWriter, progress):
		for name in self.order:
			if name in self.skipNames:
				continue
			value = getattr(self, name, None)
			if value is None:
				continue
			conv = self.converters.get(name)
			if conv is not None:
				conv.xmlWrite(xmlWriter, name, value)
			else:
				if isinstance(value, ListType):
					value = " ".join(map(str, value))
				xmlWriter.simpletag(name, value=value)
				xmlWriter.newline()


class TopDict(BaseDict):
	
	defaults = buildDefaults(topDictOperators)
	converters = buildConverters(topDictOperators)
	order = buildOrder(topDictOperators)
	decompilerClass = TopDictDecompiler
	compilerClass = TopDictCompiler
	
	def __init__(self, strings, file, offset, GlobalSubrs):
		BaseDict.__init__(self, strings, file, offset)
		self.GlobalSubrs = GlobalSubrs
	
	def getGlyphOrder(self):
		return self.charset
	
	def postDecompile(self):
		offset = self.rawDict.get("CharStrings")
		if offset is None:
			return
		# get the number of glyphs beforehand.
		self.file.seek(offset)
		self.numGlyphs = readCard16(self.file)
	
	def toXML(self, xmlWriter, progress):
		if hasattr(self, "CharStrings"):
			self.decompileAllCharStrings()
		if not hasattr(self, "ROS") or not hasattr(self, "CharStrings"):
			# these values have default values, but I only want them to show up
			# in CID fonts.
			self.skipNames = ['CIDFontVersion', 'CIDFontRevision', 'CIDFontType',
					'CIDCount']
		BaseDict.toXML(self, xmlWriter, progress)
	
	def decompileAllCharStrings(self):
		for charString in self.CharStrings.values():
			charString.decompile()


class PrivateDict(BaseDict):
	defaults = buildDefaults(privateDictOperators)
	converters = buildConverters(privateDictOperators)
	order = buildOrder(privateDictOperators)
	decompilerClass = PrivateDictDecompiler
	compilerClass = PrivateDictCompiler


class IndexedStrings:
	
	"""SID -> string mapping."""
	
	def __init__(self, file=None):
		if file is None:
			strings = []
		else:
			strings = list(Index(file, "IndexedStrings"))
		self.strings = strings
	
	def getCompiler(self):
		return IndexedStringsCompiler(self, None, None)
	
	def __len__(self):
		return len(self.strings)
	
	def __getitem__(self, SID):
		if SID < cffStandardStringCount:
			return cffStandardStrings[SID]
		else:
			return self.strings[SID - cffStandardStringCount]
	
	def getSID(self, s):
		if not hasattr(self, "stringMapping"):
			self.buildStringMapping()
		if cffStandardStringMapping.has_key(s):
			SID = cffStandardStringMapping[s]
		elif self.stringMapping.has_key(s):
			SID = self.stringMapping[s]
		else:
			SID = len(self.strings) + cffStandardStringCount
			self.strings.append(s)
			self.stringMapping[s] = SID
		return SID
	
	def getStrings(self):
		return self.strings
	
	def buildStringMapping(self):
		self.stringMapping = {}
		for index in range(len(self.strings)):
			self.stringMapping[self.strings[index]] = index + cffStandardStringCount


# The 391 Standard Strings as used in the CFF format.
# from Adobe Technical None #5176, version 1.0, 18 March 1998

cffStandardStrings = ['.notdef', 'space', 'exclam', 'quotedbl', 'numbersign', 
		'dollar', 'percent', 'ampersand', 'quoteright', 'parenleft', 'parenright', 
		'asterisk', 'plus', 'comma', 'hyphen', 'period', 'slash', 'zero', 'one', 
		'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'colon', 
		'semicolon', 'less', 'equal', 'greater', 'question', 'at', 'A', 'B', 'C', 
		'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 
		'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'bracketleft', 'backslash', 
		'bracketright', 'asciicircum', 'underscore', 'quoteleft', 'a', 'b', 'c', 
		'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 
		's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'braceleft', 'bar', 'braceright', 
		'asciitilde', 'exclamdown', 'cent', 'sterling', 'fraction', 'yen', 'florin', 
		'section', 'currency', 'quotesingle', 'quotedblleft', 'guillemotleft', 
		'guilsinglleft', 'guilsinglright', 'fi', 'fl', 'endash', 'dagger', 
		'daggerdbl', 'periodcentered', 'paragraph', 'bullet', 'quotesinglbase', 
		'quotedblbase', 'quotedblright', 'guillemotright', 'ellipsis', 'perthousand', 
		'questiondown', 'grave', 'acute', 'circumflex', 'tilde', 'macron', 'breve', 
		'dotaccent', 'dieresis', 'ring', 'cedilla', 'hungarumlaut', 'ogonek', 'caron', 
		'emdash', 'AE', 'ordfeminine', 'Lslash', 'Oslash', 'OE', 'ordmasculine', 'ae', 
		'dotlessi', 'lslash', 'oslash', 'oe', 'germandbls', 'onesuperior', 
		'logicalnot', 'mu', 'trademark', 'Eth', 'onehalf', 'plusminus', 'Thorn', 
		'onequarter', 'divide', 'brokenbar', 'degree', 'thorn', 'threequarters', 
		'twosuperior', 'registered', 'minus', 'eth', 'multiply', 'threesuperior', 
		'copyright', 'Aacute', 'Acircumflex', 'Adieresis', 'Agrave', 'Aring', 
		'Atilde', 'Ccedilla', 'Eacute', 'Ecircumflex', 'Edieresis', 'Egrave', 
		'Iacute', 'Icircumflex', 'Idieresis', 'Igrave', 'Ntilde', 'Oacute', 
		'Ocircumflex', 'Odieresis', 'Ograve', 'Otilde', 'Scaron', 'Uacute', 
		'Ucircumflex', 'Udieresis', 'Ugrave', 'Yacute', 'Ydieresis', 'Zcaron', 
		'aacute', 'acircumflex', 'adieresis', 'agrave', 'aring', 'atilde', 'ccedilla', 
		'eacute', 'ecircumflex', 'edieresis', 'egrave', 'iacute', 'icircumflex', 
		'idieresis', 'igrave', 'ntilde', 'oacute', 'ocircumflex', 'odieresis', 
		'ograve', 'otilde', 'scaron', 'uacute', 'ucircumflex', 'udieresis', 'ugrave', 
		'yacute', 'ydieresis', 'zcaron', 'exclamsmall', 'Hungarumlautsmall', 
		'dollaroldstyle', 'dollarsuperior', 'ampersandsmall', 'Acutesmall', 
		'parenleftsuperior', 'parenrightsuperior', 'twodotenleader', 'onedotenleader', 
		'zerooldstyle', 'oneoldstyle', 'twooldstyle', 'threeoldstyle', 'fouroldstyle', 
		'fiveoldstyle', 'sixoldstyle', 'sevenoldstyle', 'eightoldstyle', 
		'nineoldstyle', 'commasuperior', 'threequartersemdash', 'periodsuperior', 
		'questionsmall', 'asuperior', 'bsuperior', 'centsuperior', 'dsuperior', 
		'esuperior', 'isuperior', 'lsuperior', 'msuperior', 'nsuperior', 'osuperior', 
		'rsuperior', 'ssuperior', 'tsuperior', 'ff', 'ffi', 'ffl', 'parenleftinferior', 
		'parenrightinferior', 'Circumflexsmall', 'hyphensuperior', 'Gravesmall', 
		'Asmall', 'Bsmall', 'Csmall', 'Dsmall', 'Esmall', 'Fsmall', 'Gsmall', 'Hsmall', 
		'Ismall', 'Jsmall', 'Ksmall', 'Lsmall', 'Msmall', 'Nsmall', 'Osmall', 'Psmall', 
		'Qsmall', 'Rsmall', 'Ssmall', 'Tsmall', 'Usmall', 'Vsmall', 'Wsmall', 'Xsmall', 
		'Ysmall', 'Zsmall', 'colonmonetary', 'onefitted', 'rupiah', 'Tildesmall', 
		'exclamdownsmall', 'centoldstyle', 'Lslashsmall', 'Scaronsmall', 'Zcaronsmall', 
		'Dieresissmall', 'Brevesmall', 'Caronsmall', 'Dotaccentsmall', 'Macronsmall', 
		'figuredash', 'hypheninferior', 'Ogoneksmall', 'Ringsmall', 'Cedillasmall', 
		'questiondownsmall', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 
		'onethird', 'twothirds', 'zerosuperior', 'foursuperior', 'fivesuperior', 
		'sixsuperior', 'sevensuperior', 'eightsuperior', 'ninesuperior', 'zeroinferior', 
		'oneinferior', 'twoinferior', 'threeinferior', 'fourinferior', 'fiveinferior', 
		'sixinferior', 'seveninferior', 'eightinferior', 'nineinferior', 'centinferior', 
		'dollarinferior', 'periodinferior', 'commainferior', 'Agravesmall', 
		'Aacutesmall', 'Acircumflexsmall', 'Atildesmall', 'Adieresissmall', 'Aringsmall', 
		'AEsmall', 'Ccedillasmall', 'Egravesmall', 'Eacutesmall', 'Ecircumflexsmall', 
		'Edieresissmall', 'Igravesmall', 'Iacutesmall', 'Icircumflexsmall', 
		'Idieresissmall', 'Ethsmall', 'Ntildesmall', 'Ogravesmall', 'Oacutesmall', 
		'Ocircumflexsmall', 'Otildesmall', 'Odieresissmall', 'OEsmall', 'Oslashsmall', 
		'Ugravesmall', 'Uacutesmall', 'Ucircumflexsmall', 'Udieresissmall', 
		'Yacutesmall', 'Thornsmall', 'Ydieresissmall', '001.000', '001.001', '001.002', 
		'001.003', 'Black', 'Bold', 'Book', 'Light', 'Medium', 'Regular', 'Roman', 
		'Semibold'
]

cffStandardStringCount = 391
assert len(cffStandardStrings) == cffStandardStringCount
# build reverse mapping
cffStandardStringMapping = {}
for _i in range(cffStandardStringCount):
	cffStandardStringMapping[cffStandardStrings[_i]] = _i

