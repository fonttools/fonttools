"""cffLib.py -- read/write tools for Adobe CFF fonts."""

#
# $Id: cffLib.py,v 1.12 2002-05-15 07:41:30 jvr Exp $
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
		self.fonts = {}
	
	def decompile(self, file):
		sstruct.unpack(cffHeaderFormat, file.read(4), self)
		assert self.major == 1 and self.minor == 0, \
				"unknown CFF format: %d.%d" % (self.major, self.minor)
		
		self.fontNames = readINDEX(file)
		topDicts = readINDEX(file)
		strings = IndexedStrings(readINDEX(file))
		globalSubrs = readINDEX(file)
		
		file.seek(4)
		xfnames = Index(file)
		xtopds = Index(file)
		xstrings = Index(file)
		xgsubrs = Index(file)
		
		assert xfnames.toList() == self.fontNames
		assert xtopds.toList() == topDicts
		assert xstrings.toList() == strings.strings
		assert xgsubrs.toList() == globalSubrs
		
		self.GlobalSubrs = map(psCharStrings.T2CharString, globalSubrs)
		
		for i in range(len(topDicts)):
			font = self.fonts[self.fontNames[i]] = CFFFont()
			font.GlobalSubrs = self.GlobalSubrs
			file.seek(0)
			font.decompile(file, topDicts[i], strings, self)
	
	def compile(self):
		strings = IndexedStrings()
		XXXX
	
	def toXML(self, xmlWriter, progress=None):
		xmlWriter.newline()
		for fontName in self.fontNames:
			xmlWriter.begintag("CFFFont", name=fontName)
			xmlWriter.newline()
			font = self.fonts[fontName]
			font.toXML(xmlWriter, progress)
			xmlWriter.endtag("CFFFont")
			xmlWriter.newline()
		xmlWriter.newline()
		xmlWriter.begintag("GlobalSubrs")
		xmlWriter.newline()
		for i in range(len(self.GlobalSubrs)):
			xmlWriter.newline()
			xmlWriter.begintag("CharString", index=i)
			xmlWriter.newline()
			self.GlobalSubrs[i].toXML(xmlWriter)
			xmlWriter.endtag("CharString")
			xmlWriter.newline()
		xmlWriter.newline()
		xmlWriter.endtag("GlobalSubrs")
		xmlWriter.newline()
		xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content)):
		xxx


class CFFFont:
	
	def __init__(self):
		pass
	
	def __getattr__(self, attr):
		if not topDictDefaults.has_key(attr):
			raise AttributeError, attr
		return topDictDefaults[attr]
	
	def fromDict(self, d):
		self.__dict__.update(d)
	
	def decompile(self, file, topDictData, strings, fontSet):
		top = TopDictDecompiler(strings)
		top.decompile(topDictData)
		self.fromDict(top.getDict())
		
		if hasattr(self, "ROS"):
			isCID = 1
			# XXX CID subFonts
			offset = self.FDArray
			file.seek(offset)
			fontDicts = readINDEX(file)
			subFonts = self.subFonts = []
			for topDictData in fontDicts:
				subFont = CFFFont()
				subFonts.append(subFont)
				subFont.decompile(file, topDictData, strings, None)
			# XXX
		else:
			isCID = 0
			size, offset = self.Private
			file.seek(offset)
			privateData = file.read(size)
			file.seek(offset)
			assert len(privateData) == size
			self.Private = PrivateDict()
			self.Private.decompile(file, privateData, strings)
		
		if hasattr(self, "CharStrings"):
			file.seek(self.CharStrings)
			rawCharStrings = Index(file)
			nGlyphs = len(rawCharStrings)
		
		# get charset (or rather: get glyphNames)
		if self.charset > 2:
			file.seek(self.charset)
			format = ord(file.read(1))
			if format == 0:
				raise NotImplementedError
			elif format == 1:
				charset = parseCharsetFormat1(nGlyphs, file, strings, isCID)
			elif format == 2:
				charset = parseCharsetFormat2(nGlyphs, file, strings, isCID)
			elif format == 3:
				raise NotImplementedError
			else:
				raise NotImplementedError
			self.charset = charset
			assert len(charset) == nGlyphs
		else:
			# self.charset:
			#   0: ISOAdobe (or CID font!)
			#   1: Expert
			#   2: ExpertSubset
			pass
		
		if hasattr(self, "CharStrings"):
			self.CharStrings = charStrings = {}
			if self.CharstringType == 2:
				# Type 2 CharStrings
				charStringClass = psCharStrings.T2CharString
			else:
				# Type 1 CharStrings
				charStringClass = psCharStrings.T1CharString
			for i in range(nGlyphs):
				charStrings[charset[i]] = charStringClass(rawCharStrings[i])
			assert len(charStrings) == nGlyphs
		
		encoding = self.Encoding
		if encoding > 1:
			# encoding is an offset from the beginning of 'data' to an encoding subtable
			raise NotImplementedError
			self.Encoding = encoding
		else:
			# self.Encoding:
			#   0 Standard Encoding
			#   1 Expert Encoding
			pass
	
	def getGlyphOrder(self):
		return self.charset
	
	def setGlyphOrder(self, glyphOrder):
		self.charset = glyphOrder
	
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
	
	def toXML(self, xmlWriter, progress=None):
		xmlWriter.newline()
		genericToXML(self, topDictOrder, {'CharStrings': 'CharString'}, xmlWriter)


class PrivateDict:
	
	def __init__(self):
		pass
	
	def decompile(self, file, privateData, strings):
		p = PrivateDictDecompiler(strings)
		p.decompile(privateData)
		self.fromDict(p.getDict())
		
		# get local subrs
		if hasattr(self, "Subrs"):
			file.seek(self.Subrs, 1)
			localSubrs = Index(file)
			self.Subrs = map(psCharStrings.T2CharString, localSubrs)
		else:
			self.Subrs = []
	
	def toXML(self, xmlWriter):
		xmlWriter.newline()
		genericToXML(self, privateDictOrder, {'Subrs': 'CharString'}, xmlWriter)
	
	def __getattr__(self, attr):
		if not privateDictDefaults.has_key(attr):
			raise AttributeError, attr
		return privateDictDefaults[attr]
	
	def fromDict(self, d):
		self.__dict__.update(d)


def readINDEX(file):
	count, = struct.unpack(">H", file.read(2))
	if count == 0:
		return []
	offSize = ord(file.read(1))
	offsets = []
	for index in range(count+1):
		chunk = file.read(offSize)
		chunk = '\0' * (4 - offSize) + chunk
		offset, = struct.unpack(">L", chunk)
		offset = int(offset)
		offsets.append(offset)
	offsetBase = file.tell() - 1
	prev = offsets[0]
	stuff = []
	for next in offsets[1:]:
		assert offsetBase + prev == file.tell()
		chunk = file.read(next - prev)
		assert len(chunk) == next - prev
		stuff.append(chunk)
		prev = next
	return stuff


class Index:

	def __init__(self, file):
		self.file = file
		count, = struct.unpack(">H", file.read(2))
		self.count = count
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
		file.seek(self.offsetBase + offsets[-1])
	
	def __len__(self):
		return self.count
	
	def __getitem__(self, index):
		offset = self.offsets[index] + self.offsetBase
		size = self.offsets[index+1] - self.offsets[index]
		return FileString(self.file, offset, size)
	
	def toList(self):
		l = []
		for item in self:
			l.append(item[:])
		return l


class FileString:

	def __init__(self, file, offset, size):
		self.file = file
		self.offset = offset
		self.size = size
		self.string = None
	
	def __len__(self):
		return self.size
	
	def __getitem__(self, index):
		return self.get()[index]
	
	def __getslice__(self, i, j):
		return self.get()[i:j]
	
	def get(self):
		if self.string is None:
			self.file.seek(self.offset)
			self.string = self.file.read(self.size)
		return self.string


def getItems(o):
	if hasattr(o, "items"):
		items = o.items()
		items.sort()
		return "name", items
	else:
		return "index", map(None, range(len(o)), o)


def genericToXML(obj, order, arrayTypes, xmlWriter):
	for name in order:
		value = getattr(obj, name, None)
		if value is None:
			continue
		if hasattr(value, "toXML"):
			xmlWriter.newline()
			xmlWriter.begintag(name)
			xmlWriter.newline()
			value.toXML(xmlWriter)
			xmlWriter.endtag(name)
			xmlWriter.newline()
			xmlWriter.newline()
		elif arrayTypes.has_key(name):
			typeName = arrayTypes[name]
			xmlWriter.newline()
			xmlWriter.begintag(name)
			xmlWriter.newline()
			xmlWriter.newline()
			label, items = getItems(value)
			for k, v in items:
				xmlWriter.begintag(typeName, [(label, k)])
				xmlWriter.newline()
				v.toXML(xmlWriter)
				xmlWriter.endtag(typeName)
				xmlWriter.newline()
				xmlWriter.newline()
			xmlWriter.endtag(name)
			xmlWriter.newline()
			xmlWriter.newline()
		else:
			if isinstance(value, types.ListType):
				value = " ".join(map(str, value))
			xmlWriter.simpletag(name, value=value)
			xmlWriter.newline()


def parseCharsetFormat1(nGlyphs, file, strings, isCID):
	charset = ['.notdef']
	count = 1
	while count < nGlyphs:
		first, = struct.unpack(">H", file.read(2))
		nLeft = ord(file.read(1))
		if isCID:
			for CID in range(first, first+nLeft+1):
				charset.append(CID)
		else:
			for SID in range(first, first+nLeft+1):
				charset.append(strings[SID])
		count = count + nLeft + 1
	return charset


def parseCharsetFormat2(nGlyphs, file, strings, isCID):
	charset = ['.notdef']
	count = 1
	while count < nGlyphs:
		first, = struct.unpack(">H", file.read(2))
		nLeft, = struct.unpack(">H", file.read(2))
		if isCID:
			for CID in range(first, first+nLeft+1):
				charset.append(CID)
		else:
			for SID in range(first, first+nLeft+1):
				charset.append(strings[SID])
		count = count + nLeft + 1
	return charset


def buildOperatorDict(table):
	d = {}
	for row in table:
		d[row[0]] = row[1:3]
	return d

def buildOrder(table):
	l = []
	for row in table:
		l.append(row[1])
	return l

def buildDefaults(table):
	d = {}
	for row in table:
		if row[3] is not None:
			d[row[1]] = row[3]
	return d


topDictOperators = [
#	opcode     name                  argument type   default
	(0,        'version',            'SID',          None),
	(1,        'Notice',             'SID',          None),
	((12, 0),  'Copyright',          'SID',          None),
	(2,        'FullName',           'SID',          None),
	(3,        'FamilyName',         'SID',          None),
	(4,        'Weight',             'SID',          None),
	((12, 1),  'isFixedPitch',       'number',       0),
	((12, 2),  'ItalicAngle',        'number',       0),
	((12, 3),  'UnderlinePosition',  'number',       None),
	((12, 4),  'UnderlineThickness', 'number',       50),
	((12, 5),  'PaintType',          'number',       0),
	((12, 6),  'CharstringType',     'number',       2),
	((12, 7),  'FontMatrix',         'array',  [0.001,0,0,0.001,0,0]),
	(13,       'UniqueID',           'number',       None),
	(5,        'FontBBox',           'array',  [0,0,0,0]),
	((12, 8),  'StrokeWidth',        'number',       0),
	(14,       'XUID',               'array',        None),
	(15,       'charset',            'number',       0),
	(16,       'Encoding',           'number',       0),
	(18,       'Private',       ('number','number'), None),
	(17,       'CharStrings',        'number',       None),
	((12, 20), 'SyntheticBase',      'number',       None),
	((12, 21), 'PostScript',         'SID',          None),
	((12, 22), 'BaseFontName',       'SID',          None),
	((12, 23), 'BaseFontBlend',      'delta',        None),
	((12, 30), 'ROS',        ('SID','SID','number'), None),
	((12, 31), 'CIDFontVersion',     'number',       0),
	((12, 32), 'CIDFontRevision',    'number',       0),
	((12, 33), 'CIDFontType',        'number',       0),
	((12, 34), 'CIDCount',           'number',       8720),
	((12, 35), 'UIDBase',            'number',       None),
	((12, 36), 'FDArray',            'number',       None),
	((12, 37), 'FDSelect',           'number',       None),
	((12, 38), 'FontName',           'SID',          None),
]

topDictDefaults = buildDefaults(topDictOperators)
topDictOrder = buildOrder(topDictOperators)

class TopDictDecompiler(psCharStrings.DictDecompiler):
	
	operators = buildOperatorDict(topDictOperators)
	dictDefaults = topDictDefaults
	

privateDictOperators = [
#	opcode     name                  argument type   default
	(6,        'BlueValues',         'delta',        None),
	(7,        'OtherBlues',         'delta',        None),
	(8,        'FamilyBlues',        'delta',        None),
	(9,        'FamilyOtherBlues',   'delta',        None),
	((12, 9),  'BlueScale',          'number',       0.039625),
	((12, 10), 'BlueShift',          'number',       7),
	((12, 11), 'BlueFuzz',           'number',       1),
	(10,       'StdHW',              'number',       None),
	(11,       'StdVW',              'number',       None),
	((12, 12), 'StemSnapH',          'delta',        None),
	((12, 13), 'StemSnapV',          'delta',        None),
	((12, 14), 'ForceBold',          'number',       0),
	((12, 17), 'LanguageGroup',      'number',       0),
	((12, 18), 'ExpansionFactor',    'number',       0.06),
	((12, 19), 'initialRandomSeed',  'number',       0),
	(20,       'defaultWidthX',      'number',       0),
	(21,       'nominalWidthX',      'number',       0),
	(19,       'Subrs',              'number',       None),
]

privateDictDefaults = buildDefaults(privateDictOperators)
privateDictOrder = buildOrder(privateDictOperators)

class PrivateDictDecompiler(psCharStrings.DictDecompiler):
	
	operators = buildOperatorDict(privateDictOperators)
	dictDefaults = privateDictDefaults


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


