from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError, getTableClass, getTableModule, newTable
from fontTools.ttLib.tables.TupleVariation import \
	TupleVariation, decompileTupleVariations
import unittest


gvar = getTableModule("gvar")
gvarClass = getTableClass("gvar")


def hexencode(s):
	h = hexStr(s).upper()
	return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])


class GVARTableTest(unittest.TestCase):
	def test_compileOffsets_shortFormat(self):
		self.assertEqual((deHexStr("00 00 00 02 FF C0"), 0),
		                 gvarClass.compileOffsets_([0, 4, 0x1ff80]))

	def test_compileOffsets_longFormat(self):
		self.assertEqual((deHexStr("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
		                 gvarClass.compileOffsets_([0, 4, 0xCAFEBEEF]))

	def test_decompileOffsets_shortFormat(self):
		decompileOffsets = gvarClass.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual(
			[2*0x0011, 2*0x2233, 2*0x4455, 2*0x6677, 2*0x8899, 2*0xaabb],
			list(decompileOffsets(data, tableFormat=0, glyphCount=5)))

	def test_decompileOffsets_longFormat(self):
		decompileOffsets = gvarClass.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual(
			[0x00112233, 0x44556677, 0x8899aabb],
			list(decompileOffsets(data, tableFormat=1, glyphCount=2)))

	def test_compileGlyph_noVariations(self):
		table = newTable("gvar")
		table.variations = {}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_emptyVariations(self):
		table = newTable("gvar")
		table.variations = {"glyphname": []}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_onlyRedundantVariations(self):
		table = newTable("gvar")
		axes = {"wght": (0.3, 0.4, 0.5), "opsz": (0.7, 0.8, 0.9)}
		table.variations = {"glyphname": [
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4)
		]}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_roundTrip(self):
		table = newTable("gvar")
		axisTags = ["wght", "wdth"]
		numPointsInGlyph = 4
		glyphCoords = [(1,1), (2,2), (3,3), (4,4)]
		gvar1 = TupleVariation({"wght": (0.5, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		gvar2 = TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		table.variations = {"oslash": [gvar1, gvar2]}
		data = table.compileGlyph_("oslash", numPointsInGlyph, axisTags, {})
		self.assertEqual(
			[gvar1, gvar2],
			decompileTupleVariations(numPointsInGlyph, {},
									 "gvar", axisTags, data))


if __name__ == "__main__":
	unittest.main()
