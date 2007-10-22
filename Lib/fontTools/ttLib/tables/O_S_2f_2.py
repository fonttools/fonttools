import DefaultTable
import sstruct
from fontTools.misc.textTools import safeEval, num2binary, binary2num
from types import TupleType


# panose classification

panoseFormat = """
	bFamilyType:        B
	bSerifStyle:        B
	bWeight:            B
	bProportion:        B
	bContrast:          B
	bStrokeVariation:   B
	bArmStyle:          B
	bLetterForm:        B
	bMidline:           B
	bXHeight:           B
"""

class Panose:
	
	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(panoseFormat)
		for name in names:
			writer.simpletag(name, value=getattr(self, name))
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		setattr(self, name, safeEval(attrs["value"]))


# 'sfnt' OS/2 and Windows Metrics table - 'OS/2'

OS2_format_0 = """
	>   # big endian
	version:                H       # version
	xAvgCharWidth:          h       # average character width
	usWeightClass:          H       # degree of thickness of strokes
	usWidthClass:           H       # aspect ratio
	fsType:                 h       # type flags
	ySubscriptXSize:        h       # subscript horizontal font size
	ySubscriptYSize:        h       # subscript vertical font size
	ySubscriptXOffset:      h       # subscript x offset
	ySubscriptYOffset:      h       # subscript y offset
	ySuperscriptXSize:      h       # superscript horizontal font size
	ySuperscriptYSize:      h       # superscript vertical font size
	ySuperscriptXOffset:    h       # superscript x offset
	ySuperscriptYOffset:    h       # superscript y offset
	yStrikeoutSize:         h       # strikeout size
	yStrikeoutPosition:     h       # strikeout position
	sFamilyClass:           h       # font family class and subclass
	panose:                 10s     # panose classification number
	ulUnicodeRange1:        L       # character range
	ulUnicodeRange2:        L       # character range
	ulUnicodeRange3:        L       # character range
	ulUnicodeRange4:        L       # character range
	achVendID:              4s      # font vendor identification
	fsSelection:            H       # font selection flags
	fsFirstCharIndex:       H       # first unicode character index
	fsLastCharIndex:        H       # last unicode character index
	sTypoAscender:          h       # typographic ascender
	sTypoDescender:         h       # typographic descender
	sTypoLineGap:           h       # typographic line gap
	usWinAscent:            H       # Windows ascender
	usWinDescent:           H       # Windows descender
"""

OS2_format_1_addition =  """
	ulCodePageRange1:   L
	ulCodePageRange2:   L
"""

OS2_format_2_addition =  OS2_format_1_addition + """
	sxHeight:           h
	sCapHeight:         h
	usDefaultChar:      H
	usBreakChar:        H
	usMaxContex:        H
"""

bigendian = "	>	# big endian\n"

OS2_format_1 = OS2_format_0 + OS2_format_1_addition
OS2_format_2 = OS2_format_0 + OS2_format_2_addition
OS2_format_1_addition = bigendian + OS2_format_1_addition
OS2_format_2_addition = bigendian + OS2_format_2_addition


class table_O_S_2f_2(DefaultTable.DefaultTable):
	
	"""the OS/2 table"""
	
	def decompile(self, data, ttFont):
		dummy, data = sstruct.unpack2(OS2_format_0, data, self)
		if self.version == 1 and not data:
			# workaround for buggy Apple fonts
			self.version = 0
		if self.version == 1:
			sstruct.unpack2(OS2_format_1_addition, data, self)
		elif self.version in (2, 3, 4):
			sstruct.unpack2(OS2_format_2_addition, data, self)
		elif self.version <> 0:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown format for OS/2 table: version %s" % self.version
		self.panose = sstruct.unpack(panoseFormat, self.panose, Panose())
	
	def compile(self, ttFont):
		panose = self.panose
		self.panose = sstruct.pack(panoseFormat, self.panose)
		if self.version == 0:
			data = sstruct.pack(OS2_format_0, self)
		elif self.version == 1:
			data = sstruct.pack(OS2_format_1, self)
		elif self.version in (2, 3, 4):
			data = sstruct.pack(OS2_format_2, self)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown format for OS/2 table: version %s" % self.version
		self.panose = panose
		return data
	
	def toXML(self, writer, ttFont):
		if self.version == 1:
			format = OS2_format_1
		elif self.version in (2, 3, 4):
			format = OS2_format_2
		else:
			format = OS2_format_0
		formatstring, names, fixes = sstruct.getformat(format)
		for name in names:
			value = getattr(self, name)
			if type(value) == type(0L):
				value = int(value)
			if name=="panose":
				writer.begintag("panose")
				writer.newline()
				value.toXML(writer, ttFont)
				writer.endtag("panose")
			elif name in ("ulUnicodeRange1", "ulUnicodeRange2", 
					"ulUnicodeRange3", "ulUnicodeRange4",
					"ulCodePageRange1", "ulCodePageRange2"):
				writer.simpletag(name, value=num2binary(value))
			elif name in ("fsType", "fsSelection"):
				writer.simpletag(name, value=num2binary(value, 16))
			elif name == "achVendID":
				writer.simpletag(name, value=repr(value)[1:-1])
			else:
				writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name == "panose":
			self.panose = panose = Panose()
			for element in content:
				if type(element) == TupleType:
					panose.fromXML(element, ttFont)
		elif name in ("ulUnicodeRange1", "ulUnicodeRange2", 
				"ulUnicodeRange3", "ulUnicodeRange4",
				"ulCodePageRange1", "ulCodePageRange2",
				"fsType", "fsSelection"):
			setattr(self, name, binary2num(attrs["value"]))
		elif name == "achVendID":
			setattr(self, name, safeEval("'''" + attrs["value"] + "'''"))
		else:
			setattr(self, name, safeEval(attrs["value"]))


