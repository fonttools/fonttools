from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError, getTableClass, getTableModule, newTable
import unittest


gvarClass = getTableClass("gvar")


GVAR_DATA_EMPTY_VARIATIONS = deHexStr(
    "0001 0000 "           #  0: majorVersion=1 minorVersion=0
    "0002 0000 "           #  4: axisCount=2 sharedTupleCount=0
    "0000001c "            #  8: offsetToSharedTuples=28
    "0003 0000 "           # 12: glyphCount=3 flags=0
    "0000001c "            # 16: offsetToGlyphVariationData=28
    "0000 0000 0000 0000"  # 20: offsets=[0, 0, 0, 0]
)                          # 28: <end>


def hexencode(s):
	h = hexStr(s).upper()
	return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])


class GVARTableTest(unittest.TestCase):
	def makeFont(self, glyphs=[".notdef", "space", "I"]):
		Axis = getTableModule("fvar").Axis
		Glyph = getTableModule("glyf").Glyph
		glyf, fvar, gvar = newTable("glyf"), newTable("fvar"), newTable("gvar")
		font = FakeFont(glyphs)
		font.tables = {"glyf": glyf, "gvar": gvar, "fvar": fvar}
		glyf.glyphs = {glyph: Glyph() for glyph in glyphs}
		fvar.axes = [Axis(), Axis()]
		fvar.axes[0].axisTag, fvar.axes[1].axisTag = "wght", "wdth"
		return font, gvar

	def test_compile_noVariations(self):
		font, gvar = self.makeFont()
		self.assertEqual(hexStr(gvar.compile(font)),
		                 hexStr(GVAR_DATA_EMPTY_VARIATIONS))

	def test_compile_emptyVariations(self):
		font, gvar = self.makeFont()
		gvar.variations = {".notdef": [], "space": [], "I": []}
		self.assertEqual(hexStr(gvar.compile(font)),
		                 hexStr(GVAR_DATA_EMPTY_VARIATIONS))

	def test_decompile_noVariations(self):
		font, gvar = self.makeFont()
		gvar.decompile(GVAR_DATA_EMPTY_VARIATIONS, font)
		self.assertEqual(gvar.variations,
		                 {".notdef": [], "space": [], "I": []})

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


if __name__ == "__main__":
	unittest.main()
