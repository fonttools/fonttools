from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval, num2binary, binary2num
from . import DefaultTable
import warnings


# Unicode ranges as per OpenType Specification V1.6

OS2_UNICODE_RANGES = (
	[(0x0000, 0x007F)],  # 0: Basic Latin
	[(0x0080, 0x00FF)],  # 1: Latin-1 Supplement
	[(0x0100, 0x017F)],  # 2: Latin Extended-A
	[(0x0180, 0x024F)],  # 3: Latin Extended-B
	[(0x0250, 0x02AF),   # 4: IPA Extensions,
		(0x1D00, 0x1D7F),   # Phonetic Extensions,
		(0x1D80, 0x1DBF)],  # Phonetic Extensions Supplement
	[(0x02B0, 0x02FF),   # 5: Spacing Modifier Letters,
		(0xA700, 0xA71F)],  # Modifier Tone Letters
	[(0x0300, 0x036F),   # 6: Combining Diacritical Marks,
		(0x1DC0, 0x1DFF)],  # Combining Diacritical Marks Supplement
	[(0x0370, 0x03FF)],  # 7: Greek and Coptic
	[(0x2C80, 0x2CFF)],  # 8: Coptic
	[(0x0400, 0x04FF),   # 9: Cyrillic,
		(0x0500, 0x052F),   # Cyrillic Supplement,
		(0x2DE0, 0x2DFF),   # Cyrillic Extended-A,
		(0xA640, 0xA69F)],  # Cyrillic Extended-B
	[(0x0530, 0x058F)],  # 10: Armenian
	[(0x0590, 0x05FF)],  # 11: Hebrew
	[(0xA500, 0xA63F)],  # 12: Vai
	[(0x0600, 0x06FF),   # 13: Arabic,
		(0x0750, 0x077F)],   # Arabic Supplement
	[(0x07C0, 0x07FF)],  # 14: NKo
	[(0x0900, 0x097F)],  # 15: Devanagari
	[(0x0980, 0x09FF)],  # 16: Bengali
	[(0x0A00, 0x0A7F)],  # 17: Gurmukhi
	[(0x0A80, 0x0AFF)],  # 18: Gujarati
	[(0x0B00, 0x0B7F)],  # 19: Oriya
	[(0x0B80, 0x0BFF)],  # 20: Tamil
	[(0x0C00, 0x0C7F)],  # 21: Telugu
	[(0x0C80, 0x0CFF)],  # 22: Kannada
	[(0x0D00, 0x0D7F)],  # 23: Malayalam
	[(0x0E00, 0x0E7F)],  # 24: Thai
	[(0x0E80, 0x0EFF)],  # 25: Lao
	[(0x10A0, 0x10FF),   # 26: Georgian,
		(0x2D00, 0x2D2F)],   # Georgian Supplement
	[(0x1B00, 0x1B7F)],  # 27: Balinese
	[(0x1100, 0x11FF)],  # 28: Hangul Jamo
	[(0x1E00, 0x1EFF),   # 29: Latin Extended Additional,
		(0x2C60, 0x2C7F),    # Latin Extended-C,
		(0xA720, 0xA7FF)],   # Latin Extended-D
	[(0x1F00, 0x1FFF)],  # 30: Greek Extended
	[(0x2000, 0x206F),   # 31: General Punctuation
		(0x2E00, 0x2E7F)],   # Supplemental Punctuation
	[(0x2070, 0x209F)],  # 32: Superscripts And Subscripts
	[(0x20A0, 0x20CF)],  # 33: Currency Symbols
	[(0x20D0, 0x20FF)],  # 34: Combining Diacritical Marks For Symbols
	[(0x2100, 0x214F)],  # 35: Letterlike Symbols
	[(0x2150, 0x218F)],  # 36: Number Forms
	[(0x2190, 0x21FF),   # 37: Arrows
		(0x27F0, 0x27FF),    # Supplemental Arrows-A
		(0x2900, 0x297F),    # Supplemental Arrows-B
		(0x2B00, 0x2BFF)],   # Miscellaneous Symbols and Arrows
	[(0x2200, 0x22FF),   # 38: Mathematical Operators
		(0x27C0, 0x27EF),    # Miscellaneous Mathematical Symbols-A
		(0x2980, 0x29FF),    # Miscellaneous Mathematical Symbols-B
		(0x2A00, 0x2AFF)],   # Supplemental Mathematical Operators
	[(0x2300, 0x23FF)],  # 39: Miscellaneous Technical
	[(0x2400, 0x243F)],  # 40: Control Pictures
	[(0x2440, 0x245F)],  # 41: Optical Character Recognition
	[(0x2460, 0x24FF)],  # 42: Enclosed Alphanumerics
	[(0x2500, 0x257F)],  # 43: Box Drawing
	[(0x2580, 0x259F)],  # 44: Block Elements
	[(0x25A0, 0x25FF)],  # 45: Geometric Shapes
	[(0x2600, 0x26FF)],  # 46: Miscellaneous Symbols
	[(0x2700, 0x27BF)],  # 47: Dingbats
	[(0x3000, 0x303F)],  # 48: CJK Symbols And Punctuation
	[(0x3040, 0x309F)],  # 49: Hiragana
	[(0x30A0, 0x30FF),   # 50: Katakana
		(0x31F0, 0x31FF)],   # Katakana Phonetic Extensions
	[(0x3100, 0x312F),   # 51: Bopomofo
		(0x31A0, 0x31BF)],   # Bopomofo Extended
	[(0x3130, 0x318F)],  # 52: Hangul Compatibility Jamo
	[(0xA840, 0xA87F)],  # 53: Phags-pa
	[(0x3200, 0x32FF)],  # 54: Enclosed CJK Letters And Months
	[(0x3300, 0x33FF)],  # 55: CJK Compatibility
	[(0xAC00, 0xD7AF)],  # 56: Hangul Syllables
	[(0xD800, 0xDFFF)],  # 57: Non-Plane 0 (if at least one codepoint > 0xFFFF)
	[(0x10900, 0x1091F)],  # 58: Phoenician
	[(0x2E80, 0x2EFF),   # 59: CJK Radicals Supplement
		(0x2F00, 0x2FDF),    # Kangxi Radicals
		(0x2FF0, 0x2FFF),    # Ideographic Description Characters
		(0x3190, 0x319F),    # Kanbun
		(0x3400, 0x4DBF),    # CJK Unified Ideographs Extension A
		(0x4E00, 0x9FFF),    # CJK Unified Ideographs
		(0x20000, 0x2A6DF)],  # CJK Unified Ideographs Extension B
	[(0xE000, 0xF8FF)],  # 60: Private Use Area (plane 0)
	[(0x31C0, 0x31EF),   # 61: CJK Strokes
		(0xF900, 0xFAFF),    # CJK Compatibility Ideographs
		(0x2F800, 0x2FA1F)],  # CJK Compatibility Ideographs Supplement
	[(0xFB00, 0xFB4F)],  # 62: Alphabetic Presentation Forms
	[(0xFB50, 0xFDFF)],  # 63: Arabic Presentation Forms-A
	[(0xFE20, 0xFE2F)],  # 64: Combining Half Marks
	[(0xFE10, 0xFE1F),   # 65: Vertical Forms
		(0xFE30, 0xFE4F)],   # CJK Compatibility Forms
	[(0xFE50, 0xFE6F)],  # 66: Small Form Variants
	[(0xFE70, 0xFEFF)],  # 67: Arabic Presentation Forms-B
	[(0xFF00, 0xFFEF)],  # 68: Halfwidth And Fullwidth Forms
	[(0xFFF0, 0xFFFF)],  # 69 Specials
	[(0x0F00, 0x0FFF)],  # 70: Tibetan
	[(0x0700, 0x074F)],  # 71: Syriac
	[(0x0780, 0x07BF)],  # 72: Thaana
	[(0x0D80, 0x0DFF)],  # 73: Sinhala
	[(0x1000, 0x109F)],  # 74: Myanmar
	[(0x1200, 0x137F),   # 75: Ethiopic
		(0x1380, 0x139F),    # Ethiopic Supplement
		(0x2D80, 0x2DDF)],   # Ethiopic Extended
	[(0x13A0, 0x13FF)],  # 76: Cherokee
	[(0x1400, 0x167F)],  # 77: Unified Canadian Aboriginal Syllabics
	[(0x1680, 0x169F)],  # 78: Ogham
	[(0x16A0, 0x16FF)],  # 79: Runic
	[(0x1780, 0x17FF),   # 80: Khmer
		(0x19E0, 0x19FF)],   # Khmer Symbols
	[(0x1800, 0x18AF)],  # 81: Mongolian
	[(0x2800, 0x28FF)],  # 82: Braille Patterns
	[(0xA000, 0xA48F),   # 83: Yi Syllables
		(0xA490, 0xA4CF)],   # Yi Radicals
	[(0x1700, 0x171F),   # 84: Tagalog
		(0x1720, 0x173F),    # Hanunoo
		(0x1740, 0x175F),    # Buhid
		(0x1760, 0x177F)],   # Tagbanwa
	[(0x10300, 0x1032F)],  # 85: Old Italic
	[(0x10330, 0x1034F)],  # 86: Gothic
	[(0x10400, 0x1044F)],  # 87: Deseret
	[(0x1D000, 0x1D0FF),   # 88: Byzantine Musical Symbols
		(0x1D100, 0x1D1FF),    # Musical Symbols
		(0x1D200, 0x1D24F)],   # Ancient Greek Musical Notation
	[(0x1D400, 0x1D7FF)],  # 89: Mathematical Alphanumeric Symbols
	[(0xFF000, 0xFFFFD),   # 90: Private Use (plane 15)
		(0x100000, 0x10FFFD)],  # Private Use (plane 16)
	[(0xFE00, 0xFE0F),   # 91: Variation Selectors
		(0xE0100, 0xE01EF)],  # Variation Selectors Supplement
	[(0xE0000, 0xE007F)],  # 92: Tags
	[(0x1900, 0x194F)],  # 93: Limbu
	[(0x1950, 0x197F)],  # 94: Tai Le
	[(0x1980, 0x19DF)],  # 95: New Tai Lue
	[(0x1A00, 0x1A1F)],  # 96: Buginese
	[(0x2C00, 0x2C5F)],  # 97: Glagolitic
	[(0x2D30, 0x2D7F)],  # 98: Tifinagh
	[(0x4DC0, 0x4DFF)],  # 99: Yijing Hexagram Symbols
	[(0xA800, 0xA82F)],  # 100: Syloti Nagri
	[(0x10000, 0x1007F),   # 101: Linear B Syllabary
		(0x10080, 0x100FF),     # Linear B Ideograms
		(0x10100, 0x1013F)],    # Aegean Numbers
	[(0x10140, 0x1018F)],  # 102: Ancient Greek Numbers
	[(0x10380, 0x1039F)],  # 103: Ugaritic
	[(0x103A0, 0x103DF)],  # 104: Old Persian
	[(0x10450, 0x1047F)],  # 105: Shavian
	[(0x10480, 0x104AF)],  # 106: Osmanya
	[(0x10800, 0x1083F)],  # 107: Cypriot Syllabary
	[(0x10A00, 0x10A5F)],  # 108: Kharoshthi
	[(0x1D300, 0x1D35F)],  # 109: Tai Xuan Jing Symbols
	[(0x12000, 0x123FF),   # 110: Cuneiform
		(0x12400, 0x1247F)],    # Cuneiform Numbers and Punctuation
	[(0x1D360, 0x1D37F)],  # 111: Counting Rod Numerals
	[(0x1B80, 0x1BBF)],  # 112: Sundanese
	[(0x1C00, 0x1C4F)],  # 113: Lepcha
	[(0x1C50, 0x1C7F)],  # 114: Ol Chiki
	[(0xA880, 0xA8DF)],  # 115: Saurashtra
	[(0xA900, 0xA92F)],  # 116: Kayah Li
	[(0xA930, 0xA95F)],  # 117: Rejang
	[(0xAA00, 0xAA5F)],  # 118: Cham
	[(0x10190, 0x101CF)],  # 119: Ancient Symbols
	[(0x101D0, 0x101FF)],  # 120: Phaistos Disc
	[(0x10280, 0x1029F),   # 121: Lycian
		(0x102A0, 0x102DF),     # Carian
		(0x10920, 0x1093F)],    # Lydian
	[(0x1F000, 0x1F02F),   # 122: Mahjong Tiles
		(0x1F030, 0x1F09F)],    # Domino Tiles
	)


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

class Panose(object):
	
	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(panoseFormat)
		for name in names:
			writer.simpletag(name, value=getattr(self, name))
			writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
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

OS2_format_5_addition =  OS2_format_2_addition + """
	usLowerOpticalPointSize:    H
	usUpperOpticalPointSize:    H
"""

bigendian = "	>	# big endian\n"

OS2_format_1 = OS2_format_0 + OS2_format_1_addition
OS2_format_2 = OS2_format_0 + OS2_format_2_addition
OS2_format_5 = OS2_format_0 + OS2_format_5_addition
OS2_format_1_addition = bigendian + OS2_format_1_addition
OS2_format_2_addition = bigendian + OS2_format_2_addition
OS2_format_5_addition = bigendian + OS2_format_5_addition


class table_O_S_2f_2(DefaultTable.DefaultTable):
	
	"""the OS/2 table"""
	
	def decompile(self, data, ttFont):
		dummy, data = sstruct.unpack2(OS2_format_0, data, self)

		if self.version == 1:
			dummy, data = sstruct.unpack2(OS2_format_1_addition, data, self)
		elif self.version in (2, 3, 4):
			dummy, data = sstruct.unpack2(OS2_format_2_addition, data, self)
		elif self.version == 5:
			dummy, data = sstruct.unpack2(OS2_format_5_addition, data, self)
			self.usLowerOpticalPointSize /= 20
			self.usUpperOpticalPointSize /= 20
		elif self.version != 0:
			from fontTools import ttLib
			raise ttLib.TTLibError("unknown format for OS/2 table: version %s" % self.version)
		if len(data):
			warnings.warn("too much 'OS/2' table data")

		self.panose = sstruct.unpack(panoseFormat, self.panose, Panose())
	
	def compile(self, ttFont):
		panose = self.panose
		self.panose = sstruct.pack(panoseFormat, self.panose)
		if ttFont.recalcUnicodeRanges:
			self.updateUnicodeRanges(ttFont)
		if self.version == 0:
			data = sstruct.pack(OS2_format_0, self)
		elif self.version == 1:
			data = sstruct.pack(OS2_format_1, self)
		elif self.version in (2, 3, 4):
			data = sstruct.pack(OS2_format_2, self)
		elif self.version == 5:
			d = self.__dict__.copy()
			d['usLowerOpticalPointSize'] = int(round(self.usLowerOpticalPointSize * 20))
			d['usUpperOpticalPointSize'] = int(round(self.usUpperOpticalPointSize * 20))
			data = sstruct.pack(OS2_format_5, d)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("unknown format for OS/2 table: version %s" % self.version)
		self.panose = panose
		return data
	
	def toXML(self, writer, ttFont):
		if self.version == 1:
			format = OS2_format_1
		elif self.version in (2, 3, 4):
			format = OS2_format_2
		elif self.version == 5:
			format = OS2_format_5
		else:
			format = OS2_format_0
		formatstring, names, fixes = sstruct.getformat(format)
		for name in names:
			value = getattr(self, name)
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
	
	def fromXML(self, name, attrs, content, ttFont):
		if name == "panose":
			self.panose = panose = Panose()
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					panose.fromXML(name, attrs, content, ttFont)
		elif name in ("ulUnicodeRange1", "ulUnicodeRange2", 
				"ulUnicodeRange3", "ulUnicodeRange4",
				"ulCodePageRange1", "ulCodePageRange2",
				"fsType", "fsSelection"):
			setattr(self, name, binary2num(attrs["value"]))
		elif name == "achVendID":
			setattr(self, name, safeEval("'''" + attrs["value"] + "'''"))
		else:
			setattr(self, name, safeEval(attrs["value"]))

	def updateUnicodeRanges(self, ttFont):
		""" Update the OS/2 'ulUnicodeRange' values according to the code points
		specified in the font's Unicode cmap tables.
		"""
		# gather all the Unicode code points specified in ttFont
		unicodes = set()
		for t in ttFont['cmap'].tables:
			if t.isUnicode():
				unicodes.update(t.cmap.keys())
		# set the 'ulUnicodeRange' bits that intersect the given code points
		ulUnicodeRange1 = ulUnicodeRange2 = ulUnicodeRange3 = ulUnicodeRange4 = 0
		for bit, unirange in enumerate(OS2_UNICODE_RANGES):
			for start, stop in unirange:
				if not set(range(start, stop+1)).isdisjoint(unicodes):
					if 0 <= bit < 32:
						ulUnicodeRange1 |= 1 << bit
					elif 32 <= bit < 64:
						ulUnicodeRange2 |= 1 << (bit - 32)
					elif 64 <= bit < 96:
						ulUnicodeRange3 |= 1 << (bit - 64)
					elif 96 <= bit < 123:
						ulUnicodeRange4 |= 1 << (bit - 96)
					break
		# set the special bit 57 if at least one codepoint is beyond the BMP
		if not set(range(0x10000, 0x110000)).isdisjoint(unicodes):
			ulUnicodeRange2 |= 1 << (57 - 32)
		self.ulUnicodeRange1 = ulUnicodeRange1
		self.ulUnicodeRange2 = ulUnicodeRange2
		self.ulUnicodeRange3 = ulUnicodeRange3
		self.ulUnicodeRange4 = ulUnicodeRange4
