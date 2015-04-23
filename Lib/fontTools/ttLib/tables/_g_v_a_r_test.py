from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r, GlyphVariation


def hexdecode(s):
	return bytesjoin([c.decode("hex") for c in s.split()])

# Glyph variation table of uppercase I in the Skia font, as printed in Apple's
# TrueType spec. The actual Skia font uses a different table for uppercase I.
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
SKIA_GVAR_I = hexdecode(
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
SKIA_SHARED_COORDS = hexdecode(
	"40 00 00 00 C0 00 00 00 00 00 40 00 00 00 C0 00 "
	"C0 00 C0 00 40 00 C0 00 40 00 40 00 C0 00 40 00")


class GlyphVariationTableTest(unittest.TestCase):
	def test_decompileOffsets_shortFormat(self):
		decompileOffsets = table__g_v_a_r.decompileOffsets_
		data = hexdecode("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual([2*0x0011, 2*0x2233, 2*0x4455, 2*0x6677, 2*0x8899, 2*0xaabb],
				 list(decompileOffsets(data, format=0, glyphCount=5)))

	def test_decompileOffsets_longFormat(self):
		decompileOffsets = table__g_v_a_r.decompileOffsets_
		data = hexdecode("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual([0x00112233, 0x44556677, 0x8899aabb],
				 list(decompileOffsets(data, format=1, glyphCount=2)))

	def test_compileOffsets_shortFormat(self):
		self.assertEqual((hexdecode("00 00 00 02 FF C0"), 0),
				 table__g_v_a_r.compileOffsets_([0, 4, 0x1ff80]))

	def test_compileOffsets_longFormat(self):
		self.assertEqual((hexdecode("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
				 table__g_v_a_r.compileOffsets_([0, 4, 0xCAFEBEEF]))

	def test_decompileSharedCoords(self):
		table = table__g_v_a_r()
		table.offsetToCoord = 4
		table.sharedCoordCount = 3
		data = b"XXXX" + hexdecode(
			"40 00 00 00 20 00 "
			"C0 00 00 00 10 00 "
			"00 00 C0 00 40 00")
		self.assertEqual([
			{"wght":  1.0, "wdth": 0.0, "opsz": 0.5},
			{"wght": -1.0, "wdth": 0.0, "opsz": 0.25},
			{"wght":  0.0, "wdth": -1.0, "opsz": 1.0}
		], table.decompileSharedCoords_(["wght", "wdth", "opsz"], data))

	def test_decompileSharedCoords_Skia(self):
		table = table__g_v_a_r()
		table.offsetToCoord = 0
		table.sharedCoordCount = 8
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
		table.offsetToCoord = 0
		table.sharedCoordCount = 0
		self.assertEqual([], table.decompileSharedCoords_(["wght"], b""))

	def test_decompileVariations_Skia_I(self):
		axes = ["wght", "wdth"]
		table = table__g_v_a_r()
		table.offsetToCoord = 0
		table.sharedCoordCount = 8
		table.axisCount = len(axes)
		sharedCoords = table.decompileSharedCoords_(axes, SKIA_SHARED_COORDS)
		self.assertEqual([], table.decompileVariations_(99, sharedCoords, axes, SKIA_GVAR_I))

	def test_decompileVariations_empty(self):
		table = table__g_v_a_r()
		self.assertEqual([], table.decompileVariations_(numPoints=5, sharedCoords=[], axisTags=[], data=b""))

	def test_getTupleSize(self):
		getTupleSize = table__g_v_a_r.getTupleSize_
		axisCount = 3
		self.assertEqual(4 + axisCount * 2, getTupleSize(0x8042, axisCount))
		self.assertEqual(4 + axisCount * 4, getTupleSize(0x4077, axisCount))
		self.assertEqual(4, getTupleSize(0x2077, axisCount))
		self.assertEqual(4, getTupleSize(11, axisCount))

	def test_decompileDeltas(self):
		decompileDeltas = table__g_v_a_r.decompileDeltas_
		# 83 = zero values (0x80), count = 4 (1 + 0x83 & 0x3F)
		self.assertEqual(([0, 0, 0, 0], 1), decompileDeltas(4, hexdecode("83")))
		# 41 01 02 FF FF = signed 16-bit values (0x40), count = 2 (1 + 0x41 & 0x3F)
		self.assertEqual(([258, -1], 5), decompileDeltas(2, hexdecode("41 01 02 FF FF")))
		# 01 81 07 = signed 8-bit values, count = 2 (1 + 0x01 & 0x3F)
		self.assertEqual(([-127, 7], 3), decompileDeltas(2, hexdecode("01 81 07")))
		# combination of all three encodings, followed by unused data in buffer
		data = hexdecode("83 40 01 02 01 81 80 DE AD BE EF")
		self.assertEqual(([0, 0, 0, 0, 258, -127, -128], 7), decompileDeltas(7, data))


if __name__ == "__main__":
	unittest.main()
