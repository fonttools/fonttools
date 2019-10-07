from fontTools.misc.py23 import *
from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib.tables.TupleVariation import \
	log, TupleVariation, compileSharedTuples, decompileSharedTuples, \
	compileTupleVariationStore, decompileTupleVariationStore, inferRegion_
import random
import unittest


def hexencode(s):
	h = hexStr(s).upper()
	return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])


AXES = {
	"wdth": (0.25, 0.375, 0.5),
	"wght": (0.0, 1.0, 1.0),
	"opsz": (-0.75, -0.75, 0.0)
}


# Shared tuples in the 'gvar' table of the Skia font, as printed
# in Apple's TrueType specification.
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
SKIA_GVAR_SHARED_TUPLES_DATA = deHexStr(
	"40 00 00 00 C0 00 00 00 00 00 40 00 00 00 C0 00 "
	"C0 00 C0 00 40 00 C0 00 40 00 40 00 C0 00 40 00")

SKIA_GVAR_SHARED_TUPLES = [
	{"wght": 1.0, "wdth": 0.0},
	{"wght": -1.0, "wdth": 0.0},
	{"wght": 0.0, "wdth": 1.0},
	{"wght": 0.0, "wdth": -1.0},
	{"wght": -1.0, "wdth": -1.0},
	{"wght": 1.0, "wdth": -1.0},
	{"wght": 1.0, "wdth": 1.0},
	{"wght": -1.0, "wdth": 1.0}
]


# Tuple Variation Store of uppercase I in the Skia font, as printed in Apple's
# TrueType spec. The actual Skia font uses a different table for uppercase I
# than what is printed in Apple's spec, but we still want to make sure that
# we can parse the data as it appears in the specification.
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
SKIA_GVAR_I_DATA = deHexStr(
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


class TupleVariationTest(unittest.TestCase):
	def __init__(self, methodName):
		unittest.TestCase.__init__(self, methodName)
		# Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
		# and fires deprecation warnings if a program uses the old name.
		if not hasattr(self, "assertRaisesRegex"):
			self.assertRaisesRegex = self.assertRaisesRegexp

	def test_equal(self):
		var1 = TupleVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		var2 = TupleVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		self.assertEqual(var1, var2)

	def test_equal_differentAxes(self):
		var1 = TupleVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		var2 = TupleVariation({"wght":(0.7, 0.8, 0.9)}, [(0,0), (9,8), (7,6)])
		self.assertNotEqual(var1, var2)

	def test_equal_differentCoordinates(self):
		var1 = TupleVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8), (7,6)])
		var2 = TupleVariation({"wght":(0.0, 1.0, 1.0)}, [(0,0), (9,8)])
		self.assertNotEqual(var1, var2)

	def test_hasImpact_someDeltasNotZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		var = TupleVariation(axes, [(0,0), (9,8), (7,6)])
		self.assertTrue(var.hasImpact())

	def test_hasImpact_allDeltasZero(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		var = TupleVariation(axes, [(0,0), (0,0), (0,0)])
		self.assertTrue(var.hasImpact())

	def test_hasImpact_allDeltasNone(self):
		axes = {"wght":(0.0, 1.0, 1.0)}
		var = TupleVariation(axes, [None, None, None])
		self.assertFalse(var.hasImpact())

	def test_toXML_badDeltaFormat(self):
		writer = XMLWriter(BytesIO())
		g = TupleVariation(AXES, ["String"])
		with CapturingLogHandler(log, "ERROR") as captor:
			g.toXML(writer, ["wdth"])
		self.assertIn("bad delta format", [r.msg for r in captor.records])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wdth" min="0.25" value="0.375" max="0.5"/>',
			  '<!-- bad delta #0 -->',
			'</tuple>',
		], TupleVariationTest.xml_lines(writer))

	def test_toXML_constants(self):
		writer = XMLWriter(BytesIO())
		g = TupleVariation(AXES, [42, None, 23, 0, -17, None])
		g.toXML(writer, ["wdth", "wght", "opsz"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wdth" min="0.25" value="0.375" max="0.5"/>',
			  '<coord axis="wght" value="1.0"/>',
			  '<coord axis="opsz" value="-0.75"/>',
			  '<delta cvt="0" value="42"/>',
			  '<delta cvt="2" value="23"/>',
			  '<delta cvt="3" value="0"/>',
			  '<delta cvt="4" value="-17"/>',
			'</tuple>'
		], TupleVariationTest.xml_lines(writer))

	def test_toXML_points(self):
		writer = XMLWriter(BytesIO())
		g = TupleVariation(AXES, [(9,8), None, (7,6), (0,0), (-1,-2), None])
		g.toXML(writer, ["wdth", "wght", "opsz"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wdth" min="0.25" value="0.375" max="0.5"/>',
			  '<coord axis="wght" value="1.0"/>',
			  '<coord axis="opsz" value="-0.75"/>',
			  '<delta pt="0" x="9" y="8"/>',
			  '<delta pt="2" x="7" y="6"/>',
			  '<delta pt="3" x="0" y="0"/>',
			  '<delta pt="4" x="-1" y="-2"/>',
			'</tuple>'
		], TupleVariationTest.xml_lines(writer))

	def test_toXML_allDeltasNone(self):
		writer = XMLWriter(BytesIO())
		axes = {"wght":(0.0, 1.0, 1.0)}
		g = TupleVariation(axes, [None] * 5)
		g.toXML(writer, ["wght", "wdth"])
		self.assertEqual([
			'<tuple>',
			  '<coord axis="wght" value="1.0"/>',
			  '<!-- no deltas -->',
			'</tuple>'
		], TupleVariationTest.xml_lines(writer))

	def test_toXML_axes_floats(self):
		writer = XMLWriter(BytesIO())
		axes = {
			"wght": (0.0, 0.2999878, 0.7000122),
			"wdth": (0.0, 0.4000244, 0.4000244),
		}
		g = TupleVariation(axes, [None] * 5)
		g.toXML(writer, ["wght", "wdth"])
		self.assertEqual(
			[
				'<coord axis="wght" min="0.0" value="0.3" max="0.7"/>',
				'<coord axis="wdth" value="0.4"/>',
			],
			TupleVariationTest.xml_lines(writer)[1:3]
		)

	def test_fromXML_badDeltaFormat(self):
		g = TupleVariation({}, [])
		with CapturingLogHandler(log, "WARNING") as captor:
			for name, attrs, content in parseXML('<delta a="1" b="2"/>'):
				g.fromXML(name, attrs, content)
		self.assertIn("bad delta format: a, b",
		              [r.msg for r in captor.records])

	def test_fromXML_constants(self):
		g = TupleVariation({}, [None] * 4)
		for name, attrs, content in parseXML(
				'<coord axis="wdth" min="0.25" value="0.375" max="0.5"/>'
				'<coord axis="wght" value="1.0"/>'
				'<coord axis="opsz" value="-0.75"/>'
				'<delta cvt="1" value="42"/>'
				'<delta cvt="2" value="-23"/>'):
			g.fromXML(name, attrs, content)
		self.assertEqual(AXES, g.axes)
		self.assertEqual([None, 42, -23, None], g.coordinates)

	def test_fromXML_points(self):
		g = TupleVariation({}, [None] * 4)
		for name, attrs, content in parseXML(
				'<coord axis="wdth" min="0.25" value="0.375" max="0.5"/>'
				'<coord axis="wght" value="1.0"/>'
				'<coord axis="opsz" value="-0.75"/>'
				'<delta pt="1" x="33" y="44"/>'
				'<delta pt="2" x="-2" y="170"/>'):
			g.fromXML(name, attrs, content)
		self.assertEqual(AXES, g.axes)
		self.assertEqual([None, (33, 44), (-2, 170), None], g.coordinates)

	def test_fromXML_axes_floats(self):
		g = TupleVariation({}, [None] * 4)
		for name, attrs, content in parseXML(
			'<coord axis="wght" min="0.0" value="0.3" max="0.7"/>'
			'<coord axis="wdth" value="0.4"/>'
		):
			g.fromXML(name, attrs, content)

		self.assertEqual(g.axes["wght"][0], 0)
		self.assertAlmostEqual(g.axes["wght"][1], 0.2999878)
		self.assertAlmostEqual(g.axes["wght"][2], 0.7000122)

		self.assertEqual(g.axes["wdth"][0], 0)
		self.assertAlmostEqual(g.axes["wdth"][1], 0.4000244)
		self.assertAlmostEqual(g.axes["wdth"][2], 0.4000244)

	def test_compile_sharedPeaks_nonIntermediate_sharedPoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedPeakIndices = { var.compileCoord(axisTags): 0x77 }
		tup, deltas, _ = var.compile(axisTags, sharedPeakIndices,
		                          sharedPoints={0,1,2})
		# len(deltas)=8; flags=None; tupleIndex=0x77
		# embeddedPeaks=[]; intermediateCoord=[]
		self.assertEqual("00 08 00 77", hexencode(tup))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
						 "02 04 05 06",     # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_sharedPeaks_intermediate_sharedPoints(self):
		var = TupleVariation(
			{"wght": (0.3, 0.5, 0.7), "wdth": (0.1, 0.8, 0.9)},
			[(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedPeakIndices = { var.compileCoord(axisTags): 0x77 }
		tup, deltas, _ = var.compile(axisTags, sharedPeakIndices,
		                          sharedPoints={0,1,2})
		# len(deltas)=8; flags=INTERMEDIATE_REGION; tupleIndex=0x77
		# embeddedPeak=[]; intermediateCoord=[(0.3, 0.1), (0.7, 0.9)]
		self.assertEqual("00 08 40 77 13 33 06 66 2C CD 39 9A", hexencode(tup))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
						 "02 04 05 06",     # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_sharedPeaks_nonIntermediate_privatePoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedPeakIndices = { var.compileCoord(axisTags): 0x77 }
		tup, deltas, _ = var.compile(axisTags, sharedPeakIndices,
		                          sharedPoints=None)
		# len(deltas)=9; flags=PRIVATE_POINT_NUMBERS; tupleIndex=0x77
		# embeddedPeak=[]; intermediateCoord=[]
		self.assertEqual("00 09 20 77", hexencode(tup))
		self.assertEqual("00 "              # all points in glyph
						 "02 07 08 09 "     # deltaX: [7, 8, 9]
						 "02 04 05 06",     # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_sharedPeaks_intermediate_privatePoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 1.0), "wdth": (0.0, 0.8, 1.0)},
			[(7,4), (8,5), (9,6)])
		axisTags = ["wght", "wdth"]
		sharedPeakIndices = { var.compileCoord(axisTags): 0x77 }
		tuple, deltas, _ = var.compile(axisTags,
		                            sharedPeakIndices, sharedPoints=None)
		# len(deltas)=9; flags=PRIVATE_POINT_NUMBERS; tupleIndex=0x77
		# embeddedPeak=[]; intermediateCoord=[(0.0, 0.0), (1.0, 1.0)]
		self.assertEqual("00 09 60 77 00 00 00 00 40 00 40 00",
		                 hexencode(tuple))
		self.assertEqual("00 "              # all points in glyph
						 "02 07 08 09 "     # deltaX: [7, 8, 9]
						 "02 04 05 06",     # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_embeddedPeak_nonIntermediate_sharedPoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[(7,4), (8,5), (9,6)])
		tup, deltas, _ = var.compile(axisTags=["wght", "wdth"],
		                          sharedCoordIndices={}, sharedPoints={0, 1, 2})
		# len(deltas)=8; flags=EMBEDDED_PEAK_TUPLE
		# embeddedPeak=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 08 80 00 20 00 33 33", hexencode(tup))
		self.assertEqual("02 07 08 09 "     # deltaX: [7, 8, 9]
						 "02 04 05 06",     # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_embeddedPeak_nonIntermediate_sharedConstants(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[3, 1, 4])
		tup, deltas, _ = var.compile(axisTags=["wght", "wdth"],
		                          sharedCoordIndices={}, sharedPoints={0, 1, 2})
		# len(deltas)=4; flags=EMBEDDED_PEAK_TUPLE
		# embeddedPeak=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 04 80 00 20 00 33 33", hexencode(tup))
		self.assertEqual("02 03 01 04",     # delta: [3, 1, 4]
						 hexencode(deltas))

	def test_compile_embeddedPeak_intermediate_sharedPoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 1.0), "wdth": (0.0, 0.8, 0.8)},
			[(7,4), (8,5), (9,6)])
		tup, deltas, _ = var.compile(axisTags=["wght", "wdth"],
		                          sharedCoordIndices={},
		                          sharedPoints={0, 1, 2})
		# len(deltas)=8; flags=EMBEDDED_PEAK_TUPLE
		# embeddedPeak=[(0.5, 0.8)]; intermediateCoord=[(0.0, 0.0), (1.0, 0.8)]
		self.assertEqual("00 08 C0 00 20 00 33 33 00 00 00 00 40 00 33 33",
		                hexencode(tup))
		self.assertEqual("02 07 08 09 "  # deltaX: [7, 8, 9]
						 "02 04 05 06",  # deltaY: [4, 5, 6]
						 hexencode(deltas))

	def test_compile_embeddedPeak_nonIntermediate_privatePoints(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[(7,4), (8,5), (9,6)])
		tup, deltas, _ = var.compile(
			axisTags=["wght", "wdth"], sharedCoordIndices={}, sharedPoints=None)
		# len(deltas)=9; flags=PRIVATE_POINT_NUMBERS|EMBEDDED_PEAK_TUPLE
		# embeddedPeak=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 09 A0 00 20 00 33 33", hexencode(tup))
		self.assertEqual("00 "           # all points in glyph
		                 "02 07 08 09 "  # deltaX: [7, 8, 9]
		                 "02 04 05 06",  # deltaY: [4, 5, 6]
		                 hexencode(deltas))

	def test_compile_embeddedPeak_nonIntermediate_privateConstants(self):
		var = TupleVariation(
			{"wght": (0.0, 0.5, 0.5), "wdth": (0.0, 0.8, 0.8)},
			[7, 8, 9])
		tup, deltas, _ = var.compile(
			axisTags=["wght", "wdth"], sharedCoordIndices={}, sharedPoints=None)
		# len(deltas)=5; flags=PRIVATE_POINT_NUMBERS|EMBEDDED_PEAK_TUPLE
		# embeddedPeak=[(0.5, 0.8)]; intermediateCoord=[]
		self.assertEqual("00 05 A0 00 20 00 33 33", hexencode(tup))
		self.assertEqual("00 "           # all points in glyph
		                 "02 07 08 09",  # delta: [7, 8, 9]
		                 hexencode(deltas))

	def test_compile_embeddedPeak_intermediate_privatePoints(self):
		var = TupleVariation(
			{"wght": (0.4, 0.5, 0.6), "wdth": (0.7, 0.8, 0.9)},
			[(7,4), (8,5), (9,6)])
		tup, deltas, _ = var.compile(
			axisTags = ["wght", "wdth"],
			sharedCoordIndices={}, sharedPoints=None)
		# len(deltas)=9;
		# flags=PRIVATE_POINT_NUMBERS|INTERMEDIATE_REGION|EMBEDDED_PEAK_TUPLE
		# embeddedPeak=(0.5, 0.8); intermediateCoord=[(0.4, 0.7), (0.6, 0.9)]
		self.assertEqual("00 09 E0 00 20 00 33 33 19 9A 2C CD 26 66 39 9A",
		                 hexencode(tup))
		self.assertEqual("00 "              # all points in glyph
		                 "02 07 08 09 "     # deltaX: [7, 8, 9]
		                 "02 04 05 06",     # deltaY: [4, 5, 6]
		                 hexencode(deltas))

	def test_compile_embeddedPeak_intermediate_privateConstants(self):
		var = TupleVariation(
			{"wght": (0.4, 0.5, 0.6), "wdth": (0.7, 0.8, 0.9)},
			[7, 8, 9])
		tup, deltas, _ = var.compile(
			axisTags = ["wght", "wdth"],
			sharedCoordIndices={}, sharedPoints=None)
		# len(deltas)=5;
		# flags=PRIVATE_POINT_NUMBERS|INTERMEDIATE_REGION|EMBEDDED_PEAK_TUPLE
		# embeddedPeak=(0.5, 0.8); intermediateCoord=[(0.4, 0.7), (0.6, 0.9)]
		self.assertEqual("00 05 E0 00 20 00 33 33 19 9A 2C CD 26 66 39 9A",
		                 hexencode(tup))
		self.assertEqual("00 "             # all points in glyph
		                 "02 07 08 09",    # delta: [7, 8, 9]
		                 hexencode(deltas))

	def test_compileCoord(self):
		var = TupleVariation({"wght": (-1.0, -1.0, -1.0), "wdth": (0.4, 0.5, 0.6)}, [None] * 4)
		self.assertEqual("C0 00 20 00", hexencode(var.compileCoord(["wght", "wdth"])))
		self.assertEqual("20 00 C0 00", hexencode(var.compileCoord(["wdth", "wght"])))
		self.assertEqual("C0 00", hexencode(var.compileCoord(["wght"])))

	def test_compileIntermediateCoord(self):
		var = TupleVariation({"wght": (-1.0, -1.0, 0.0), "wdth": (0.4, 0.5, 0.6)}, [None] * 4)
		self.assertEqual("C0 00 19 9A 00 00 26 66", hexencode(var.compileIntermediateCoord(["wght", "wdth"])))
		self.assertEqual("19 9A C0 00 26 66 00 00", hexencode(var.compileIntermediateCoord(["wdth", "wght"])))
		self.assertEqual(None, var.compileIntermediateCoord(["wght"]))
		self.assertEqual("19 9A 26 66", hexencode(var.compileIntermediateCoord(["wdth"])))

	def test_decompileCoord(self):
		decompileCoord = TupleVariation.decompileCoord_
		data = deHexStr("DE AD C0 00 20 00 DE AD")
		self.assertEqual(({"wght": -1.0, "wdth": 0.5}, 6), decompileCoord(["wght", "wdth"], data, 2))

	def test_decompileCoord_roundTrip(self):
		# Make sure we are not affected by https://github.com/fonttools/fonttools/issues/286
		data = deHexStr("7F B9 80 35")
		values, _ = TupleVariation.decompileCoord_(["wght", "wdth"], data, 0)
		axisValues = {axis:(val, val, val) for axis, val in  values.items()}
		var = TupleVariation(axisValues, [None] * 4)
		self.assertEqual("7F B9 80 35", hexencode(var.compileCoord(["wght", "wdth"])))

	def test_compilePoints(self):
		compilePoints = lambda p: TupleVariation.compilePoints(set(p), numPointsInGlyph=999)
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
			points, offset = TupleVariation.decompilePoints_(numPointsInGlyph, deHexStr(data), offset, "gvar")
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
		decompilePoints = TupleVariation.decompilePoints_
		# 2 points; first run: [3, 9].
		numPointsInGlyph = 8
		with CapturingLogHandler(log, "WARNING") as captor:
			decompilePoints(numPointsInGlyph,
			                deHexStr("02 01 03 06"), 0, "cvar")
		self.assertIn("point 9 out of range in 'cvar' table",
		              [r.msg for r in captor.records])

	def test_decompilePoints_roundTrip(self):
		numPointsInGlyph = 500  # greater than 255, so we also exercise code path for 16-bit encoding
		compile = lambda points: TupleVariation.compilePoints(points, numPointsInGlyph)
		decompile = lambda data: set(TupleVariation.decompilePoints_(numPointsInGlyph, data, 0, "gvar")[0])
		for i in range(50):
			points = set(random.sample(range(numPointsInGlyph), 30))
			self.assertSetEqual(points, decompile(compile(points)),
					    "failed round-trip decompile/compilePoints; points=%s" % points)
		allPoints = set(range(numPointsInGlyph))
		self.assertSetEqual(allPoints, decompile(compile(allPoints)))

	def test_compileDeltas_points(self):
		var = TupleVariation({}, [(0,0), (1, 0), (2, 0), None, (4, 0), (5, 0)])
		points = {1, 2, 3, 4}
		# deltaX for points: [1, 2, 4]; deltaY for points: [0, 0, 0]
		self.assertEqual("02 01 02 04 82", hexencode(var.compileDeltas(points)))

	def test_compileDeltas_constants(self):
		var = TupleVariation({}, [0, 1, 2, None, 4, 5])
		cvts = {1, 2, 3, 4}
		# delta for cvts: [1, 2, 4]
		self.assertEqual("02 01 02 04", hexencode(var.compileDeltas(cvts)))

	def test_compileDeltaValues(self):
		compileDeltaValues = lambda values: hexencode(TupleVariation.compileDeltaValues_(values))
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
		# bytes or words from floats
		self.assertEqual("00 01", compileDeltaValues([1.1]))
		self.assertEqual("00 02", compileDeltaValues([1.9]))
		self.assertEqual("40 66 66", compileDeltaValues([0x6666 + 0.1]))
		self.assertEqual("40 66 66", compileDeltaValues([0x6665 + 0.9]))

	def test_decompileDeltas(self):
		decompileDeltas = TupleVariation.decompileDeltas_
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
		compile = TupleVariation.compileDeltaValues_
		decompile = lambda data: TupleVariation.decompileDeltas_(numDeltas, data, 0)[0]
		for i in range(50):
			deltas = random.sample(range(-128, 127), 10)
			deltas.extend(random.sample(range(-32768, 32767), 10))
			deltas.extend([0] * 10)
			random.shuffle(deltas)
			self.assertListEqual(deltas, decompile(compile(deltas)))

	def test_compileSharedTuples(self):
		# Below, the peak coordinate {"wght": 1.0, "wdth": 0.7} appears
		# three times; {"wght": 1.0, "wdth": 0.8} appears twice.
		# Because the start and end of variation ranges is not encoded
		# into the shared pool, they should get ignored.
		deltas = [None] * 4
		variations = [
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.5, 0.7, 1.0)
			}, deltas),
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.2, 0.7, 1.0)
			}, deltas),
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.2, 0.8, 1.0)
			}, deltas),
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.3, 0.7, 1.0)
			}, deltas),
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.3, 0.8, 1.0)
			}, deltas),
			TupleVariation({
				"wght": (1.0, 1.0, 1.0),
				"wdth": (0.3, 0.9, 1.0)
            }, deltas)
		]
		result = compileSharedTuples(["wght", "wdth"], variations)
		self.assertEqual([hexencode(c) for c in result],
		                 ["40 00 2C CD", "40 00 33 33"])

	def test_decompileSharedTuples_Skia(self):
		sharedTuples = decompileSharedTuples(
			axisTags=["wght", "wdth"], sharedTupleCount=8,
			data=SKIA_GVAR_SHARED_TUPLES_DATA, offset=0)
		self.assertEqual(sharedTuples, SKIA_GVAR_SHARED_TUPLES)

	def test_decompileSharedTuples_empty(self):
		self.assertEqual(decompileSharedTuples(["wght"], 0, b"", 0), [])

	def test_compileTupleVariationStore_allVariationsRedundant(self):
		axes = {"wght": (0.3, 0.4, 0.5), "opsz": (0.7, 0.8, 0.9)}
		variations = [
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4),
			TupleVariation(axes, [None] * 4)
		]
		self.assertEqual(
			compileTupleVariationStore(variations, pointCount=8,
			                           axisTags=["wght", "opsz"],
			                           sharedTupleIndices={}),
            (0, b"", b""))

	def test_compileTupleVariationStore_noVariations(self):
		self.assertEqual(
			compileTupleVariationStore(variations=[], pointCount=8,
			                           axisTags=["wght", "opsz"],
			                           sharedTupleIndices={}),
            (0, b"", b""))

	def test_compileTupleVariationStore_roundTrip_cvar(self):
		deltas = [1, 2, 3, 4]
		variations = [
			TupleVariation({"wght": (0.5, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)},
			               deltas),
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)},
			               deltas)
		]
		tupleVariationCount, tuples, data = compileTupleVariationStore(
			variations, pointCount=4, axisTags=["wght", "wdth"],
			sharedTupleIndices={})
		self.assertEqual(
			decompileTupleVariationStore("cvar", ["wght", "wdth"],
			                             tupleVariationCount, pointCount=4,
			                             sharedTuples={}, data=(tuples + data),
			                             pos=0, dataPos=len(tuples)),
            variations)

	def test_compileTupleVariationStore_roundTrip_gvar(self):
		deltas = [(1,1), (2,2), (3,3), (4,4)]
		variations = [
			TupleVariation({"wght": (0.5, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)},
			               deltas),
			TupleVariation({"wght": (1.0, 1.0, 1.0), "wdth": (1.0, 1.0, 1.0)},
			               deltas)
		]
		tupleVariationCount, tuples, data = compileTupleVariationStore(
			variations, pointCount=4, axisTags=["wght", "wdth"],
			sharedTupleIndices={})
		self.assertEqual(
			decompileTupleVariationStore("gvar", ["wght", "wdth"],
			                             tupleVariationCount, pointCount=4,
			                             sharedTuples={}, data=(tuples + data),
			                             pos=0, dataPos=len(tuples)),
            variations)

	def test_decompileTupleVariationStore_Skia_I(self):
		tvar = decompileTupleVariationStore(
			tableTag="gvar", axisTags=["wght", "wdth"],
			tupleVariationCount=8, pointCount=18,
			sharedTuples=SKIA_GVAR_SHARED_TUPLES,
			data=SKIA_GVAR_I_DATA, pos=4, dataPos=36)
		self.assertEqual(len(tvar), 8)
		self.assertEqual(tvar[0].axes, {"wght": (0.0, 1.0, 1.0)})
		self.assertEqual(
			" ".join(["%d,%d" % c for c in tvar[0].coordinates]),
			"257,0 -127,0 -128,58 -130,90 -130,62 -130,67 -130,32 -127,0 "
			"257,0 259,14 260,64 260,21 260,69 258,124 0,0 130,0 0,0 0,0")

	def test_decompileTupleVariationStore_empty(self):
		self.assertEqual(
			decompileTupleVariationStore(tableTag="gvar", axisTags=[],
			                             tupleVariationCount=0, pointCount=5,
			                             sharedTuples=[],
			                             data=b"", pos=4, dataPos=4),
			[])

	def test_getTupleSize(self):
		getTupleSize = TupleVariation.getTupleSize_
		numAxes = 3
		self.assertEqual(4 + numAxes * 2, getTupleSize(0x8042, numAxes))
		self.assertEqual(4 + numAxes * 4, getTupleSize(0x4077, numAxes))
		self.assertEqual(4, getTupleSize(0x2077, numAxes))
		self.assertEqual(4, getTupleSize(11, numAxes))

	def test_inferRegion(self):
		start, end = inferRegion_({"wght": -0.3, "wdth": 0.7})
		self.assertEqual(start, {"wght": -0.3, "wdth": 0.0})
		self.assertEqual(end, {"wght": 0.0, "wdth": 0.7})

	@staticmethod
	def xml_lines(writer):
		content = writer.file.getvalue().decode("utf-8")
		return [line.strip() for line in content.splitlines()][1:]

	def test_getCoordWidth(self):
		empty = TupleVariation({}, [])
		self.assertEqual(empty.getCoordWidth(), 0)

		empty = TupleVariation({}, [None])
		self.assertEqual(empty.getCoordWidth(), 0)

		gvarTuple = TupleVariation({}, [None, (0, 0)])
		self.assertEqual(gvarTuple.getCoordWidth(), 2)

		cvarTuple = TupleVariation({}, [None, 0])
		self.assertEqual(cvarTuple.getCoordWidth(), 1)

		cvarTuple.coordinates[1] *= 1.0
		self.assertEqual(cvarTuple.getCoordWidth(), 1)

		with self.assertRaises(TypeError):
			TupleVariation({}, [None, "a"]).getCoordWidth()

	def test_scaleDeltas_cvar(self):
		var = TupleVariation({}, [100, None])

		var.scaleDeltas(1.0)
		self.assertEqual(var.coordinates, [100, None])

		var.scaleDeltas(0.333)
		self.assertAlmostEqual(var.coordinates[0], 33.3)
		self.assertIsNone(var.coordinates[1])

		var.scaleDeltas(0.0)
		self.assertEqual(var.coordinates, [0, None])

	def test_scaleDeltas_gvar(self):
		var = TupleVariation({}, [(100, 200), None])

		var.scaleDeltas(1.0)
		self.assertEqual(var.coordinates, [(100, 200), None])

		var.scaleDeltas(0.333)
		self.assertAlmostEqual(var.coordinates[0][0], 33.3)
		self.assertAlmostEqual(var.coordinates[0][1], 66.6)
		self.assertIsNone(var.coordinates[1])

		var.scaleDeltas(0.0)
		self.assertEqual(var.coordinates, [(0, 0), None])

	def test_roundDeltas_cvar(self):
		var = TupleVariation({}, [55.5, None, 99.9])
		var.roundDeltas()
		self.assertEqual(var.coordinates, [56, None, 100])

	def test_roundDeltas_gvar(self):
		var = TupleVariation({}, [(55.5, 100.0), None, (99.9, 100.0)])
		var.roundDeltas()
		self.assertEqual(var.coordinates, [(56, 100), None, (100, 100)])

	def test_calcInferredDeltas(self):
		var = TupleVariation({}, [(0, 0), None, None, None])
		coords = [(1, 1), (1, 1), (1, 1), (1, 1)]

		var.calcInferredDeltas(coords, [])

		self.assertEqual(
			var.coordinates,
			[(0, 0), (0, 0), (0, 0), (0, 0)]
		)

	def test_calcInferredDeltas_invalid(self):
		# cvar tuples can't have inferred deltas
		with self.assertRaises(TypeError):
			TupleVariation({}, [0]).calcInferredDeltas([], [])

		# origCoords must have same length as self.coordinates
		with self.assertRaises(ValueError):
			TupleVariation({}, [(0, 0), None]).calcInferredDeltas([], [])

		# at least 4 phantom points required
		with self.assertRaises(AssertionError):
			TupleVariation({}, [(0, 0), None]).calcInferredDeltas([(0, 0), (0, 0)], [])

		with self.assertRaises(AssertionError):
			TupleVariation({}, [(0, 0)] + [None]*5).calcInferredDeltas(
				[(0, 0)]*6,
				[1, 0]  # endPts not in increasing order
			)

	def test_optimize(self):
		var = TupleVariation({"wght": (0.0, 1.0, 1.0)}, [(0, 0)]*5)

		var.optimize([(0, 0)]*5, [0])

		self.assertEqual(var.coordinates, [None, None, None, None, None])

	def test_optimize_isComposite(self):
		# when a composite glyph's deltas are all (0, 0), we still want
		# to write out an entry in gvar, else macOS doesn't apply any
		# variations to the composite glyph (even if its individual components
		# do vary).
		# https://github.com/fonttools/fonttools/issues/1381
		var = TupleVariation({"wght": (0.0, 1.0, 1.0)}, [(0, 0)]*5)
		var.optimize([(0, 0)]*5, [0], isComposite=True)
		self.assertEqual(var.coordinates, [(0, 0)]*5)

		# it takes more than 128 (0, 0) deltas before the optimized tuple with
		# (None) inferred deltas (except for the first) becomes smaller than
		# the un-optimized one that has all deltas explicitly set to (0, 0).
		var = TupleVariation({"wght": (0.0, 1.0, 1.0)}, [(0, 0)]*129)
		var.optimize([(0, 0)]*129, list(range(129-4)), isComposite=True)
		self.assertEqual(var.coordinates, [(0, 0)] + [None]*128)

	def test_sum_deltas_gvar(self):
		var1 = TupleVariation(
			{},
			[
				(-20, 0), (-20, 0), (20, 0), (20, 0),
				(0, 0), (0, 0), (0, 0), (0, 0),
			]
		)
		var2 = TupleVariation(
			{},
			[
				(-10, 0), (-10, 0), (10, 0), (10, 0),
				(0, 0), (20, 0), (0, 0), (0, 0),
			]
		)

		var1 += var2

		self.assertEqual(
			var1.coordinates,
			[
				(-30, 0), (-30, 0), (30, 0), (30, 0),
				(0, 0), (20, 0), (0, 0), (0, 0),
			]
		)

	def test_sum_deltas_gvar_invalid_length(self):
		var1 = TupleVariation({}, [(1, 2)])
		var2 = TupleVariation({}, [(1, 2), (3, 4)])

		with self.assertRaisesRegex(ValueError, "deltas with different lengths"):
			var1 += var2

	def test_sum_deltas_gvar_with_inferred_points(self):
		var1 = TupleVariation({}, [(1, 2), None])
		var2 = TupleVariation({}, [(2, 3), None])

		with self.assertRaisesRegex(ValueError, "deltas with inferred points"):
			var1 += var2

	def test_sum_deltas_cvar(self):
		axes = {"wght": (0.0, 1.0, 1.0)}
		var1 = TupleVariation(axes, [0, 1, None, None])
		var2 = TupleVariation(axes, [None, 2, None, 3])
		var3 = TupleVariation(axes, [None, None, None, 4])

		var1 += var2
		var1 += var3

		self.assertEqual(var1.coordinates, [0, 3, None, 7])


if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())
