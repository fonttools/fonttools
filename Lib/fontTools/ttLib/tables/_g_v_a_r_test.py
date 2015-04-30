from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
from fontTools import ttLib
import unittest
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r, GlyphVariation

def hexdecode(s):
	return bytesjoin([c.decode("hex") for c in s.split()])

def hexencode(s):
	return ' '.join([c.encode("hex").upper() for c in s])

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
	def test_compileOffsets_shortFormat(self):
		self.assertEqual((hexdecode("00 00 00 02 FF C0"), 0),
				 table__g_v_a_r.compileOffsets_([0, 4, 0x1ff80]))

	def test_compileOffsets_longFormat(self):
		self.assertEqual((hexdecode("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
				 table__g_v_a_r.compileOffsets_([0, 4, 0xCAFEBEEF]))

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

	def test_compileGlyph_noVariations(self):
		table = table__g_v_a_r()
		table.variations = {}
		self.assertEqual(b"", table.compileGlyph_("glyphname", ["wght", "opsz"], {}))

	def test_compileGlyph_emptyVariations(self):
		table = table__g_v_a_r()
		table.variations = {"glyphname": []}
		self.assertEqual(b"", table.compileGlyph_("glyphname", ["wght", "opsz"], {}))

	def test_compileGlyph_onlyRedundantVariations(self):
		table = table__g_v_a_r()
		axes = {"wght": (0.3, 0.4, 0.5), "opsz": (0.7, 0.8, 0.9)}
		table.variations = {"glyphname": [
			GlyphVariation(axes, GlyphCoordinates.zeros(4)),
			GlyphVariation(axes, GlyphCoordinates.zeros(4)),
			GlyphVariation(axes, GlyphCoordinates.zeros(4))
		]}
		self.assertEqual(b"", table.compileGlyph_("glyphname", ["wght", "opsz"], {}))

	def test_compileSharedCoords(self):
		class FakeFont:
			def getGlyphOrder(self):
				return ["A", "B", "C"]
		font = FakeFont()
		table = table__g_v_a_r()
		table.variations = {}
		table.variations["A"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.5, 0.7, 1.0)}, GlyphCoordinates.zeros(4))
		]
		table.variations["B"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.7, 1.0)}, GlyphCoordinates.zeros(4)),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.8, 1.0)}, GlyphCoordinates.zeros(4))
		]
		table.variations["C"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.7, 1.0)}, GlyphCoordinates.zeros(4)),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.8, 1.0)}, GlyphCoordinates.zeros(4)),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.9, 1.0)}, GlyphCoordinates.zeros(4))
		]
		# {"wght":1.0, "wdth":0.7} is shared 3 times; {"wght":1.0, "wdth":0.8} is shared twice.
		# Min and max values are not part of the shared coordinate pool and should get ignored.
		result = table.compileSharedCoords_(font, ["wght", "wdth"])
		self.assertEquals(["40 00 2C CD", "40 00 33 33"], [hexencode(c) for c in result])

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

	def test_decompileGlyph_Skia_I(self):
		axes = ["wght", "wdth"]
		table = table__g_v_a_r()
		table.offsetToCoord = 0
		table.sharedCoordCount = 8
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
		self.assertEqual([], table.decompileGlyph_(numPoints=5, sharedCoords=[], axisTags=[], data=b""))

	def test_computeMinMaxCord(self):
		coord = {"wght": -0.3, "wdth": 0.7}
		minCoord, maxCoord = table__g_v_a_r.computeMinMaxCoord_(coord)
		self.assertEqual({"wght": -0.3, "wdth": 0.0}, minCoord)
		self.assertEqual({"wght": 0.0, "wdth": 0.7}, maxCoord)

class GlyphVariationTest(unittest.TestCase):
	def test_hasImpact_someDeltasNotZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		gvar = GlyphVariation(axes, GlyphCoordinates([(0,0), (9,8), (7,6)]))
		self.assertTrue(gvar.hasImpact())

	def test_hasImpact_allDeltasZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		gvar = GlyphVariation(axes, GlyphCoordinates([(0,0), (0,0), (0,0)]))
		self.assertFalse(gvar.hasImpact())

	def test_toXML(self):
		writer = XMLWriter(StringIO())
		axes = {"wdth":(0.3, 0.4, 0.5), "wght":(0.0, 1.0, 1.0), "opsz":(-0.7, -0.7, 0.0)}
		g = GlyphVariation(axes, GlyphCoordinates([(9,8), (7,6), (0,0), (-1,-2)]))
		g.toXML(writer, ["wdth", "wght", "opsz"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wdth" max="0.5" min="0.3" value="0.4"/>',
			  '<coord axis="wght" value="1.0"/>',
			  '<coord axis="opsz" value="-0.7"/>',
			  '<delta pt="0" x="9" y="8"/>',
			  '<delta pt="1" x="7" y="6"/>',
			  '<delta pt="3" x="-1" y="-2"/>',
			'</tuple>'
		], GlyphVariationTest.xml_lines(writer))

	def test_toXML_allDeltasZero(self):
		writer = XMLWriter(StringIO())
		axes = {"wght":(0.0, 1.0, 1.0)}
		g = GlyphVariation(axes, GlyphCoordinates.zeros(5))
		g.toXML(writer, ["wght", "wdth"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wght" value="1.0"/>',
			  '<!-- all deltas are (0,0) -->',
			'</tuple>'
		], GlyphVariationTest.xml_lines(writer))

	def test_fromXML(self):
		g = GlyphVariation({}, GlyphCoordinates.zeros(4))
		g.fromXML("coord", {"axis":"wdth", "min":"0.3", "value":"0.4", "max":"0.5"}, [])
		g.fromXML("coord", {"axis":"wght", "value":"1.0"}, [])
		g.fromXML("coord", {"axis":"opsz", "value":"-0.5"}, [])
		g.fromXML("delta", {"pt":"1", "x":"33", "y":"44"}, [])
		g.fromXML("delta", {"pt":"2", "x":"-2", "y":"170"}, [])
		self.assertEqual({
			"wdth":( 0.3,  0.4, 0.5),
			"wght":( 0.0,  1.0, 1.0),
			"opsz":(-0.5, -0.5, 0.0)
		}, g.axes)
		self.assertEqual("0,0 33,44 -2,170 0,0", " ".join(["%d,%d" % c for c in g.coordinates]))

	def test_compileCoord(self):
		gvar = GlyphVariation({"wght": (-1.0, -1.0, -1.0), "wdth": (0.4, 0.5, 0.6)}, GlyphCoordinates.zeros(4))
		self.assertEqual("C0 00 20 00", hexencode(gvar.compileCoord(["wght", "wdth"])))
		self.assertEqual("20 00 C0 00", hexencode(gvar.compileCoord(["wdth", "wght"])))
		self.assertEqual("C0 00", hexencode(gvar.compileCoord(["wght"])))

	def test_compileIntermediateCoord(self):
		gvar = GlyphVariation({"wght": (-1.0, -1.0, 0.0), "wdth": (0.4, 0.5, 0.6)}, GlyphCoordinates.zeros(4))
		self.assertEqual("C0 00 19 9A 00 00 26 66", hexencode(gvar.compileIntermediateCoord(["wght", "wdth"])))
		self.assertEqual("19 9A C0 00 26 66 00 00", hexencode(gvar.compileIntermediateCoord(["wdth", "wght"])))
		self.assertEqual(None, gvar.compileIntermediateCoord(["wght"]))
		self.assertEqual("19 9A 26 66", hexencode(gvar.compileIntermediateCoord(["wdth"])))

	def test_decompileCoord(self):
		decompileCoord = GlyphVariation.decompileCoord_
		data = hexdecode("DE AD C0 00 20 00 DE AD")
		self.assertEqual(({"wght": -1.0, "wdth": 0.5}, 6), decompileCoord(["wght", "wdth"], data, 2))

	def test_decompileCoords(self):
		decompileCoords = GlyphVariation.decompileCoords_
		axes = ["wght", "wdth", "opsz"]
		coords = [
			{"wght":  1.0, "wdth": 0.0, "opsz": 0.5},
			{"wght": -1.0, "wdth": 0.0, "opsz": 0.25},
			{"wght":  0.0, "wdth": -1.0, "opsz": 1.0}
		]
		data = hexdecode("DE AD 40 00 00 00 20 00 C0 00 00 00 10 00 00 00 C0 00 40 00")
		self.assertEqual((coords, 20), decompileCoords(axes, numCoords=3, data=data, offset=2))

	def test_compilePoints(self):
		compilePoints = GlyphVariation.compilePoints
		self.assertEquals("01 00 07", hexencode(compilePoints({7})))
		self.assertEquals("01 80 FF FF", hexencode(compilePoints({65535})))
		self.assertEquals("02 01 09 06", hexencode(compilePoints({9, 15})))
		self.assertEquals("06 05 07 01 F7 02 01 F2", hexencode(compilePoints({7, 8, 255, 257, 258, 500})))
		self.assertEquals("03 01 07 01 80 01 F4", hexencode(compilePoints({7, 8, 500})))
		self.assertEquals("04 01 07 01 81 BE EF 0C 0F", hexencode(compilePoints({7, 8, 0xBEEF, 0xCAFE})))
		self.assertEquals("81 2C" +  # 300 points (0x12c) in total
				  " 7F 00" + (127 * " 01") +  # first run, contains 128 points: [0 .. 127]
				  " 7F 80" + (127 * " 01") +  # second run, contains 128 points: [128 .. 511]
				  " AB 01 00" + (43 * " 00 01"),  # third run, contains 44 points: [512 .. 299]
				  hexencode(compilePoints(set(xrange(300)))))

	def test_decompilePoints(self):
		decompilePoints = GlyphVariation.decompilePoints_
		numPoints = 65536
		allPoints = range(numPoints)
		# all points in glyph
		self.assertEqual((allPoints, 1), decompilePoints(numPoints, hexdecode("00"), 0))
		# all points in glyph (in overly verbose encoding, not explicitly prohibited by spec)
		self.assertEqual((allPoints, 2), decompilePoints(numPoints, hexdecode("80 00"), 0))
		# 2 points; first run: [9, 9+6]
		self.assertEqual(([9, 15], 4), decompilePoints(numPoints, hexdecode("02 01 09 06"), 0))
		# 2 points; first run: [0xBEEF, 0xCAFE]. (0x0C0F = 0xCAFE - 0xBEEF)
		self.assertEqual(([0xBEEF, 0xCAFE], 6), decompilePoints(numPoints, hexdecode("02 81 BE EF 0C 0F"), 0))
		# 1 point; first run: [7]
		self.assertEqual(([7], 3), decompilePoints(numPoints, hexdecode("01 00 07"), 0))
		# 1 point; first run: [7] in overly verbose encoding
		self.assertEqual(([7], 4), decompilePoints(numPoints, hexdecode("01 80 00 07"), 0))
		# 1 point; first run: [65535]; requires words to be treated as unsigned numbers
		self.assertEqual(([65535], 4), decompilePoints(numPoints, hexdecode("01 80 FF FF"), 0))
		# 4 points; first run: [7, 8]; second run: [255, 257]. 257 is stored in delta-encoded bytes (0xFF + 2).
		self.assertEqual(([7, 8, 255, 257], 7), decompilePoints(numPoints, hexdecode("04 01 07 01 01 FF 02"), 0))
		# combination of all encodings, preceded and followed by 4 bytes of unused data
		data = hexdecode("DE AD DE AD 04 01 07 01 81 BE EF 0C 0F DE AD DE AD")
		self.assertEqual(([7, 8, 0xBEEF, 0xCAFE], 13), decompilePoints(numPoints, data, 4))

	def test_decompilePoints_shouldGuardAgainstBadPointNumbers(self):
		decompilePoints = GlyphVariation.decompilePoints_
		# 2 points; first run: [3, 9].
		numPoints = 8
		self.assertRaises(ttLib.TTLibError, decompilePoints, numPoints, hexdecode("02 01 03 06"), 0)

	def test_decompileDeltas(self):
		decompileDeltas = GlyphVariation.decompileDeltas_
		# 83 = zero values (0x80), count = 4 (1 + 0x83 & 0x3F)
		self.assertEqual(([0, 0, 0, 0], 1), decompileDeltas(4, hexdecode("83"), 0))
		# 41 01 02 FF FF = signed 16-bit values (0x40), count = 2 (1 + 0x41 & 0x3F)
		self.assertEqual(([258, -1], 5), decompileDeltas(2, hexdecode("41 01 02 FF FF"), 0))
		# 01 81 07 = signed 8-bit values, count = 2 (1 + 0x01 & 0x3F)
		self.assertEqual(([-127, 7], 3), decompileDeltas(2, hexdecode("01 81 07"), 0))
		# combination of all three encodings, preceded and followed by 4 bytes of unused data
		data = hexdecode("DE AD BE EF 83 40 01 02 01 81 80 DE AD BE EF")
		self.assertEqual(([0, 0, 0, 0, 258, -127, -128], 11), decompileDeltas(7, data, 4))

	def test_getTupleSize(self):
		getTupleSize = GlyphVariation.getTupleSize_
		numAxes = 3
		self.assertEqual(4 + numAxes * 2, getTupleSize(0x8042, numAxes))
		self.assertEqual(4 + numAxes * 4, getTupleSize(0x4077, numAxes))
		self.assertEqual(4, getTupleSize(0x2077, numAxes))
		self.assertEqual(4, getTupleSize(11, numAxes))

	@staticmethod
	def xml_lines(writer):
		content = writer.file.getvalue().decode("utf-8")
		return [line.strip() for line in content.splitlines()][1:]


if __name__ == "__main__":
	unittest.main()
