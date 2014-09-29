""" fontTools.ttLib.tables.unicodeRanges.py -- Tools for manipulating OS/2
Unicode Character Ranges.

See: http://www.microsoft.com/typography/otspec/os2.htm#ur
"""
from __future__ import print_function
from fontTools.misc.binTools import *


# sets of Unicode ranges sorted by bit number, as defined by OT Specs V1.6
UNICODE_BLOCK_RANGES = (
  frozenset(range(0x0000, 0x0080)),   # 0: Basic Latin
  frozenset(range(0x0080, 0x0100)),   # 1: Latin-1 Supplement
  frozenset(range(0x0100, 0x0180)),   # 2: Latin Extended-A
  frozenset(range(0x0180, 0x0250)),   # 3: Latin Extended-B
  frozenset(range(0x0250, 0x02B0)) |  # 4: IPA Extensions,
    frozenset(range(0x1D00, 0x1D80)) |  # Phonetic Extensions,
    frozenset(range(0x1D80, 0x1DC0)),   # Phonetic Extensions Supplement
  frozenset(range(0x02B0, 0x0300)) |  # 5: Spacing Modifier Letters,
    frozenset(range(0xA700, 0xA720)),   # Modifier Tone Letters
  frozenset(range(0x0300, 0x0370)) |  # 6: Combining Diacritical Marks,
    frozenset(range(0x1DC0, 0x1E00)),   # Combining Diacritical Marks Supplement
  frozenset(range(0x0370, 0x0400)),   # 7: Greek and Coptic
  frozenset(range(0x2C80, 0x2D00)),   # 8: Coptic
  frozenset(range(0x0400, 0x0500)) |  # 9: Cyrillic,
    frozenset(range(0x0500, 0x0530)) |  # Cyrillic Supplement,
    frozenset(range(0x2DE0, 0x2E00)) |  # Cyrillic Extended-A,
    frozenset(range(0xA640, 0xA6A0)),   # Cyrillic Extended-B
  frozenset(range(0x0530, 0x0590)),   # 10: Armenian
  frozenset(range(0x0590, 0x0600)),   # 11: Hebrew
  frozenset(range(0xA500, 0xA640)),   # 12: Vai
  frozenset(range(0x0600, 0x0700)) |  # 13: Arabic,
    frozenset(range(0x0750, 0x0780)),   # Arabic Supplement
  frozenset(range(0x07C0, 0x0800)),   # 14: NKo
  frozenset(range(0x0900, 0x0980)),   # 15: Devanagari
  frozenset(range(0x0980, 0x0A00)),   # 16: Bengali
  frozenset(range(0x0A00, 0x0A80)),   # 17: Gurmukhi
  frozenset(range(0x0A80, 0x0B00)),   # 18: Gujarati
  frozenset(range(0x0B00, 0x0B80)),   # 19: Oriya
  frozenset(range(0x0B80, 0x0C00)),   # 20: Tamil
  frozenset(range(0x0C00, 0x0C80)),   # 21: Telugu
  frozenset(range(0x0C80, 0x0D00)),   # 22: Kannada
  frozenset(range(0x0D00, 0x0D80)),   # 23: Malayalam
  frozenset(range(0x0E00, 0x0E80)),   # 24: Thai
  frozenset(range(0x0E80, 0x0F00)),   # 25: Lao
  frozenset(range(0x10A0, 0x1100)) |  # 26: Georgian,
    frozenset(range(0x2D00, 0x2D30)),   # Georgian Supplement
  frozenset(range(0x1B00, 0x1B80)),   # 27: Balinese
  frozenset(range(0x1100, 0x1200)),   # 28: Hangul Jamo
  frozenset(range(0x1E00, 0x1F00)) |  # 29: Latin Extended Additional,
    frozenset(range(0x2C60, 0x2C80)) |  # Latin Extended-C,
    frozenset(range(0xA720, 0xA800)),   # Latin Extended-D
  frozenset(range(0x1F00, 0x2000)),   # 30: Greek Extended
  frozenset(range(0x2000, 0x2070)) |  # 31: General Punctuation
    frozenset(range(0x2E00, 0x2E80)),   # Supplemental Punctuation
  frozenset(range(0x2070, 0x20A0)),   # 32: Superscripts And Subscripts
  frozenset(range(0x20A0, 0x20D0)),   # 33: Currency Symbols
  frozenset(range(0x20D0, 0x2100)),   # 34: Combining Diacritical Marks For Symbols
  frozenset(range(0x2100, 0x2150)),   # 35: Letterlike Symbols
  frozenset(range(0x2150, 0x2190)),   # 36: Number Forms
  frozenset(range(0x2190, 0x2200)) |  # 37: Arrows
    frozenset(range(0x27F0, 0x2800)) |  # Supplemental Arrows-A
    frozenset(range(0x2900, 0x2980)) |  # Supplemental Arrows-B
    frozenset(range(0x2B00, 0x2C00)),   # Miscellaneous Symbols and Arrows
  frozenset(range(0x2200, 0x2300)) |  # 38: Mathematical Operators
    frozenset(range(0x27C0, 0x27F0)) |  # Miscellaneous Mathematical Symbols-A
    frozenset(range(0x2980, 0x2A00)) |  # Miscellaneous Mathematical Symbols-B
    frozenset(range(0x2A00, 0x2B00)),   # Supplemental Mathematical Operators
  frozenset(range(0x2300, 0x2400)),   # 39: Miscellaneous Technical
  frozenset(range(0x2400, 0x2440)),   # 40: Control Pictures
  frozenset(range(0x2440, 0x2460)),   # 41: Optical Character Recognition
  frozenset(range(0x2460, 0x2500)),   # 42: Enclosed Alphanumerics
  frozenset(range(0x2500, 0x2580)),   # 43: Box Drawing
  frozenset(range(0x2580, 0x25A0)),   # 44: Block Elements
  frozenset(range(0x25A0, 0x2600)),   # 45: Geometric Shapes
  frozenset(range(0x2600, 0x2700)),   # 46: Miscellaneous Symbols
  frozenset(range(0x2700, 0x27C0)),   # 47: Dingbats
  frozenset(range(0x3000, 0x3040)),   # 48: CJK Symbols And Punctuation
  frozenset(range(0x3040, 0x30A0)),   # 49: Hiragana
  frozenset(range(0x30A0, 0x3100)) |  # 50: Katakana
    frozenset(range(0x31F0, 0x3200)),   # Katakana Phonetic Extensions
  frozenset(range(0x3100, 0x3130)) |  # 51: Bopomofo
    frozenset(range(0x31A0, 0x31C0)),   # Bopomofo Extended
  frozenset(range(0x3130, 0x3190)),   # 52: Hangul Compatibility Jamo
  frozenset(range(0xA840, 0xA880)),   # 53: Phags-pa
  frozenset(range(0x3200, 0x3300)),   # 54: Enclosed CJK Letters And Months
  frozenset(range(0x3300, 0x3400)),   # 55: CJK Compatibility
  frozenset(range(0xAC00, 0xD7B0)),   # 56: Hangul Syllables
  frozenset(range(0xD800, 0xE000)),   # 57: Non-Plane 0 *
  frozenset(range(0x10900, 0x10920)),   # 58: Phoenician
  frozenset(range(0x2E80, 0x2F00)) |  # 59: CJK Radicals Supplement
    frozenset(range(0x2F00, 0x2FE0)) |  # Kangxi Radicals
    frozenset(range(0x2FF0, 0x3000)) |  # Ideographic Description Characters
    frozenset(range(0x3190, 0x31A0)) |  # Kanbun
    frozenset(range(0x3400, 0x4DC0)) |  # CJK Unified Ideographs Extension A
    frozenset(range(0x4E00, 0xA000)) |  # CJK Unified Ideographs
    frozenset(range(0x20000, 0x2A6E0)),   # CJK Unified Ideographs Extension B
  frozenset(range(0xE000, 0xF900)),   # 60: Private Use Area (plane 0)
  frozenset(range(0x31C0, 0x31F0)) |  # 61: CJK Strokes
    frozenset(range(0xF900, 0xFB00)) |  # CJK Compatibility Ideographs
    frozenset(range(0x2F800, 0x2FA20)), # CJK Compatibility Ideographs Supplement
  frozenset(range(0xFB00, 0xFB50)),   # 62: Alphabetic Presentation Forms
  frozenset(range(0xFB50, 0xFE00)),   # 63: Arabic Presentation Forms-A
  frozenset(range(0xFE20, 0xFE30)),   # 64: Combining Half Marks
  frozenset(range(0xFE10, 0xFE20)) |  # 65: Vertical Forms
    frozenset(range(0xFE30, 0xFE50)),   # CJK Compatibility Forms
  frozenset(range(0xFE50, 0xFE70)),   # 66: Small Form Variants
  frozenset(range(0xFE70, 0xFF00)),   # 67: Arabic Presentation Forms-B
  frozenset(range(0xFF00, 0xFFF0)),   # 68: Halfwidth And Fullwidth Forms
  frozenset(range(0xFFF0, 0x10000)),   # 69 Specials
  frozenset(range(0x0F00, 0x1000)),   # 70: Tibetan
  frozenset(range(0x0700, 0x0750)),   # 71: Syriac
  frozenset(range(0x0780, 0x07C0)),   # 72: Thaana
  frozenset(range(0x0D80, 0x0E00)),   # 73: Sinhala
  frozenset(range(0x1000, 0x10A0)),   # 74: Myanmar
  frozenset(range(0x1200, 0x1380)) |  # 75: Ethiopic
    frozenset(range(0x1380, 0x13A0)) |  # Ethiopic Supplement
    frozenset(range(0x2D80, 0x2DE0)),   # Ethiopic Extended
  frozenset(range(0x13A0, 0x1400)),   # 76: Cherokee
  frozenset(range(0x1400, 0x1680)),   # 77: Unified Canadian Aboriginal Syllabics
  frozenset(range(0x1680, 0x16A0)),   # 78: Ogham
  frozenset(range(0x16A0, 0x1700)),   # 79: Runic
  frozenset(range(0x1780, 0x1800)) |  # 80: Khmer
    frozenset(range(0x19E0, 0x1A00)),   # Khmer Symbols
  frozenset(range(0x1800, 0x18B0)),   # 81: Mongolian
  frozenset(range(0x2800, 0x2900)),   # 82: Braille Patterns
  frozenset(range(0xA000, 0xA490)) |  # 83: Yi Syllables
    frozenset(range(0xA490, 0xA4D0)),   # Yi Radicals
  frozenset(range(0x1700, 0x1720)) |  # 84: Tagalog
    frozenset(range(0x1720, 0x1740)) |  # Hanunoo
    frozenset(range(0x1740, 0x1760)) |  # Buhid
    frozenset(range(0x1760, 0x1780)),   # Tagbanwa
  frozenset(range(0x10300, 0x10330)),   # 85: Old Italic
  frozenset(range(0x10330, 0x10350)),   # 86: Gothic
  frozenset(range(0x10400, 0x10450)),   # 87: Deseret
  frozenset(range(0x1D000, 0x1D100)) |  # 88: Byzantine Musical Symbols
    frozenset(range(0x1D100, 0x1D200)) |  # Musical Symbols
    frozenset(range(0x1D200, 0x1D250)),   # Ancient Greek Musical Notation
  frozenset(range(0x1D400, 0x1D800)),   # 89: Mathematical Alphanumeric Symbols
  frozenset(range(0xFF000, 0xFFFFE)) |  # 90: Private Use (plane 15)
    frozenset(range(0x100000, 0x10FFFE)),  # Private Use (plane 16)
  frozenset(range(0xFE00, 0xFE10)) |  # 91: Variation Selectors
    frozenset(range(0xE0100, 0xE01F0)),  # Variation Selectors Supplement
  frozenset(range(0xE0000, 0xE0080)),   # 92: Tags
  frozenset(range(0x1900, 0x1950)),   # 93: Limbu
  frozenset(range(0x1950, 0x1980)),   # 94: Tai Le
  frozenset(range(0x1980, 0x19E0)),   # 95: New Tai Lue
  frozenset(range(0x1A00, 0x1A20)),   # 96: Buginese
  frozenset(range(0x2C00, 0x2C60)),   # 97: Glagolitic
  frozenset(range(0x2D30, 0x2D80)),   # 98: Tifinagh
  frozenset(range(0x4DC0, 0x4E00)),   # 99: Yijing Hexagram Symbols
  frozenset(range(0xA800, 0xA830)),   # 100: Syloti Nagri
  frozenset(range(0x10000, 0x10080)) |  # 101: Linear B Syllabary
    frozenset(range(0x10080, 0x10100)) |  # Linear B Ideograms
    frozenset(range(0x10100, 0x10140)),   # Aegean Numbers
  frozenset(range(0x10140, 0x10190)),   # 102: Ancient Greek Numbers
  frozenset(range(0x10380, 0x103A0)),   # 103: Ugaritic
  frozenset(range(0x103A0, 0x103E0)),   # 104: Old Persian
  frozenset(range(0x10450, 0x10480)),   # 105: Shavian
  frozenset(range(0x10480, 0x104B0)),   # 106: Osmanya
  frozenset(range(0x10800, 0x10840)),   # 107: Cypriot Syllabary
  frozenset(range(0x10A00, 0x10A60)),   # 108: Kharoshthi
  frozenset(range(0x1D300, 0x1D360)),   # 109: Tai Xuan Jing Symbols
  frozenset(range(0x12000, 0x12400)) |  # 110: Cuneiform
    frozenset(range(0x12400, 0x12480)),   # Cuneiform Numbers and Punctuation
  frozenset(range(0x1D360, 0x1D380)),   # 111: Counting Rod Numerals
  frozenset(range(0x1B80, 0x1BC0)),   # 112: Sundanese
  frozenset(range(0x1C00, 0x1C50)),   # 113: Lepcha
  frozenset(range(0x1C50, 0x1C80)),   # 114: Ol Chiki
  frozenset(range(0xA880, 0xA8E0)),   # 115: Saurashtra
  frozenset(range(0xA900, 0xA930)),   # 116: Kayah Li
  frozenset(range(0xA930, 0xA960)),   # 117: Rejang
  frozenset(range(0xAA00, 0xAA60)),   # 118: Cham
  frozenset(range(0x10190, 0x101D0)),   # 119: Ancient Symbols
  frozenset(range(0x101D0, 0x10200)),   # 120: Phaistos Disc
  frozenset(range(0x10280, 0x102A0)) |  # 121: Lycian
    frozenset(range(0x102A0, 0x102E0)) |  # Carian
    frozenset(range(0x10920, 0x10940)),   # Lydian
  frozenset(range(0x1F000, 0x1F030)) |  # 122: Mahjong Tiles
    frozenset(range(0x1F030, 0x1F0A0)),   # Domino Tiles
  )


# Unicode blocks names sorted by bit number, as defined by the OT Specs V1.6
UNICODE_BLOCK_NAMES = (
  'Basic Latin',
  'Latin-1 Supplement',
  'Latin Extended-A',
  'Latin Extended-B',
  'IPA Extensions | Phonetic Extensions | Phonetic Extensions Supplement',
  'Spacing Modifier Letters | Modifier Tone Letters',
  'Combining Diacritical Marks | Combining Diacritical Marks Supplement',
  'Greek and Coptic',
  'Coptic',
  'Cyrillic | Cyrillic Supplement | Cyrillic Extended-A | Cyrillic Extended-B',
  'Armenian',
  'Hebrew',
  'Vai',
  'Arabic | Arabic Supplement',
  'NKo',
  'Devanagari',
  'Bengali',
  'Gurmukhi',
  'Gujarati',
  'Oriya',
  'Tamil',
  'Telugu',
  'Kannada',
  'Malayalam',
  'Thai',
  'Lao',
  'Georgian | Georgian Supplement',
  'Balinese',
  'Hangul Jamo',
  'Latin Extended Additional | Latin Extended-C | Latin Extended-D',
  'Greek Extended',
  'General Punctuation | Supplemental Punctuation',
  'Superscripts And Subscripts',
  'Currency Symbols',
  'Combining Diacritical Marks For Symbols',
  'Letterlike Symbols',
  'Number Forms',
  'Arrows | Supplemental Arrows-A | Supplemental Arrows-B | Miscellaneous Symbols and Arrows',
  'Mathematical Operators | Miscellaneous Mathematical Symbols-A | Miscellaneous Mathematical Symbols-B | Supplemental Mathematical Operators',
  'Miscellaneous Technical',
  'Control Pictures',
  'Optical Character Recognition',
  'Enclosed Alphanumerics',
  'Box Drawing',
  'Block Elements',
  'Geometric Shapes',
  'Miscellaneous Symbols',
  'Dingbats',
  'CJK Symbols And Punctuation',
  'Hiragana',
  'Katakana | Katakana Phonetic Extensions',
  'Bopomofo | Bopomofo Extended',
  'Hangul Compatibility Jamo',
  'Phags-pa',
  'Enclosed CJK Letters And Months',
  'CJK Compatibility',
  'Hangul Syllables',
  'Non-Plane 0 *',
  'Phoenician',
  'CJK Radicals Supplement | Kangxi Radicals | Ideographic Description Characters | Kanbun | CJK Unified Ideographs Extension A | CJK Unified Ideographs | CJK Unified Ideographs Extension B',
  'Private Use Area (plane 0)',
  'CJK Strokes | CJK Compatibility Ideographs | CJK Compatibility Ideographs Supplement',
  'Alphabetic Presentation Forms',
  'Arabic Presentation Forms-A',
  'Combining Half Marks',
  'Vertical Forms | CJK Compatibility Forms',
  'Small Form Variants',
  'Arabic Presentation Forms-B',
  'Halfwidth And Fullwidth Forms',
  'Specials',
  'Tibetan',
  'Syriac',
  'Thaana',
  'Sinhala',
  'Myanmar',
  'Ethiopic | Ethiopic Supplement | Ethiopic Extended',
  'Cherokee',
  'Unified Canadian Aboriginal Syllabics',
  'Ogham',
  'Runic',
  'Khmer | Khmer Symbols',
  'Mongolian',
  'Braille Patterns',
  'Yi Syllables | Yi Radicals',
  'Tagalog | Hanunoo | Buhid | Tagbanwa',
  'Old Italic',
  'Gothic',
  'Deseret',
  'Byzantine Musical Symbols | Musical Symbols | Ancient Greek Musical Notation',
  'Mathematical Alphanumeric Symbols',
  'Private Use (plane 15) | Private Use (plane 16)',
  'Variation Selectors | Variation Selectors Supplement',
  'Tags',
  'Limbu',
  'Tai Le',
  'New Tai Lue',
  'Buginese',
  'Glagolitic',
  'Tifinagh',
  'Yijing Hexagram Symbols',
  'Syloti Nagri',
  'Linear B Syllabary | Linear B Ideograms | Aegean Numbers',
  'Ancient Greek Numbers',
  'Ugaritic',
  'Old Persian',
  'Shavian',
  'Osmanya',
  'Cypriot Syllabary',
  'Kharoshthi',
  'Tai Xuan Jing Symbols',
  'Cuneiform | Cuneiform Numbers and Punctuation',
  'Counting Rod Numerals',
  'Sundanese',
  'Lepcha',
  'Ol Chiki',
  'Saurashtra',
  'Kayah Li',
  'Rejang',
  'Cham',
  'Ancient Symbols',
  'Phaistos Disc',
  'Lycian | Carian | Lydian',
  'Mahjong Tiles | Domino Tiles'
  )


def getRanges(ttFont):
  """ Return a (bit, name) dict of the UnicodeRanges enabled in ttFont."""
  bits = set()
  for i in range(32):
    if testBit(ttFont['OS/2'].ulUnicodeRange1, i):
      bits.add(i)
    if testBit(ttFont['OS/2'].ulUnicodeRange2, i):
      bits.add(i + 32)
    if testBit(ttFont['OS/2'].ulUnicodeRange3, i):
      bits.add(i + 64)
    if testBit(ttFont['OS/2'].ulUnicodeRange4, i):
      bits.add(i + 96)
  bits = sorted(bits)
  names = [UNICODE_BLOCK_NAMES[bit] for bit in bits]
  return dict(zip(bits, names))


def setRanges(ttFont, bits):
  """Set the 'ulUnicodeRange' values in ttFont to a list of bit numbers."""
  # build synthetic 128-bit integer
  ulUnicodeRanges = 0
  for bit in bits:
    ulUnicodeRanges = setBit(ulUnicodeRanges, bit)

  # slice it into four 32-bit integers
  ulUnicodeRange1 = int(getBitRange(ulUnicodeRanges, 0, 32))
  ulUnicodeRange2 = int(getBitRange(ulUnicodeRanges, 32, 64))
  ulUnicodeRange3 = int(getBitRange(ulUnicodeRanges, 64, 96))
  ulUnicodeRange4 = int(getBitRange(ulUnicodeRanges, 96, 128))

  # update the corresponding OS/2 fields
  ttFont['OS/2'].ulUnicodeRange1 = ulUnicodeRange1
  ttFont['OS/2'].ulUnicodeRange2 = ulUnicodeRange2
  ttFont['OS/2'].ulUnicodeRange3 = ulUnicodeRange3
  ttFont['OS/2'].ulUnicodeRange4 = ulUnicodeRange4


def calculateBits(unicodes):
  """ Given a list of (int) Unicode codepoints, test the intersection with the
  Unicode block ranges defined in the OpenType specification v1.6.
  Return the corresponding 'ulUnicodeRange' bits.
  """
  unicodes = set(unicodes)
  bits = set()
  for bit, block in enumerate(UNICODE_BLOCK_RANGES):
    if not block.isdisjoint(unicodes):
      bits.add(bit)
  return sorted(bits)


def updateRanges(ttFont):
  """ Update the OS/2 'ulUnicodeRange' values according to the codepoints
  specified in the font's Unicode cmap tables.
  Return True if values were modifed.
  """
  # get the original 'ulUnicodeRange' bits
  orig_ranges = getRanges(ttFont)
  # gather all Unicode codepoints in ttFont
  unicodes = set()
  for t in ttFont['cmap'].tables:
    if t.isUnicode():
      unicodes.update(t.cmap.keys())
  # calculate the 'ulUnicodeRange' bits that intersect the given set
  new_bits = calculateBits(unicodes)
  # check the difference between the original and calculated bits
  if set(orig_ranges.keys()) ^ set(new_bits):
    # if different, update the 'ulUnicodeRange' values
    setRanges(ttFont, new_bits)
    return True
  return False
