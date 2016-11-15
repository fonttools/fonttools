from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTLibError
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r, GlyphVariation
import random
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


class GlyphVariationTableTest(unittest.TestCase):
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
			GlyphVariation(axes, [None] * 4),
			GlyphVariation(axes, [None] * 4),
			GlyphVariation(axes, [None] * 4)
		]}
		self.assertEqual(b"", table.compileGlyph_("glyphname", 8, ["wght", "opsz"], {}))

	def test_compileGlyph_roundTrip(self):
		table = table__g_v_a_r()
		axisTags = ["wght", "wdth"]
		numPointsInGlyph = 4
		glyphCoords = [(1,1), (2,2), (3,3), (4,4)]
		gvar1 = GlyphVariation({"wght": (0.5, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		gvar2 = GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)}, glyphCoords)
		table.variations = {"oslash": [gvar1, gvar2]}
		data = table.compileGlyph_("oslash", numPointsInGlyph, axisTags, {})
		self.assertEqual([gvar1, gvar2], table.decompileGlyph_(numPointsInGlyph, {}, axisTags, data))

	def test_compileSharedCoords(self):
		table = table__g_v_a_r()
		table.variations = {}
		deltas = [None] * 4
		table.variations["A"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.5, 0.7, 1.0)}, deltas)
		]
		table.variations["B"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.7, 1.0)}, deltas),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.2, 0.8, 1.0)}, deltas)
		]
		table.variations["C"] = [
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.7, 1.0)}, deltas),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.8, 1.0)}, deltas),
			GlyphVariation({"wght": (1.0, 1.0, 1.0), "wdth": (0.3, 0.9, 1.0)}, deltas)
		]
		# {"wght":1.0, "wdth":0.7} is shared 3 times; {"wght":1.0, "wdth":0.8} is shared twice.
		# Min and max values are not part of the shared coordinate pool and should get ignored.
		result = table.compileSharedCoords_(["wght", "wdth"])
		self.assertEqual(["40 00 2C CD", "40 00 33 33"], [hexencode(c) for c in result])

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
		self.assertEqual([], table.decompileGlyph_(numPointsInGlyph=5, sharedCoords=[], axisTags=[], data=b""))

	def test_computeMinMaxCord(self):
		coord = {"wght": -0.3, "wdth": 0.7}
		minCoord, maxCoord = table__g_v_a_r.computeMinMaxCoord_(coord)
		self.assertEqual({"wght": -0.3, "wdth": 0.0}, minCoord)
		self.assertEqual({"wght": 0.0, "wdth": 0.7}, maxCoord)

class GlyphVariationTest(unittest.TestCase):
	def test_equal(self):
		gvar1 = GlyphVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		gvar2 = GlyphVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		self.assertEqual(gvar1, gvar2)

	def test_equal_differentAxes(self):
		gvar1 = GlyphVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		gvar2 = GlyphVariation({"wght":(0.7, 0.8, 0.9)}, [(0,0), (9,8), (7,6)])
		self.assertNotEqual(gvar1, gvar2)

	def test_equal_differentCoordinates(self):
		gvar1 = GlyphVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		gvar2 = GlyphVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8)])
		self.assertNotEqual(gvar1, gvar2)

	def test_hasImpact_someDeltasNotZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		gvar = GlyphVariation(axes, [(0,0), (9,8), (7,6)])
		self.assertTrue(gvar.hasImpact())

	def test_hasImpact_allDeltasZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		gvar = GlyphVariation(axes, [(0,0), (0,0), (0,0)])
		self.assertTrue(gvar.hasImpact())

	def test_hasImpact_allDeltasNone(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		gvar = GlyphVariation(axes, [None, None, None])
		self.assertFalse(gvar.hasImpact())

	def test_toXML(self):
		writer = XMLWriter(BytesIO())
		axes = {"wdth":(0.3, 0.4, 0.5), "wght":(0.0, 1.0, 1.0), "opsz":(-0.7, -0.7, 0.0)}
		g = GlyphVariation(axes, [(9,8), None, (7,6), (0,0), (-1,-2), None])
		g.toXML(writer, ["wdth", "wght", "opsz"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wdth" max="0.5" min="0.3" value="0.4"/>',
			  '<coord axis="wght" value="1.0"/>',
			  '<coord axis="opsz" value="-0.7"/>',
			  '<delta pt="0" x="9" y="8"/>',
			  '<delta pt="2" x="7" y="6"/>',
			  '<delta pt="3" x="0" y="0"/>',
			  '<delta pt="4" x="-1" y="-2"/>',
			'</tuple>'
		], GlyphVariationTest.xml_lines(writer))

	def test_toXML_allDeltasNone(self):
		writer = XMLWriter(BytesIO())
		axes = {"wght":(0.0, 1.0, 1.0)}
		g = GlyphVariation(axes, [None] * 5)
		g.toXML(writer, ["wght", "wdth"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wght" value="1.0"/>',
			  '<!-- no deltas -->',
			'</tuple>'
		], GlyphVariationTest.xml_lines(writer))

	def test_fromXML(self):
		g = GlyphVariation({}, [None] * 4)
		for name, attrs, content in parseXML(
				'<coord axis="wdth" min="0.3" value="0.4" max="0.5"/>'
				'<coord axis="wght" value="1.0"/>'
				'<coord axis="opsz" value="-0.5"/>'
				'<delta pt="1" x="33" y="44"/>'
				'<delta pt="2" x="-2" y="170"/>'):
			g.fromXML(name, attrs, content)
		self.assertEqual({
			"wdth":( 0.3,  0.4, 0.5),
			"wght":( 0.0,  1.0, 1.0),
			"opsz":(-0.5, -0.5, 0.0)
		}, g.axes)
		self.assertEqual([None, (33, 44), (-2, 170), None], g.coordinates)

	def test_compile_sharedCoords_nonIntermediate_sharedPoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedCoordIndices = { gvar.compileCoord(axisTags): 0x77 }
		tuple, data = gvar.compile(axisTags, sharedCoordIndices, sharedPoints={0,1,2})
		# len(data)=8; flags=None; tupleIndex=0x77
		# embeddedCoord=[]; intermediateCoord=[]
		self.assertEqual("00 08 00 77", hexencode(tuple))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_sharedCoords_intermediate_sharedPoints(self):
		gvar = GlyphVariation({"wght": (0.3, 0.5, 0.7), "wdth": (0.1, 0.8, 0.9)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedCoordIndices = { gvar.compileCoord(axisTags): 0x77 }
		tuple, data = gvar.compile(axisTags, sharedCoordIndices, sharedPoints={0,1,2})
		# len(data)=8; flags=INTERMEDIATE_TUPLE; tupleIndex=0x77
		# embeddedCoord=[]; intermediateCoord=[(0.3, 0.1), (0.7, 0.9)]
		self.assertEqual("00 08 40 77 13 33 06 66 2C CD 39 9A", hexencode(tuple))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_sharedCoords_nonIntermediate_privatePoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedCoordIndices = { gvar.compileCoord(axisTags): 0x77 }
		tuple, data = gvar.compile(axisTags, sharedCoordIndices, sharedPoints=None)
		# len(data)=13; flags=PRIVATE_POINT_NUMBERS; tupleIndex=0x77
		# embeddedCoord=[]; intermediateCoord=[]
		self.assertEqual("00 09 20 77", hexencode(tuple))
		self.assertEqual("00 "              # all points in glyph
				 "02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_sharedCoords_intermediate_privatePoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 1.0), "wdth": (0.0, 0.8, 1.0)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedCoordIndices = { gvar.compileCoord(axisTags): 0x77 }
		tuple, data = gvar.compile(axisTags, sharedCoordIndices, sharedPoints=None)
		# len(data)=13; flags=PRIVATE_POINT_NUMBERS; tupleIndex=0x77
		# embeddedCoord=[]; intermediateCoord=[(0.0, 0.0), (1.0, 1.0)]
		self.assertEqual("00 09 60 77 00 00 00 00 40 00 40 00", hexencode(tuple))
		self.assertEqual("00 "              # all points in glyph
				 "02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_embeddedCoords_nonIntermediate_sharedPoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		tuple, data = gvar.compile(axisTags, sharedCoordIndices={}, sharedPoints={0,1,2})
		# len(data)=8; flags=EMBEDDED_TUPLE_COORD
		# embeddedCoord=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 08 80 00 20 00 33 33", hexencode(tuple))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_embeddedCoords_intermediate_sharedPoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 1.0), "wdth": (0.0, 0.8, 0.8)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		tuple, data = gvar.compile(axisTags, sharedCoordIndices={}, sharedPoints={0,1,2})
		# len(data)=8; flags=EMBEDDED_TUPLE_COORD
		# embeddedCoord=[(0.5, 0.8)]; intermediateCoord=[(0.0, 0.0), (1.0, 0.8)]
		self.assertEqual("00 08 C0 00 20 00 33 33 00 00 00 00 40 00 33 33", hexencode(tuple))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_embeddedCoords_nonIntermediate_privatePoints(self):
		gvar = GlyphVariation({"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		tuple, data = gvar.compile(axisTags, sharedCoordIndices={}, sharedPoints=None)
		# len(data)=13; flags=PRIVATE_POINT_NUMBERS|EMBEDDED_TUPLE_COORD
		# embeddedCoord=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 09 A0 00 20 00 33 33", hexencode(tuple))
		self.assertEqual("00 "              # all points in glyph
				 "02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compile_embeddedCoords_intermediate_privatePoints(self):
		gvar = GlyphVariation({"wght": (0.4, 0.5, 0.6), "wdth": (0.7, 0.8, 0.9)},
				      [(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		tuple, data = gvar.compile(axisTags, sharedCoordIndices={}, sharedPoints=None)
		# len(data)=13; flags=PRIVATE_POINT_NUMBERS|INTERMEDIATE_TUPLE|EMBEDDED_TUPLE_COORD
		# embeddedCoord=(0.5, 0.8); intermediateCoord=[(0.4, 0.7), (0.6, 0.9)]
		self.assertEqual("00 09 E0 00 20 00 33 33 19 9A 2C CD 26 66 39 9A", hexencode(tuple))
		self.assertEqual("00 "              # all points in glyph
				 "02 07 08 09 "     # deltaX: [7, 8, 9]
				 "02 04 05 06",     # deltaY: [4, 5, 6]
				 hexencode(data))

	def test_compileCoord(self):
		gvar = GlyphVariation({"wght": (-1.0, -1.0, -1.0), "wdth": (0.4, 0.5, 0.6)}, [None] * 4)
		self.assertEqual("C0 00 20 00", hexencode(gvar.compileCoord(["wght", "wdth"])))
		self.assertEqual("20 00 C0 00", hexencode(gvar.compileCoord(["wdth", "wght"])))
		self.assertEqual("C0 00", hexencode(gvar.compileCoord(["wght"])))

	def test_compileIntermediateCoord(self):
		gvar = GlyphVariation({"wght": (-1.0, -1.0, 0.0), "wdth": (0.4, 0.5, 0.6)}, [None] * 4)
		self.assertEqual("C0 00 19 9A 00 00 26 66", hexencode(gvar.compileIntermediateCoord(["wght", "wdth"])))
		self.assertEqual("19 9A C0 00 26 66 00 00", hexencode(gvar.compileIntermediateCoord(["wdth", "wght"])))
		self.assertEqual(None, gvar.compileIntermediateCoord(["wght"]))
		self.assertEqual("19 9A 26 66", hexencode(gvar.compileIntermediateCoord(["wdth"])))

	def test_decompileCoord(self):
		decompileCoord = GlyphVariation.decompileCoord_
		data = deHexStr("DE AD C0 00 20 00 DE AD")
		self.assertEqual(({"wght": -1.0, "wdth": 0.5}, 6), decompileCoord(["wght", "wdth"], data, 2))

	def test_decompileCoord_roundTrip(self):
		# Make sure we are not affected by https://github.com/behdad/fonttools/issues/286
		data = deHexStr("7F B9 80 35")
		values, _ = GlyphVariation.decompileCoord_(["wght", "wdth"], data, 0)
		axisValues = {axis:(val, val, val) for axis, val in  values.items()}
		gvar = GlyphVariation(axisValues, [None] * 4)
		self.assertEqual("7F B9 80 35", hexencode(gvar.compileCoord(["wght", "wdth"])))

	def test_decompileCoords(self):
		decompileCoords = GlyphVariation.decompileCoords_
		axes = ["wght", "wdth", "opsz"]
		coords = [
			{"wght":  1.0, "wdth": 0.0, "opsz": 0.5},
			{"wght": -1.0, "wdth": 0.0, "opsz": 0.25},
			{"wght":  0.0, "wdth": -1.0, "opsz": 1.0}
		]
		data = deHexStr("DE AD 40 00 00 00 20 00 C0 00 00 00 10 00 00 00 C0 00 40 00")
		self.assertEqual((coords, 20), decompileCoords(axes, numCoords=3, data=data, offset=2))

	def test_compilePoints(self):
		compilePoints = lambda p: GlyphVariation.compilePoints(set(p), numPointsInGlyph=999)
		self.assertEqual("00", hexencode(compilePoints(range(999))))  # all points in glyph
		self.assertEqual("01 00 07", hexencode(compilePoints([7])))
		self.assertEqual("01 80 FF FF", hexencode(compilePoints([65535])))
		self.assertEqual("02 01 09 06", hexencode(compilePoints([9, 15])))
		self.assertEqual("06 05 07 01 F7 02 01 F2", hexencode(compilePoints([7, 8, 255, 257, 258, 500])))
		self.assertEqual("03 01 07 01 80 01 EC", hexencode(compilePoints([7, 8, 500])))
		self.assertEqual("04 01 07 01 81 BE E7 0C 0F", hexencode(compilePoints([7, 8, 0xBEEF, 0xCAFE])))
		self.maxDiff = None
		self.assertEqual("81 2C" +  # 300 points (0x12c) in total
				 " 7F 00" + (127 * " 01") +  # first run, contains 128 points: [0 .. 127]
				 " 7F" + (128 * " 01") +  # second run, contains 128 points: [128 .. 255]
				 " 2B" + (44 * " 01"),  # third run, contains 44 points: [256 .. 299]
				 hexencode(compilePoints(range(300))))
		self.assertEqual("81 8F" +  # 399 points (0x18f) in total
				 " 7F 00" + (127 * " 01") +  # first run, contains 128 points: [0 .. 127]
				 " 7F" + (128 * " 01") +  # second run, contains 128 points: [128 .. 255]
				 " 7F" + (128 * " 01") +  # third run, contains 128 points: [256 .. 383]
				 " 0E" + (15 * " 01"),  # fourth run, contains 15 points: [384 .. 398]
				 hexencode(compilePoints(range(399))))

	def test_decompilePoints(self):
		numPointsInGlyph = 65536
		allPoints = list(range(numPointsInGlyph))
		def decompilePoints(data, offset):
			points, offset = GlyphVariation.decompilePoints_(numPointsInGlyph, deHexStr(data), offset)
			# Conversion to list needed for Python 3.
			return (list(points), offset)
		# all points in glyph
		self.assertEqual((allPoints, 1), decompilePoints("00", 0))
		# all points in glyph (in overly verbose encoding, not explicitly prohibited by spec)
		self.assertEqual((allPoints, 2), decompilePoints("80 00", 0))
		# 2 points; first run: [9, 9+6]
		self.assertEqual(([9, 15], 4), decompilePoints("02 01 09 06", 0))
		# 2 points; first run: [0xBEEF, 0xCAFE]. (0x0C0F = 0xCAFE - 0xBEEF)
		self.assertEqual(([0xBEEF, 0xCAFE], 6), decompilePoints("02 81 BE EF 0C 0F", 0))
		# 1 point; first run: [7]
		self.assertEqual(([7], 3), decompilePoints("01 00 07", 0))
		# 1 point; first run: [7] in overly verbose encoding
		self.assertEqual(([7], 4), decompilePoints("01 80 00 07", 0))
		# 1 point; first run: [65535]; requires words to be treated as unsigned numbers
		self.assertEqual(([65535], 4), decompilePoints("01 80 FF FF", 0))
		# 4 points; first run: [7, 8]; second run: [255, 257]. 257 is stored in delta-encoded bytes (0xFF + 2).
		self.assertEqual(([7, 8, 263, 265], 7), decompilePoints("04 01 07 01 01 FF 02", 0))
		# combination of all encodings, preceded and followed by 4 bytes of unused data
		data = "DE AD DE AD 04 01 07 01 81 BE E7 0C 0F DE AD DE AD"
		self.assertEqual(([7, 8, 0xBEEF, 0xCAFE], 13), decompilePoints(data, 4))
		self.assertSetEqual(set(range(300)), set(decompilePoints(
		    "81 2C" +  # 300 points (0x12c) in total
		    " 7F 00" + (127 * " 01") +  # first run, contains 128 points: [0 .. 127]
		    " 7F" + (128 * " 01") +  # second run, contains 128 points: [128 .. 255]
		    " AB" + (44 * " 00 01"),  # third run, contains 44 points: [256 .. 299]
		    0)[0]))
		self.assertSetEqual(set(range(399)), set(decompilePoints(
		    "81 8F" +  # 399 points (0x18f) in total
		    " 7F 00" + (127 * " 01") +  # first run, contains 128 points: [0 .. 127]
		    " 7F" + (128 * " 01") +  # second run, contains 128 points: [128 .. 255]
		    " FF" + (128 * " 00 01") + # third run, contains 128 points: [256 .. 383]
		    " 8E" + (15 * " 00 01"),  # fourth run, contains 15 points: [384 .. 398]
		    0)[0]))

	def test_decompilePoints_shouldAcceptBadPointNumbers(self):
		decompilePoints = GlyphVariation.decompilePoints_
		# 2 points; first run: [3, 9].
		numPointsInGlyph = 8
		decompilePoints(numPointsInGlyph, deHexStr("02 01 03 06"), 0)

	def test_decompilePoints_roundTrip(self):
		numPointsInGlyph = 500  # greater than 255, so we also exercise code path for 16-bit encoding
		compile = lambda points: GlyphVariation.compilePoints(points, numPointsInGlyph)
		decompile = lambda data: set(GlyphVariation.decompilePoints_(numPointsInGlyph, data, 0)[0])
		for i in range(50):
			points = set(random.sample(range(numPointsInGlyph), 30))
			self.assertSetEqual(points, decompile(compile(points)),
					    "failed round-trip decompile/compilePoints; points=%s" % points)
		allPoints = set(range(numPointsInGlyph))
		self.assertSetEqual(allPoints, decompile(compile(allPoints)))

	def test_compileDeltas(self):
		gvar = GlyphVariation({}, [(0,0), (1, 0), (2, 0), (3, 3)])
		points = {1, 2}
		# deltaX for points: [1, 2]; deltaY for points: [0, 0]
		self.assertEqual("01 01 02 81", hexencode(gvar.compileDeltas(points)))

	def test_compileDeltaValues(self):
		compileDeltaValues = lambda values: hexencode(GlyphVariation.compileDeltaValues_(values))
		# zeroes
		self.assertEqual("80", compileDeltaValues([0]))
		self.assertEqual("BF", compileDeltaValues([0] * 64))
		self.assertEqual("BF 80", compileDeltaValues([0] * 65))
		self.assertEqual("BF A3", compileDeltaValues([0] * 100))
		self.assertEqual("BF BF BF BF", compileDeltaValues([0] * 256))
		# bytes
		self.assertEqual("00 01", compileDeltaValues([1]))
		self.assertEqual("06 01 02 03 7F 80 FF FE", compileDeltaValues([1, 2, 3, 127, -128, -1, -2]))
		self.assertEqual("3F" + (64 * " 7F"), compileDeltaValues([127] * 64))
		self.assertEqual("3F" + (64 * " 7F") + " 00 7F", compileDeltaValues([127] * 65))
		# words
		self.assertEqual("40 66 66", compileDeltaValues([0x6666]))
		self.assertEqual("43 66 66 7F FF FF FF 80 00", compileDeltaValues([0x6666, 32767, -1, -32768]))
		self.assertEqual("7F" + (64 * " 11 22"), compileDeltaValues([0x1122] * 64))
		self.assertEqual("7F" + (64 * " 11 22") + " 40 11 22", compileDeltaValues([0x1122] * 65))
		# bytes, zeroes, bytes: a single zero is more compact when encoded as part of the bytes run
		self.assertEqual("04 7F 7F 00 7F 7F", compileDeltaValues([127, 127, 0, 127, 127]))
		self.assertEqual("01 7F 7F 81 01 7F 7F", compileDeltaValues([127, 127, 0, 0, 127, 127]))
		self.assertEqual("01 7F 7F 82 01 7F 7F", compileDeltaValues([127, 127, 0, 0, 0, 127, 127]))
		self.assertEqual("01 7F 7F 83 01 7F 7F", compileDeltaValues([127, 127, 0, 0, 0, 0, 127, 127]))
		# bytes, zeroes
		self.assertEqual("01 01 00", compileDeltaValues([1, 0]))
		self.assertEqual("00 01 81", compileDeltaValues([1, 0, 0]))
		# words, bytes, words: a single byte is more compact when encoded as part of the words run
		self.assertEqual("42 66 66 00 02 77 77", compileDeltaValues([0x6666, 2, 0x7777]))
		self.assertEqual("40 66 66 01 02 02 40 77 77", compileDeltaValues([0x6666, 2, 2, 0x7777]))
		# words, zeroes, words
		self.assertEqual("40 66 66 80 40 77 77", compileDeltaValues([0x6666, 0, 0x7777]))
		self.assertEqual("40 66 66 81 40 77 77", compileDeltaValues([0x6666, 0, 0, 0x7777]))
		self.assertEqual("40 66 66 82 40 77 77", compileDeltaValues([0x6666, 0, 0, 0, 0x7777]))
		# words, zeroes, bytes
		self.assertEqual("40 66 66 80 02 01 02 03", compileDeltaValues([0x6666, 0, 1, 2, 3]))
		self.assertEqual("40 66 66 81 02 01 02 03", compileDeltaValues([0x6666, 0, 0, 1, 2, 3]))
		self.assertEqual("40 66 66 82 02 01 02 03", compileDeltaValues([0x6666, 0, 0, 0, 1, 2, 3]))
		# words, zeroes
		self.assertEqual("40 66 66 80", compileDeltaValues([0x6666, 0]))
		self.assertEqual("40 66 66 81", compileDeltaValues([0x6666, 0, 0]))

	def test_decompileDeltas(self):
		decompileDeltas = GlyphVariation.decompileDeltas_
		# 83 = zero values (0x80), count = 4 (1 + 0x83 & 0x3F)
		self.assertEqual(([0, 0, 0, 0], 1), decompileDeltas(4, deHexStr("83"), 0))
		# 41 01 02 FF FF = signed 16-bit values (0x40), count = 2 (1 + 0x41 & 0x3F)
		self.assertEqual(([258, -1], 5), decompileDeltas(2, deHexStr("41 01 02 FF FF"), 0))
		# 01 81 07 = signed 8-bit values, count = 2 (1 + 0x01 & 0x3F)
		self.assertEqual(([-127, 7], 3), decompileDeltas(2, deHexStr("01 81 07"), 0))
		# combination of all three encodings, preceded and followed by 4 bytes of unused data
		data = deHexStr("DE AD BE EF 83 40 01 02 01 81 80 DE AD BE EF")
		self.assertEqual(([0, 0, 0, 0, 258, -127, -128], 11), decompileDeltas(7, data, 4))

	def test_decompileDeltas_roundTrip(self):
		numDeltas = 30
		compile = GlyphVariation.compileDeltaValues_
		decompile = lambda data: GlyphVariation.decompileDeltas_(numDeltas, data, 0)[0]
		for i in range(50):
			deltas = random.sample(range(-128, 127), 10)
			deltas.extend(random.sample(range(-32768, 32767), 10))
			deltas.extend([0] * 10)
			random.shuffle(deltas)
			self.assertListEqual(deltas, decompile(compile(deltas)))

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
