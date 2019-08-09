import io
import os
import re
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.fontBuilder import FontBuilder
import unittest
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable, table__c_m_a_p

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, 'data')
CMAP_FORMAT_14_TTX = os.path.join(DATA_DIR, "_c_m_a_p_format_14.ttx")
CMAP_FORMAT_14_BW_COMPAT_TTX = os.path.join(DATA_DIR, "_c_m_a_p_format_14_bw_compat.ttx")

def strip_VariableItems(string):
    # ttlib changes with the fontTools version
    string = re.sub(' ttLibVersion=".*"', '', string)
    return string

class CmapSubtableTest(unittest.TestCase):

	def makeSubtable(self, cmapFormat, platformID, platEncID, langID):
		subtable = CmapSubtable.newSubtable(cmapFormat)
		subtable.platformID, subtable.platEncID, subtable.language = (platformID, platEncID, langID)
		return subtable

	def test_toUnicode_utf16be(self):
		subtable = self.makeSubtable(4, 0, 2, 7)
		self.assertEqual("utf_16_be", subtable.getEncoding())
		self.assertEqual(True, subtable.isUnicode())

	def test_toUnicode_macroman(self):
		subtable = self.makeSubtable(4, 1, 0, 7)  # MacRoman
		self.assertEqual("mac_roman", subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_toUnicode_macromanian(self):
		subtable = self.makeSubtable(4, 1, 0, 37)  # Mac Romanian
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_mac_encodings(self):
		subtable = self.makeSubtable(4, 1, 1, 0) # Mac Japanese
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_unknown(self):
		subtable = self.makeSubtable(4, 10, 11, 12)
		self.assertEqual(subtable.getEncoding(), None)
		self.assertEqual(subtable.getEncoding("ascii"), "ascii")
		self.assertEqual(subtable.getEncoding(default="xyz"), "xyz")

	def test_compile_2(self):
		subtable = self.makeSubtable(2, 1, 2, 0)
		subtable.cmap = {c: "cid%05d" % c for c in range(32, 8192)}
		font = ttLib.TTFont()
		font.setGlyphOrder([".notdef"] + list(subtable.cmap.values()))
		data = subtable.compile(font)

		subtable2 = CmapSubtable.newSubtable(2)
		subtable2.decompile(data, font)
		self.assertEqual(subtable2.cmap, subtable.cmap)

	def test_compile_2_rebuild_rev_glyph_order(self):
		for fmt in [2, 4, 12]:
			subtable = self.makeSubtable(fmt, 1, 2, 0)
			subtable.cmap = {c: "cid%05d" % c for c in range(32, 8192)}
			font = ttLib.TTFont()
			font.setGlyphOrder([".notdef"] + list(subtable.cmap.values()))
			font._reverseGlyphOrderDict = {}  # force first KeyError branch in subtable.compile()
			data = subtable.compile(font)
			subtable2 = CmapSubtable.newSubtable(fmt)
			subtable2.decompile(data, font)
			self.assertEqual(subtable2.cmap, subtable.cmap, str(fmt))

	def test_compile_2_gids(self):
		for fmt in [2, 4, 12]:
			subtable = self.makeSubtable(fmt, 1, 3, 0)
			subtable.cmap = {0x0041:'gid001', 0x0042:'gid002'}
			font = ttLib.TTFont()
			font.setGlyphOrder([".notdef"])
			data = subtable.compile(font)

	def test_compile_decompile_4_empty(self):
		subtable = self.makeSubtable(4, 3, 1, 0)
		subtable.cmap = {}
		font = ttLib.TTFont()
		font.setGlyphOrder([])
		data = subtable.compile(font)
		subtable2 = CmapSubtable.newSubtable(4)
		subtable2.decompile(data, font)
		self.assertEqual(subtable2.cmap, {})

	def test_decompile_4(self):
		subtable = CmapSubtable.newSubtable(4)
		font = ttLib.TTFont()
		font.setGlyphOrder([])
		subtable.decompile(b'\0' * 3 + b'\x10' + b'\0' * 12, font)

	def test_decompile_12(self):
		subtable = CmapSubtable.newSubtable(12)
		font = ttLib.TTFont()
		font.setGlyphOrder([])
		subtable.decompile(b'\0' * 7 + b'\x10' + b'\0' * 8, font)

	def test_buildReversed(self):
		c4 = self.makeSubtable(4, 3, 1, 0)
		c4.cmap = {0x0041:'A', 0x0391:'A'}
		c12 = self.makeSubtable(12, 3, 10, 0)
		c12.cmap = {0x10314: 'u10314'}
		cmap = table__c_m_a_p()
		cmap.tables = [c4, c12]
		self.assertEqual(cmap.buildReversed(), {'A':{0x0041, 0x0391}, 'u10314':{0x10314}})

	def test_getBestCmap(self):
		c4 = self.makeSubtable(4, 3, 1, 0)
		c4.cmap = {0x0041:'A', 0x0391:'A'}
		c12 = self.makeSubtable(12, 3, 10, 0)
		c12.cmap = {0x10314: 'u10314'}
		cmap = table__c_m_a_p()
		cmap.tables = [c4, c12]
		self.assertEqual(cmap.getBestCmap(), {0x10314: 'u10314'})
		self.assertEqual(cmap.getBestCmap(cmapPreferences=[(3, 1)]), {0x0041:'A', 0x0391:'A'})
		self.assertEqual(cmap.getBestCmap(cmapPreferences=[(0, 4)]), None)

	def test_font_getBestCmap(self):
		c4 = self.makeSubtable(4, 3, 1, 0)
		c4.cmap = {0x0041:'A', 0x0391:'A'}
		c12 = self.makeSubtable(12, 3, 10, 0)
		c12.cmap = {0x10314: 'u10314'}
		cmap = table__c_m_a_p()
		cmap.tables = [c4, c12]
		font = ttLib.TTFont()
		font["cmap"] = cmap
		self.assertEqual(font.getBestCmap(), {0x10314: 'u10314'})
		self.assertEqual(font.getBestCmap(cmapPreferences=[(3, 1)]), {0x0041:'A', 0x0391:'A'})
		self.assertEqual(font.getBestCmap(cmapPreferences=[(0, 4)]), None)

	def test_format_14(self):
		subtable = self.makeSubtable(14, 0, 5, 0)
		subtable.cmap = {}  # dummy
		subtable.uvsDict = {
			0xFE00: [(0x0030, "zero.slash")],
			0xFE01: [(0x0030, None)],
		}
		fb = FontBuilder(1024, isTTF=True)
		font = fb.font
		fb.setupGlyphOrder([".notdef", "zero.slash"])
		fb.setupMaxp()
		fb.setupPost()
		cmap = table__c_m_a_p()
		cmap.tableVersion = 0
		cmap.tables = [subtable]
		font["cmap"] = cmap
		f = io.BytesIO()
		font.save(f)
		f.seek(0)
		font = ttLib.TTFont(f)
		self.assertEqual(font["cmap"].getcmap(0, 5).uvsDict, subtable.uvsDict)
		f = io.StringIO(newline=None)
		font.saveXML(f, tables=["cmap"])
		ttx = strip_VariableItems(f.getvalue())
		with open(CMAP_FORMAT_14_TTX) as f:
			expected = strip_VariableItems(f.read())
		self.assertEqual(ttx, expected)
		with open(CMAP_FORMAT_14_BW_COMPAT_TTX) as f:
			font.importXML(f)
		self.assertEqual(font["cmap"].getcmap(0, 5).uvsDict, subtable.uvsDict)


if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())
