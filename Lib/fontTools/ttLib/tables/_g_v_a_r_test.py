from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r
import unittest

def hexencode(s):
	h = hexStr(s).upper()
	return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])

# Glyph variation table of uppercase I in the Skia font, as printed in Apple's
# TrueType spec. The actual Skia font uses a different table for uppercase I.
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
SKIA_GVAR_I = deHexStr(
	"00 08 00 24 00 33 20 00 00 15 20 01 00 1B 20 02 "
	"00 24 20 03 00 15 20 04 00 26 20 07 00 0D 20 06 "
	"00 1A 20 05 00 40 01 01 01 81 80 43 FF 7E FF 7E "
	"FF 7E FF 7E 00 81 45 01 01 01 03 01 04 01 04 01 "
	"04 01 02 80 40 00 82 81 81 04 3A 5A 3E 43 20 81 "
	"04 0E 40 15 45 7C 83 00 0D 9E F3 F2 F0 F0 F0 F0 "
	"F3 9E A0 A1 A1 A1 9F 80 00 91 81 91 00 0D 0A 0A "
	"09 0A 0A 0A 0A 0A 0A 0A 0A 0A 0A 0B 80 00 15 81 "
	"81 00 C4 89 00 C4 83 00 0D 80 99 98 96 96 96 96 "
	"99 80 82 83 83 83 81 80 40 FF 18 81 81 04 E6 F9 "
	"10 21 02 81 04 E8 E5 EB 4D DA 83 00 0D CE D3 D4 "
	"D3 D3 D3 D5 D2 CE CC CD CD CD CD 80 00 A1 81 91 "
	"00 0D 07 03 04 02 02 02 03 03 07 07 08 08 08 07 "
	"80 00 09 81 81 00 28 40 00 A4 02 24 24 66 81 04 "
	"08 FA FA FA 28 83 00 82 02 FF FF FF 83 02 01 01 "
	"01 84 91 00 80 06 07 08 08 08 08 0A 07 80 03 FE "
	"FF FF FF 81 00 08 81 82 02 EE EE EE 8B 6D 00")

# Shared coordinates in the Skia font, as printed in Apple's TrueType spec.
SKIA_SHARED_COORDS = deHexStr(
	"40 00 00 00 C0 00 00 00 00 00 40 00 00 00 C0 00 "
	"C0 00 C0 00 40 00 C0 00 40 00 40 00 C0 00 40 00")


class GVARTableTest(unittest.TestCase):
	def test_compileOffsets_shortFormat(self):
		self.assertEqual((deHexStr("00 00 00 02 FF C0"), 0),
				 table__g_v_a_r.compileOffsets_([0, 4, 0x1ff80]))

	def test_compileOffsets_longFormat(self):
		self.assertEqual((deHexStr("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
				 table__g_v_a_r.compileOffsets_([0, 4, 0xCAFEBEEF]))

	def test_decompileOffsets_shortFormat(self):
		decompileOffsets = table__g_v_a_r.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual([2*0x0011, 2*0x2233, 2*0x4455, 2*0x6677, 2*0x8899, 2*0xaabb],
				 list(decompileOffsets(data, tableFormat=0, glyphCount=5)))

	def test_decompileOffsets_longFormat(self):
		decompileOffsets = table__g_v_a_r.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual([0x00112233, 0x44556677, 0x8899aabb],
				 list(decompileOffsets(data, tableFormat=1, glyphCount=2)))

	def test_compileGlyph_noVariations(self):
		table = table__g_v_a_r()
		table.variations = {}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_emptyVariations(self):
		table = table__g_v_a_r()
		table.variations = {"glyphname": []}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_onlyRedundantVariations(self):
		table = table__g_v_a_r()
		axes = {"wght": (0.3, 0.4, 0.5), "opsz": (0.7, 0.8, 0.9)}
		table.variations = {"glyphname": [
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4)
		]}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_roundTrip(self):
		table = table__g_v_a_r()
		axisTags = ["wght", "wdth"]
		numPointsInGlyph = 4
		glyphCoords = [(1,1), (2,2), (3,3), (4,4)]
		gvar1 = TupleVariation({"wght": (0.5, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		gvar2 = TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		table.variations = {"oslash": [gvar1, gvar2]}
		data = table.compileGlyph_("oslash", numPointsInGlyph, axisTags, {})
		self.assertEqual([gvar1, gvar2], table.decompileGlyph_(numPointsInGlyph, {}, axisTags, data))

	def test_compileSharedCoords(self):
		table = table__g_v_a_r()
		table.variations = {}
		deltas = [None] * 4
		table.variations["A"] = [
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.5, 0.7, 1.0)}, deltas)
		]
		table.variations["B"] = [
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.7, 1.0)}, deltas),
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.8, 1.0)}, deltas)
		]
		table.variations["C"] = [
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.7, 1.0)}, deltas),
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.8, 1.0)}, deltas),
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.9, 1.0)}, deltas)
		]
		# {"wght":1.0, "wdth":0.7} is shared 3 times; {"wght":1.0, "wdth":0.8} is shared twice.
		# Min and max values are not part of the shared coordinate pool and should get ignored.
		result = table.compileSharedCoords_(["wght", "wdth"])
		self.assertEqual(["40 00 2C CD", "40 00 33 33"], [hexencode(c) for c in result])

	def test_decompileSharedCoords_Skia(self):
		table = table__g_v_a_r()
		table.offsetToSharedTuples = 0
		table.sharedTupleCount = 8
		sharedCoords = table.decompileSharedCoords_(["wght", "wdth"], SKIA_SHARED_COORDS)
		self.assertEqual([
			{"wght": 1.0, "wdth": 0.0},
			{"wght": -1.0, "wdth": 0.0},
			{"wght": 0.0, "wdth": 1.0},
			{"wght": 0.0, "wdth": -1.0},
			{"wght": -1.0, "wdth": -1.0},
			{"wght": 1.0, "wdth": -1.0},
			{"wght": 1.0, "wdth": 1.0},
			{"wght": -1.0, "wdth": 1.0}
		], sharedCoords)

	def test_decompileSharedCoords_empty(self):
		table = table__g_v_a_r()
		table.offsetToSharedTuples = 0
		table.sharedTupleCount = 0
		self.assertEqual([], table.decompileSharedCoords_(["wght"], b""))

	def test_decompileGlyph_Skia_I(self):
		axes = ["wght", "wdth"]
		table = table__g_v_a_r()
		table.offsetToSharedTuples = 0
		table.sharedTupleCount = 8
		table.axisCount = len(axes)
		sharedCoords = table.decompileSharedCoords_(axes, SKIA_SHARED_COORDS)
		tuples = table.decompileGlyph_(18, sharedCoords, axes, SKIA_GVAR_I)
		self.assertEqual(8, len(tuples))
		self.assertEqual({"wght": (0.0, 1.0, 1.0)}, tuples[0].axes)
		self.assertEqual("257,0 -127,0 -128,58 -130,90 -130,62 -130,67 -130,32 -127,0 257,0 "
				 "259,14 260,64 260,21 260,69 258,124 0,0 130,0 0,0 0,0",
				 " ".join(["%d,%d" % c for c in tuples[0].coordinates]))

	def test_decompileGlyph_empty(self):
		table = table__g_v_a_r()
		self.assertEqual([], table.decompileGlyph_(numPointsInGlyph=5, sharedCoords=[], axisTags=[], data=b""))


if __name__ == "__main__":
	unittest.main()
