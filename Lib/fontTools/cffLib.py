"""cffLib.py -- read/write tools for Adobe CFF fonts."""

#
# $Id: cffLib.py,v 1.13 2002-05-16 18:17:32 jvr Exp $
#

import struct, sstruct
import string
import types
from fontTools.misc import psCharStrings


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
		
		self.fontNames = list(Index(file))
		self.topDictIndex = TopDictIndex(file)
		self.strings = IndexedStrings(list(Index(file)))
		self.GlobalSubrs = SubrsIndex(file)
		self.topDictIndex.strings = self.strings
	
	def __len__(self):
		return len(self.fontNames)
	
	def keys(self):
		return self.fontNames[:]
	
	def __getitem__(self, name):
		try:
			index = self.fontNames.index(name)
		except ValueError:
			raise KeyError, name
		font = self.topDictIndex[index]
		if not hasattr(font, "GlobalSubrs"):
			font.GlobalSubrs = self.GlobalSubrs
		return font
	
	def compile(self):
		strings = IndexedStrings()
		XXXX
	
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


class Index:
	
	"""This class represents what the CFF spec calls an INDEX."""
	
	def __init__(self, file):
		self.file = file
		count, = struct.unpack(">H", file.read(2))
		self.count = count
		self.items = [None] * count
		if count == 0:
			self.offsets = []
			return
		offSize = ord(file.read(1))
		self.offsets = offsets = []
		pad = '\0' * (4 - offSize)
		for index in range(count+1):
			chunk = file.read(offSize)
			chunk = pad + chunk
			offset, = struct.unpack(">L", chunk)
			offsets.append(int(offset))
		self.offsetBase = file.tell() - 1
		file.seek(self.offsetBase + offsets[-1])  # pretend we've read the whole lot
	
	def __len__(self):
		return self.count
	
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
		item = self.produceItem(data, file, offset, size)
		self.items[index] = item
		return item
	
	def produceItem(self, data, file, offset, size):
		return data


class SubrsIndex(Index):
	
	def produceItem(self, data, file, offset, size):
		return psCharStrings.T2CharString(data)
	
	def toXML(self, xmlWriter, progress):
		for i in range(len(self)):
			xmlWriter.begintag("CharString", index=i)
			xmlWriter.newline()
			self[i].toXML(xmlWriter)
			xmlWriter.endtag("CharString")
			xmlWriter.newline()


class CharStrings:
	
	def __init__(self, file, charset):
		self.charStringsIndex = SubrsIndex(file)
		self.nameToIndex = nameToIndex = {}
		for i in range(len(charset)):
			nameToIndex[charset[i]] = i
	
	def keys(self):
		return self.nameToIndex.keys()
	
	def has_key(self, name):
		return self.nameToIndex.has_key(name)
	
	def __getitem__(self, name):
		index = self.nameToIndex[name]
		return self.charStringsIndex[index]
	
	def toXML(self, xmlWriter, progress):
		names = self.keys()
		names.sort()
		for name in names:
			xmlWriter.begintag("CharString", name=name)
			xmlWriter.newline()
			self[name].toXML(xmlWriter)
			xmlWriter.endtag("CharString")
			xmlWriter.newline()


class TopDictIndex(Index):
	def produceItem(self, data, file, offset, size):
		top = TopDict(self.strings, file, offset)
		top.decompile(data)
		return top


def buildOperatorDict(table):
	d = {}
	for op, name, arg, default, conv in table:
		d[op] = (name, arg)
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


class PrivateDictConverter:
	def read(self, parent, value):
		size, offset = value
		file = parent.file
		pr = PrivateDict(parent.strings, file, offset)
		file.seek(offset)
		data = file.read(size)
		len(data) == size
		pr.decompile(data)
		return pr
	def xmlWrite(self, xmlWriter, name, value):
		xmlWriter.begintag(name)
		xmlWriter.newline()
		value.toXML(xmlWriter, None)
		xmlWriter.endtag(name)
		xmlWriter.newline()

class SubrsConverter(PrivateDictConverter):
	def read(self, parent, value):
		file = parent.file
		file.seek(parent.offset + value)  # Offset(self)
		return SubrsIndex(file)

class CharStringsConverter(PrivateDictConverter):
	def read(self, parent, value):
		file = parent.file
		file.seek(value)  # Offset(0)
		return CharStrings(file, parent.charset)

class CharsetConverter:
	def read(self, parent, value):
		isCID = hasattr(parent, "ROS")
		if value > 2:
			numGlyphs = parent.numGlyphs
			file = parent.file
			file.seek(value)
			format = ord(file.read(1))
			if format == 0:
				raise NotImplementedError
			elif format == 1 or format == 2:
				charset = parseCharset(numGlyphs, file, parent.strings, isCID, format)
			elif format == 3:
				raise NotImplementedError
			else:
				raise NotImplementedError
			assert len(charset) == numGlyphs
		else:
			if isCID:
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
	def xmlWrite(self, xmlWriter, name, value):
		# XXX GlyphOrder needs to be stored *somewhere*, but not here...
		xmlWriter.simpletag("charset", value=value)
		xmlWriter.newline()


def parseCharset(numGlyphs, file, strings, isCID, format):
	charset = ['.notdef']
	count = 1
	if format == 1:
		def nLeftFunc(file):
			return ord(file.read(1))
	else:
		def nLeftFunc(file):
			return struct.unpack(">H", file.read(2))[0]
	while count < numGlyphs:
		first, = struct.unpack(">H", file.read(2))
		nLeft = nLeftFunc(file)
		if isCID:
			for CID in range(first, first+nLeft+1):
				charset.append(CID)
		else:
			for SID in range(first, first+nLeft+1):
				charset.append(strings[SID])
		count = count + nLeft + 1
	return charset


topDictOperators = [
#	opcode     name                  argument type   default    converter
	(0,        'version',            'SID',          None,      None),
	(1,        'Notice',             'SID',          None,      None),
	((12, 0),  'Copyright',          'SID',          None,      None),
	(2,        'FullName',           'SID',          None,      None),
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
	(16,       'Encoding',           'number',       0,         None),
	(18,       'Private',       ('number','number'), None,      PrivateDictConverter()),
	(17,       'CharStrings',        'number',       None,      CharStringsConverter()),  # XXX
	((12, 20), 'SyntheticBase',      'number',       None,      None),
	((12, 21), 'PostScript',         'SID',          None,      None),
	((12, 22), 'BaseFontName',       'SID',          None,      None),
	((12, 23), 'BaseFontBlend',      'delta',        None,      None),
	((12, 30), 'ROS',        ('SID','SID','number'), None,      None),
	((12, 31), 'CIDFontVersion',     'number',       0,         None),
	((12, 32), 'CIDFontRevision',    'number',       0,         None),
	((12, 33), 'CIDFontType',        'number',       0,         None),
	((12, 34), 'CIDCount',           'number',       8720,      None),
	((12, 35), 'UIDBase',            'number',       None,      None),
	((12, 36), 'FDArray',            'number',       None,      None),
	((12, 37), 'FDSelect',           'number',       None,      None),
	((12, 38), 'FontName',           'SID',          None,      None),
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



class BaseDict:
	
	def __init__(self, strings, file, offset):
		self.rawDict = {}
		self.file = file
		self.offset = offset
		self.strings = strings
	
	def decompile(self, data):
		dec = self.decompiler(self.strings)
		dec.decompile(data)
		self.rawDict = dec.getDict()
		self.postDecompile()
	
	def postDecompile(self):
		pass
	
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
			value = getattr(self, name, None)
			if value is None:
				continue
			conv = self.converters.get(name)
			if conv is not None:
				conv.xmlWrite(xmlWriter, name, value)
			else:
				if isinstance(value, types.ListType):
					value = " ".join(map(str, value))
				xmlWriter.simpletag(name, value=value)
				xmlWriter.newline()


class TopDict(BaseDict):
	
	defaults = buildDefaults(topDictOperators)
	converters = buildConverters(topDictOperators)
	order = buildOrder(topDictOperators)
	decompiler = TopDictDecompiler
	
	def getGlyphOrder(self):
		return self.charset
	
	def postDecompile(self):
		offset = self.rawDict.get("CharStrings")
		if offset is None:
			return
		# get the number of glyphs beforehand.
		self.file.seek(offset)
		self.numGlyphs, = struct.unpack(">H", self.file.read(2))
	
	def decompileAllCharStrings(self):
		if self.CharstringType == 2:
			# Type 2 CharStrings
			decompiler = psCharStrings.SimpleT2Decompiler(self.Private.Subrs, self.GlobalSubrs)
			for charString in self.CharStrings.values():
				if charString.needsDecompilation():
					decompiler.reset()
					decompiler.execute(charString)
		else:
			# Type 1 CharStrings
			for charString in self.CharStrings.values():
				charString.decompile()


class PrivateDict(BaseDict):
	defaults = buildDefaults(privateDictOperators)
	converters = buildConverters(privateDictOperators)
	order = buildOrder(privateDictOperators)
	decompiler = PrivateDictDecompiler



# SID

class IndexedStrings:
	
	def __init__(self, strings=None):
		if strings is None:
			strings = []
		self.strings = strings
	
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
		if self.stringMapping.has_key(s):
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


