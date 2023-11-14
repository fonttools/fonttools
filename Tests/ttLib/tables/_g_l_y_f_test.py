from fontTools.misc.fixedTools import otRound
from fontTools.misc.testTools import getXML, parseXML
from fontTools.misc.transform import Transform
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.ttLib import TTFont, newTable, TTLibError
from fontTools.ttLib.tables._g_l_y_f import (
    Glyph,
    GlyphCoordinates,
    GlyphComponent,
    dropImpliedOnCurvePoints,
    flagOnCurve,
    flagCubic,
    ARGS_ARE_XY_VALUES,
    SCALED_COMPONENT_OFFSET,
    UNSCALED_COMPONENT_OFFSET,
    WE_HAVE_A_SCALE,
    WE_HAVE_A_TWO_BY_TWO,
    WE_HAVE_AN_X_AND_Y_SCALE,
)
from fontTools.ttLib.tables import ttProgram
import sys
import array
from copy import deepcopy
from io import StringIO, BytesIO
import itertools
import pytest
import re
import os
import unittest


class GlyphCoordinatesTest(object):
    def test_translate(self):
        g = GlyphCoordinates([(1, 2)])
        g.translate((0.5, 0))
        assert g == GlyphCoordinates([(1.5, 2.0)])

    def test_scale(self):
        g = GlyphCoordinates([(1, 2)])
        g.scale((0.5, 0))
        assert g == GlyphCoordinates([(0.5, 0.0)])

    def test_transform(self):
        g = GlyphCoordinates([(1, 2)])
        g.transform(((0.5, 0), (0.2, 0.5)))
        assert g[0] == GlyphCoordinates([(0.9, 1.0)])[0]

    def test__eq__(self):
        g = GlyphCoordinates([(1, 2)])
        g2 = GlyphCoordinates([(1.0, 2)])
        g3 = GlyphCoordinates([(1.5, 2)])
        assert g == g2
        assert not g == g3
        assert not g2 == g3
        assert not g == object()

    def test__ne__(self):
        g = GlyphCoordinates([(1, 2)])
        g2 = GlyphCoordinates([(1.0, 2)])
        g3 = GlyphCoordinates([(1.5, 2)])
        assert not (g != g2)
        assert g != g3
        assert g2 != g3
        assert g != object()

    def test__pos__(self):
        g = GlyphCoordinates([(1, 2)])
        g2 = +g
        assert g == g2

    def test__neg__(self):
        g = GlyphCoordinates([(1, 2)])
        g2 = -g
        assert g2 == GlyphCoordinates([(-1, -2)])

    @pytest.mark.skipif(sys.version_info[0] < 3, reason="__round___ requires Python 3")
    def test__round__(self):
        g = GlyphCoordinates([(-1.5, 2)])
        g2 = round(g)
        assert g2 == GlyphCoordinates([(-1, 2)])

    def test__add__(self):
        g1 = GlyphCoordinates([(1, 2)])
        g2 = GlyphCoordinates([(3, 4)])
        g3 = GlyphCoordinates([(4, 6)])
        assert g1 + g2 == g3
        assert g1 + (1, 1) == GlyphCoordinates([(2, 3)])
        with pytest.raises(TypeError) as excinfo:
            assert g1 + object()
        assert "unsupported operand" in str(excinfo.value)

    def test__sub__(self):
        g1 = GlyphCoordinates([(1, 2)])
        g2 = GlyphCoordinates([(3, 4)])
        g3 = GlyphCoordinates([(-2, -2)])
        assert g1 - g2 == g3
        assert g1 - (1, 1) == GlyphCoordinates([(0, 1)])
        with pytest.raises(TypeError) as excinfo:
            assert g1 - object()
        assert "unsupported operand" in str(excinfo.value)

    def test__rsub__(self):
        g = GlyphCoordinates([(1, 2)])
        # other + (-self)
        assert (1, 1) - g == GlyphCoordinates([(0, -1)])

    def test__mul__(self):
        g = GlyphCoordinates([(1, 2)])
        assert g * 3 == GlyphCoordinates([(3, 6)])
        assert g * (3, 2) == GlyphCoordinates([(3, 4)])
        assert g * (1, 1) == g
        with pytest.raises(TypeError) as excinfo:
            assert g * object()
        assert "unsupported operand" in str(excinfo.value)

    def test__truediv__(self):
        g = GlyphCoordinates([(1, 2)])
        assert g / 2 == GlyphCoordinates([(0.5, 1)])
        assert g / (1, 2) == GlyphCoordinates([(1, 1)])
        assert g / (1, 1) == g
        with pytest.raises(TypeError) as excinfo:
            assert g / object()
        assert "unsupported operand" in str(excinfo.value)

    def test__iadd__(self):
        g = GlyphCoordinates([(1, 2)])
        g += (0.5, 0)
        assert g == GlyphCoordinates([(1.5, 2.0)])
        g2 = GlyphCoordinates([(3, 4)])
        g += g2
        assert g == GlyphCoordinates([(4.5, 6.0)])

    def test__isub__(self):
        g = GlyphCoordinates([(1, 2)])
        g -= (0.5, 0)
        assert g == GlyphCoordinates([(0.5, 2.0)])
        g2 = GlyphCoordinates([(3, 4)])
        g -= g2
        assert g == GlyphCoordinates([(-2.5, -2.0)])

    def __test__imul__(self):
        g = GlyphCoordinates([(1, 2)])
        g *= (2, 0.5)
        g *= 2
        assert g == GlyphCoordinates([(4.0, 2.0)])
        g = GlyphCoordinates([(1, 2)])
        g *= 2
        assert g == GlyphCoordinates([(2, 4)])

    def test__itruediv__(self):
        g = GlyphCoordinates([(1, 3)])
        g /= (0.5, 1.5)
        g /= 2
        assert g == GlyphCoordinates([(1.0, 1.0)])

    def test__bool__(self):
        g = GlyphCoordinates([])
        assert bool(g) == False
        g = GlyphCoordinates([(0, 0), (0.0, 0)])
        assert bool(g) == True
        g = GlyphCoordinates([(0, 0), (1, 0)])
        assert bool(g) == True
        g = GlyphCoordinates([(0, 0.5), (0, 0)])
        assert bool(g) == True

    def test_double_precision_float(self):
        # https://github.com/fonttools/fonttools/issues/963
        afloat = 242.50000000000003
        g = GlyphCoordinates([(afloat, 0)])
        g.toInt()
        # this would return 242 if the internal array.array typecode is 'f',
        # since the Python float is truncated to a C float.
        # when using typecode 'd' it should return the correct value 243
        assert g[0][0] == otRound(afloat)

    def test__checkFloat_overflow(self):
        g = GlyphCoordinates([(1, 1)])
        g.append((0x8000, 0))
        assert list(g.array) == [1.0, 1.0, 32768.0, 0.0]


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, "data")

GLYF_TTX = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.ttx")
GLYF_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.glyf.bin")
HEAD_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.head.bin")
LOCA_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.loca.bin")
MAXP_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.maxp.bin")
INST_TTX = os.path.join(DATA_DIR, "_g_l_y_f_instructions.ttx")


def strip_ttLibVersion(string):
    return re.sub(' ttLibVersion=".*"', "", string)


class GlyfTableTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    @classmethod
    def setUpClass(cls):
        with open(GLYF_BIN, "rb") as f:
            cls.glyfData = f.read()
        with open(HEAD_BIN, "rb") as f:
            cls.headData = f.read()
        with open(LOCA_BIN, "rb") as f:
            cls.locaData = f.read()
        with open(MAXP_BIN, "rb") as f:
            cls.maxpData = f.read()
        with open(GLYF_TTX, "r") as f:
            cls.glyfXML = strip_ttLibVersion(f.read()).splitlines()

    def test_toXML(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        glyfTable = font["glyf"] = newTable("glyf")
        font["head"] = newTable("head")
        font["loca"] = newTable("loca")
        font["maxp"] = newTable("maxp")
        font["maxp"].decompile(self.maxpData, font)
        font["head"].decompile(self.headData, font)
        font["loca"].decompile(self.locaData, font)
        glyfTable.decompile(self.glyfData, font)
        out = StringIO()
        font.saveXML(out)
        glyfXML = strip_ttLibVersion(out.getvalue()).splitlines()
        self.assertEqual(glyfXML, self.glyfXML)

    def test_fromXML(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        font.importXML(GLYF_TTX)
        glyfTable = font["glyf"]
        glyfData = glyfTable.compile(font)
        self.assertEqual(glyfData, self.glyfData)

    def test_instructions_roundtrip(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        font.importXML(INST_TTX)
        glyfTable = font["glyf"]
        self.glyfData = glyfTable.compile(font)
        out = StringIO()
        font.saveXML(out)
        glyfXML = strip_ttLibVersion(out.getvalue()).splitlines()
        with open(INST_TTX, "r") as f:
            origXML = strip_ttLibVersion(f.read()).splitlines()
        self.assertEqual(glyfXML, origXML)

    def test_recursiveComponent(self):
        glyphSet = {}
        pen_dummy = TTGlyphPen(glyphSet)
        glyph_dummy = pen_dummy.glyph()
        glyphSet["A"] = glyph_dummy
        glyphSet["B"] = glyph_dummy
        pen_A = TTGlyphPen(glyphSet)
        pen_A.addComponent("B", (1, 0, 0, 1, 0, 0))
        pen_B = TTGlyphPen(glyphSet)
        pen_B.addComponent("A", (1, 0, 0, 1, 0, 0))
        glyph_A = pen_A.glyph()
        glyph_B = pen_B.glyph()
        glyphSet["A"] = glyph_A
        glyphSet["B"] = glyph_B
        with self.assertRaisesRegex(
            TTLibError, "glyph '.' contains a recursive component reference"
        ):
            glyph_A.getCoordinates(glyphSet)

    def test_trim_remove_hinting_composite_glyph(self):
        glyphSet = {"dummy": TTGlyphPen(None).glyph()}

        pen = TTGlyphPen(glyphSet)
        pen.addComponent("dummy", (1, 0, 0, 1, 0, 0))
        composite = pen.glyph()
        p = ttProgram.Program()
        p.fromAssembly(["SVTCA[0]"])
        composite.program = p
        glyphSet["composite"] = composite

        glyfTable = newTable("glyf")
        glyfTable.glyphs = glyphSet
        glyfTable.glyphOrder = sorted(glyphSet)

        composite.compact(glyfTable)

        self.assertTrue(hasattr(composite, "data"))

        # remove hinting from the compacted composite glyph, without expanding it
        composite.trim(remove_hinting=True)

        # check that, after expanding the glyph, we have no instructions
        composite.expand(glyfTable)
        self.assertFalse(hasattr(composite, "program"))

        # now remove hinting from expanded composite glyph
        composite.program = p
        composite.trim(remove_hinting=True)

        # check we have no instructions
        self.assertFalse(hasattr(composite, "program"))

        composite.compact(glyfTable)

    def test_bit6_draw_to_pen_issue1771(self):
        # https://github.com/fonttools/fonttools/issues/1771
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        # glyph00003 contains a bit 6 flag on the first point,
        # which triggered the issue
        font.importXML(GLYF_TTX)
        glyfTable = font["glyf"]
        pen = RecordingPen()
        glyfTable["glyph00003"].draw(pen, glyfTable=glyfTable)
        expected = [
            ("moveTo", ((501, 1430),)),
            ("lineTo", ((683, 1430),)),
            ("lineTo", ((1172, 0),)),
            ("lineTo", ((983, 0),)),
            ("lineTo", ((591, 1193),)),
            ("lineTo", ((199, 0),)),
            ("lineTo", ((12, 0),)),
            ("closePath", ()),
            ("moveTo", ((249, 514),)),
            ("lineTo", ((935, 514),)),
            ("lineTo", ((935, 352),)),
            ("lineTo", ((249, 352),)),
            ("closePath", ()),
        ]
        self.assertEqual(pen.value, expected)

    def test_bit6_draw_to_pointpen(self):
        # https://github.com/fonttools/fonttools/issues/1771
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        # glyph00003 contains a bit 6 flag on the first point
        # which triggered the issue
        font.importXML(GLYF_TTX)
        glyfTable = font["glyf"]
        pen = RecordingPointPen()
        glyfTable["glyph00003"].drawPoints(pen, glyfTable=glyfTable)
        expected = [
            ("beginPath", (), {}),
            ("addPoint", ((501, 1430), "line", False, None), {}),
            ("addPoint", ((683, 1430), "line", False, None), {}),
            ("addPoint", ((1172, 0), "line", False, None), {}),
            ("addPoint", ((983, 0), "line", False, None), {}),
        ]
        self.assertEqual(pen.value[: len(expected)], expected)

    def test_draw_vs_drawpoints(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        font.importXML(GLYF_TTX)
        glyfTable = font["glyf"]
        pen1 = RecordingPen()
        pen2 = RecordingPen()
        glyfTable["glyph00003"].draw(pen1, glyfTable)
        glyfTable["glyph00003"].drawPoints(PointToSegmentPen(pen2), glyfTable)
        self.assertEqual(pen1.value, pen2.value)

    def test_compile_empty_table(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        font.importXML(GLYF_TTX)
        glyfTable = font["glyf"]
        # set all glyphs to zero contours
        glyfTable.glyphs = {glyphName: Glyph() for glyphName in font.getGlyphOrder()}
        glyfData = glyfTable.compile(font)
        self.assertEqual(glyfData, b"\x00")
        self.assertEqual(list(font["loca"]), [0] * (font["maxp"].numGlyphs + 1))

    def test_decompile_empty_table(self):
        font = TTFont()
        glyphNames = [".notdef", "space"]
        font.setGlyphOrder(glyphNames)
        font["loca"] = newTable("loca")
        font["loca"].locations = [0] * (len(glyphNames) + 1)
        font["glyf"] = newTable("glyf")
        font["glyf"].decompile(b"\x00", font)
        self.assertEqual(len(font["glyf"]), 2)
        self.assertEqual(font["glyf"][".notdef"].numberOfContours, 0)
        self.assertEqual(font["glyf"]["space"].numberOfContours, 0)

    def test_getPhantomPoints(self):
        # https://github.com/fonttools/fonttools/issues/2295
        font = TTFont()
        glyphNames = [".notdef"]
        font.setGlyphOrder(glyphNames)
        font["loca"] = newTable("loca")
        font["loca"].locations = [0] * (len(glyphNames) + 1)
        font["glyf"] = newTable("glyf")
        font["glyf"].decompile(b"\x00", font)
        font["hmtx"] = newTable("hmtx")
        font["hmtx"].metrics = {".notdef": (100, 0)}
        font["head"] = newTable("head")
        font["head"].unitsPerEm = 1000
        with pytest.deprecated_call():
            self.assertEqual(
                font["glyf"].getPhantomPoints(".notdef", font, 0),
                [(0, 0), (100, 0), (0, 0), (0, -1000)],
            )

    def test_getGlyphID(self):
        # https://github.com/fonttools/fonttools/pull/3301#discussion_r1360405861
        glyf = newTable("glyf")
        glyf.setGlyphOrder([".notdef", "a", "b"])
        glyf.glyphs = {}
        for glyphName in glyf.glyphOrder:
            glyf[glyphName] = Glyph()

        assert glyf.getGlyphID("a") == 1

        with pytest.raises(ValueError):
            glyf.getGlyphID("c")

        glyf["c"] = Glyph()
        assert glyf.getGlyphID("c") == 3

        del glyf["b"]
        assert glyf.getGlyphID("c") == 2


class GlyphTest:
    def test_getCoordinates(self):
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.lineTo((100, 100))
        pen.lineTo((0, 100))
        pen.closePath()
        # simple contour glyph
        glyphSet["a"] = a = pen.glyph()

        assert a.getCoordinates(glyphSet) == (
            GlyphCoordinates([(0, 0), (100, 0), (100, 100), (0, 100)]),
            [3],
            array.array("B", [1, 1, 1, 1]),
        )

        # composite glyph with only XY offset
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("a", (1, 0, 0, 1, 10, 20))
        glyphSet["b"] = b = pen.glyph()

        assert b.getCoordinates(glyphSet) == (
            GlyphCoordinates([(10, 20), (110, 20), (110, 120), (10, 120)]),
            [3],
            array.array("B", [1, 1, 1, 1]),
        )

        # composite glyph with a scale (and referencing another composite glyph)
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("b", (0.5, 0, 0, 0.5, 0, 0))
        glyphSet["c"] = c = pen.glyph()

        assert c.getCoordinates(glyphSet) == (
            GlyphCoordinates([(5, 10), (55, 10), (55, 60), (5, 60)]),
            [3],
            array.array("B", [1, 1, 1, 1]),
        )

        # composite glyph with unscaled offset (MS-style)
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("a", (0.5, 0, 0, 0.5, 10, 20))
        glyphSet["d"] = d = pen.glyph()
        d.components[0].flags |= UNSCALED_COMPONENT_OFFSET

        assert d.getCoordinates(glyphSet) == (
            GlyphCoordinates([(10, 20), (60, 20), (60, 70), (10, 70)]),
            [3],
            array.array("B", [1, 1, 1, 1]),
        )

        # composite glyph with a scaled offset (Apple-style)
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("a", (0.5, 0, 0, 0.5, 10, 20))
        glyphSet["e"] = e = pen.glyph()
        e.components[0].flags |= SCALED_COMPONENT_OFFSET

        assert e.getCoordinates(glyphSet) == (
            GlyphCoordinates([(5, 10), (55, 10), (55, 60), (5, 60)]),
            [3],
            array.array("B", [1, 1, 1, 1]),
        )

        # composite glyph where the 2nd and 3rd components use anchor points
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("a", (1, 0, 0, 1, 0, 0))
        glyphSet["f"] = f = pen.glyph()

        comp1 = GlyphComponent()
        comp1.glyphName = "a"
        # aling the new component's pt 0 to pt 2 of contour points added so far
        comp1.firstPt = 2
        comp1.secondPt = 0
        comp1.flags = 0
        f.components.append(comp1)

        comp2 = GlyphComponent()
        comp2.glyphName = "a"
        # aling the new component's pt 0 to pt 6 of contour points added so far
        comp2.firstPt = 6
        comp2.secondPt = 0
        comp2.transform = [[0.707107, 0.707107], [-0.707107, 0.707107]]  # rotate 45 deg
        comp2.flags = WE_HAVE_A_TWO_BY_TWO
        f.components.append(comp2)

        coords, end_pts, flags = f.getCoordinates(glyphSet)
        assert end_pts == [3, 7, 11]
        assert flags == array.array("B", [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        assert list(sum(coords, ())) == pytest.approx(
            [
                0,
                0,
                100,
                0,
                100,
                100,
                0,
                100,
                100,
                100,
                200,
                100,
                200,
                200,
                100,
                200,
                200,
                200,
                270.7107,
                270.7107,
                200.0,
                341.4214,
                129.2893,
                270.7107,
            ]
        )

    def test_getCompositeMaxpValues(self):
        # https://github.com/fonttools/fonttools/issues/2044
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)  # empty non-composite glyph
        glyphSet["fraction"] = pen.glyph()
        glyphSet["zero.numr"] = pen.glyph()
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("zero.numr", (1, 0, 0, 1, 0, 0))
        glyphSet["zero.dnom"] = pen.glyph()
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("zero.numr", (1, 0, 0, 1, 0, 0))
        pen.addComponent("fraction", (1, 0, 0, 1, 0, 0))
        pen.addComponent("zero.dnom", (1, 0, 0, 1, 0, 0))
        glyphSet["percent"] = pen.glyph()
        pen = TTGlyphPen(glyphSet)
        pen.addComponent("zero.numr", (1, 0, 0, 1, 0, 0))
        pen.addComponent("fraction", (1, 0, 0, 1, 0, 0))
        pen.addComponent("zero.dnom", (1, 0, 0, 1, 0, 0))
        pen.addComponent("zero.dnom", (1, 0, 0, 1, 0, 0))
        glyphSet["perthousand"] = pen.glyph()
        assert glyphSet["zero.dnom"].getCompositeMaxpValues(glyphSet)[2] == 1
        assert glyphSet["percent"].getCompositeMaxpValues(glyphSet)[2] == 2
        assert glyphSet["perthousand"].getCompositeMaxpValues(glyphSet)[2] == 2

    def test_recalcBounds_empty_components(self):
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)
        # empty simple glyph
        foo = glyphSet["foo"] = pen.glyph()
        # use the empty 'foo' glyph as a component in 'bar' with some x/y offsets
        pen.addComponent("foo", (1, 0, 0, 1, -80, 50))
        bar = glyphSet["bar"] = pen.glyph()

        foo.recalcBounds(glyphSet)
        bar.recalcBounds(glyphSet)

        # we expect both the empty simple glyph and the composite referencing it
        # to have empty bounding boxes (0, 0, 0, 0) no matter the component's shift
        assert (foo.xMin, foo.yMin, foo.xMax, foo.yMax) == (0, 0, 0, 0)
        assert (bar.xMin, bar.yMin, bar.xMax, bar.yMax) == (0, 0, 0, 0)


class GlyphComponentTest:
    def test_toXML_no_transform(self):
        comp = GlyphComponent()
        comp.glyphName = "a"
        comp.flags = ARGS_ARE_XY_VALUES
        comp.x, comp.y = 1, 2

        assert getXML(comp.toXML) == [
            '<component glyphName="a" x="1" y="2" flags="0x2"/>'
        ]

    def test_toXML_transform_scale(self):
        comp = GlyphComponent()
        comp.glyphName = "a"
        comp.flags = ARGS_ARE_XY_VALUES | WE_HAVE_A_SCALE
        comp.x, comp.y = 1, 2

        comp.transform = [[0.2999878, 0], [0, 0.2999878]]
        assert getXML(comp.toXML) == [
            '<component glyphName="a" x="1" y="2" scale="0.3" flags="0xa"/>'
        ]

    def test_toXML_transform_xy_scale(self):
        comp = GlyphComponent()
        comp.glyphName = "a"
        comp.flags = ARGS_ARE_XY_VALUES | WE_HAVE_AN_X_AND_Y_SCALE
        comp.x, comp.y = 1, 2

        comp.transform = [[0.5999756, 0], [0, 0.2999878]]
        assert getXML(comp.toXML) == [
            '<component glyphName="a" x="1" y="2" scalex="0.6" '
            'scaley="0.3" flags="0x42"/>'
        ]

    def test_toXML_transform_2x2_scale(self):
        comp = GlyphComponent()
        comp.glyphName = "a"
        comp.flags = ARGS_ARE_XY_VALUES | WE_HAVE_A_TWO_BY_TWO
        comp.x, comp.y = 1, 2

        comp.transform = [[0.5999756, -0.2000122], [0.2000122, 0.2999878]]
        assert getXML(comp.toXML) == [
            '<component glyphName="a" x="1" y="2" scalex="0.6" scale01="-0.2" '
            'scale10="0.2" scaley="0.3" flags="0x82"/>'
        ]

    def test_fromXML_no_transform(self):
        comp = GlyphComponent()
        for name, attrs, content in parseXML(
            ['<component glyphName="a" x="1" y="2" flags="0x2"/>']
        ):
            comp.fromXML(name, attrs, content, ttFont=None)

        assert comp.glyphName == "a"
        assert comp.flags & ARGS_ARE_XY_VALUES != 0
        assert (comp.x, comp.y) == (1, 2)
        assert not hasattr(comp, "transform")

    def test_fromXML_transform_scale(self):
        comp = GlyphComponent()
        for name, attrs, content in parseXML(
            ['<component glyphName="a" x="1" y="2" scale="0.3" flags="0xa"/>']
        ):
            comp.fromXML(name, attrs, content, ttFont=None)

        assert comp.glyphName == "a"
        assert comp.flags & ARGS_ARE_XY_VALUES != 0
        assert comp.flags & WE_HAVE_A_SCALE != 0
        assert (comp.x, comp.y) == (1, 2)
        assert hasattr(comp, "transform")
        for value, expected in zip(
            itertools.chain(*comp.transform), [0.2999878, 0, 0, 0.2999878]
        ):
            assert value == pytest.approx(expected)

    def test_fromXML_transform_xy_scale(self):
        comp = GlyphComponent()
        for name, attrs, content in parseXML(
            [
                '<component glyphName="a" x="1" y="2" scalex="0.6" '
                'scaley="0.3" flags="0x42"/>'
            ]
        ):
            comp.fromXML(name, attrs, content, ttFont=None)

        assert comp.glyphName == "a"
        assert comp.flags & ARGS_ARE_XY_VALUES != 0
        assert comp.flags & WE_HAVE_AN_X_AND_Y_SCALE != 0
        assert (comp.x, comp.y) == (1, 2)
        assert hasattr(comp, "transform")
        for value, expected in zip(
            itertools.chain(*comp.transform), [0.5999756, 0, 0, 0.2999878]
        ):
            assert value == pytest.approx(expected)

    def test_fromXML_transform_2x2_scale(self):
        comp = GlyphComponent()
        for name, attrs, content in parseXML(
            [
                '<component glyphName="a" x="1" y="2" scalex="0.6" scale01="-0.2" '
                'scale10="0.2" scaley="0.3" flags="0x82"/>'
            ]
        ):
            comp.fromXML(name, attrs, content, ttFont=None)

        assert comp.glyphName == "a"
        assert comp.flags & ARGS_ARE_XY_VALUES != 0
        assert comp.flags & WE_HAVE_A_TWO_BY_TWO != 0
        assert (comp.x, comp.y) == (1, 2)
        assert hasattr(comp, "transform")
        for value, expected in zip(
            itertools.chain(*comp.transform),
            [0.5999756, -0.2000122, 0.2000122, 0.2999878],
        ):
            assert value == pytest.approx(expected)

    def test_toXML_reference_points(self):
        comp = GlyphComponent()
        comp.glyphName = "a"
        comp.flags = 0
        comp.firstPt = 1
        comp.secondPt = 2

        assert getXML(comp.toXML) == [
            '<component glyphName="a" firstPt="1" secondPt="2" flags="0x0"/>'
        ]

    def test_fromXML_reference_points(self):
        comp = GlyphComponent()
        for name, attrs, content in parseXML(
            ['<component glyphName="a" firstPt="1" secondPt="2" flags="0x0"/>']
        ):
            comp.fromXML(name, attrs, content, ttFont=None)

        assert comp.glyphName == "a"
        assert comp.flags == 0
        assert (comp.firstPt, comp.secondPt) == (1, 2)
        assert not hasattr(comp, "transform")

    def test_trim_varComposite_glyph(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        glyf = font["glyf"]

        glyf.glyphs["uniAC00"].trim()
        glyf.glyphs["uniAC01"].trim()

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        glyf = font["glyf"]

        glyf.glyphs["uni6868"].trim()

    def test_varComposite_basic(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea", "name", "fvar"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()


class GlyphCubicTest:
    def test_roundtrip(self):
        font_path = os.path.join(DATA_DIR, "NotoSans-VF-cubic.subset.ttf")
        font = TTFont(font_path)
        tables = [table_tag for table_tag in font.keys() if table_tag not in {"head"}]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()

    def test_no_oncurves(self):
        glyph = Glyph()
        glyph.numberOfContours = 1
        glyph.coordinates = GlyphCoordinates(
            [(0, 0), (1, 0), (1, 0), (1, 1), (1, 1), (0, 1), (0, 1), (0, 0)]
        )
        glyph.flags = array.array("B", [flagCubic] * 8)
        glyph.endPtsOfContours = [7]
        glyph.program = ttProgram.Program()

        for i in range(2):
            if i == 1:
                glyph.compile(None)

            pen = RecordingPen()
            glyph.draw(pen, None)

            assert pen.value == [
                ("moveTo", ((0, 0),)),
                ("curveTo", ((0, 0), (1, 0), (1, 0))),
                ("curveTo", ((1, 0), (1, 1), (1, 1))),
                ("curveTo", ((1, 1), (0, 1), (0, 1))),
                ("curveTo", ((0, 1), (0, 0), (0, 0))),
                ("closePath", ()),
            ]

    def test_spline(self):
        glyph = Glyph()
        glyph.numberOfContours = 1
        glyph.coordinates = GlyphCoordinates(
            [(0, 0), (1, 0), (1, 0), (1, 1), (1, 1), (0, 1), (0, 1)]
        )
        glyph.flags = array.array("B", [flagOnCurve] + [flagCubic] * 6)
        glyph.endPtsOfContours = [6]
        glyph.program = ttProgram.Program()

        for i in range(2):
            if i == 1:
                glyph.compile(None)

            pen = RecordingPen()
            glyph.draw(pen, None)

            assert pen.value == [
                ("moveTo", ((0, 0),)),
                ("curveTo", ((1, 0), (1, 0), (1.0, 0.5))),
                ("curveTo", ((1, 1), (1, 1), (0.5, 1.0))),
                ("curveTo", ((0, 1), (0, 1), (0, 0))),
                ("closePath", ()),
            ]


def build_interpolatable_glyphs(contours, *transforms):
    # given a list of lists of (point, flag) tuples (one per contour), build a Glyph
    # then make len(transforms) copies transformed accordingly, and return a
    # list of such interpolatable glyphs.
    glyph1 = Glyph()
    glyph1.numberOfContours = len(contours)
    glyph1.coordinates = GlyphCoordinates(
        [pt for contour in contours for pt, _flag in contour]
    )
    glyph1.flags = array.array(
        "B", [flag for contour in contours for _pt, flag in contour]
    )
    glyph1.endPtsOfContours = [
        sum(len(contour) for contour in contours[: i + 1]) - 1
        for i in range(len(contours))
    ]
    result = [glyph1]
    for t in transforms:
        glyph = deepcopy(glyph1)
        glyph.coordinates.transform((t[0:2], t[2:4]))
        glyph.coordinates.translate(t[4:6])
        result.append(glyph)
    return result


def test_dropImpliedOnCurvePoints_all_quad_off_curves():
    # Two interpolatable glyphs with same structure, the coordinates of one are 2x the
    # other; all the on-curve points are impliable in each one, thus are dropped from
    # both, leaving contours with off-curve points only.
    glyph1, glyph2 = build_interpolatable_glyphs(
        [
            [
                ((0, 1), flagOnCurve),
                ((1, 1), 0),
                ((1, 0), flagOnCurve),
                ((1, -1), 0),
                ((0, -1), flagOnCurve),
                ((-1, -1), 0),
                ((-1, 0), flagOnCurve),
                ((-1, 1), 0),
            ],
            [
                ((0, 2), flagOnCurve),
                ((2, 2), 0),
                ((2, 0), flagOnCurve),
                ((2, -2), 0),
                ((0, -2), flagOnCurve),
                ((-2, -2), 0),
                ((-2, 0), flagOnCurve),
                ((-2, 2), 0),
            ],
        ],
        Transform().scale(2.0),
    )
    # also add an empty glyph (will be ignored); we use this trick for 'sparse' masters
    glyph3 = Glyph()
    glyph3.numberOfContours = 0

    assert dropImpliedOnCurvePoints(glyph1, glyph2, glyph3) == {
        0,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
    }

    assert glyph1.flags == glyph2.flags == array.array("B", [0, 0, 0, 0, 0, 0, 0, 0])
    assert glyph1.coordinates == GlyphCoordinates(
        [(1, 1), (1, -1), (-1, -1), (-1, 1), (2, 2), (2, -2), (-2, -2), (-2, 2)]
    )
    assert glyph2.coordinates == GlyphCoordinates(
        [(2, 2), (2, -2), (-2, -2), (-2, 2), (4, 4), (4, -4), (-4, -4), (-4, 4)]
    )
    assert glyph1.endPtsOfContours == glyph2.endPtsOfContours == [3, 7]
    assert glyph3.numberOfContours == 0


def test_dropImpliedOnCurvePoints_all_cubic_off_curves():
    # same as above this time using cubic curves
    glyph1, glyph2 = build_interpolatable_glyphs(
        [
            [
                ((0, 1), flagOnCurve),
                ((1, 1), flagCubic),
                ((1, 1), flagCubic),
                ((1, 0), flagOnCurve),
                ((1, -1), flagCubic),
                ((1, -1), flagCubic),
                ((0, -1), flagOnCurve),
                ((-1, -1), flagCubic),
                ((-1, -1), flagCubic),
                ((-1, 0), flagOnCurve),
                ((-1, 1), flagCubic),
                ((-1, 1), flagCubic),
            ]
        ],
        Transform().translate(10.0),
    )
    glyph3 = Glyph()
    glyph3.numberOfContours = 0

    assert dropImpliedOnCurvePoints(glyph1, glyph2, glyph3) == {0, 3, 6, 9}

    assert glyph1.flags == glyph2.flags == array.array("B", [flagCubic] * 8)
    assert glyph1.coordinates == GlyphCoordinates(
        [(1, 1), (1, 1), (1, -1), (1, -1), (-1, -1), (-1, -1), (-1, 1), (-1, 1)]
    )
    assert glyph2.coordinates == GlyphCoordinates(
        [(11, 1), (11, 1), (11, -1), (11, -1), (9, -1), (9, -1), (9, 1), (9, 1)]
    )
    assert glyph1.endPtsOfContours == glyph2.endPtsOfContours == [7]
    assert glyph3.numberOfContours == 0


def test_dropImpliedOnCurvePoints_not_all_impliable():
    # same input as in in test_dropImpliedOnCurvePoints_all_quad_off_curves but we
    # perturbate one of the glyphs such that the 2nd on-curve is no longer half-way
    # between the neighboring off-curves.
    glyph1, glyph2, glyph3 = build_interpolatable_glyphs(
        [
            [
                ((0, 1), flagOnCurve),
                ((1, 1), 0),
                ((1, 0), flagOnCurve),
                ((1, -1), 0),
                ((0, -1), flagOnCurve),
                ((-1, -1), 0),
                ((-1, 0), flagOnCurve),
                ((-1, 1), 0),
            ]
        ],
        Transform().translate(10.0),
        Transform().translate(10.0).scale(2.0),
    )
    p2 = glyph2.coordinates[2]
    glyph2.coordinates[2] = (p2[0] + 2.0, p2[1] - 2.0)

    assert dropImpliedOnCurvePoints(glyph1, glyph2, glyph3) == {
        0,
        # 2,  this is NOT implied because it's no longer impliable for all glyphs
        4,
        6,
    }

    assert glyph2.flags == array.array("B", [0, flagOnCurve, 0, 0, 0])


def test_dropImpliedOnCurvePoints_all_empty_glyphs():
    glyph1 = Glyph()
    glyph1.numberOfContours = 0
    glyph2 = Glyph()
    glyph2.numberOfContours = 0

    assert dropImpliedOnCurvePoints(glyph1, glyph2) == set()


def test_dropImpliedOnCurvePoints_incompatible_number_of_contours():
    glyph1 = Glyph()
    glyph1.numberOfContours = 1
    glyph1.endPtsOfContours = [3]
    glyph1.flags = array.array("B", [1, 1, 1, 1])
    glyph1.coordinates = GlyphCoordinates([(0, 0), (1, 1), (2, 2), (3, 3)])

    glyph2 = Glyph()
    glyph2.numberOfContours = 2
    glyph2.endPtsOfContours = [1, 3]
    glyph2.flags = array.array("B", [1, 1, 1, 1])
    glyph2.coordinates = GlyphCoordinates([(0, 0), (1, 1), (2, 2), (3, 3)])

    with pytest.raises(ValueError, match="Incompatible numberOfContours"):
        dropImpliedOnCurvePoints(glyph1, glyph2)


def test_dropImpliedOnCurvePoints_incompatible_flags():
    glyph1 = Glyph()
    glyph1.numberOfContours = 1
    glyph1.endPtsOfContours = [3]
    glyph1.flags = array.array("B", [1, 1, 1, 1])
    glyph1.coordinates = GlyphCoordinates([(0, 0), (1, 1), (2, 2), (3, 3)])

    glyph2 = Glyph()
    glyph2.numberOfContours = 1
    glyph2.endPtsOfContours = [3]
    glyph2.flags = array.array("B", [0, 0, 0, 0])
    glyph2.coordinates = GlyphCoordinates([(0, 0), (1, 1), (2, 2), (3, 3)])

    with pytest.raises(ValueError, match="Incompatible flags"):
        dropImpliedOnCurvePoints(glyph1, glyph2)


def test_dropImpliedOnCurvePoints_incompatible_endPtsOfContours():
    glyph1 = Glyph()
    glyph1.numberOfContours = 2
    glyph1.endPtsOfContours = [2, 6]
    glyph1.flags = array.array("B", [1, 1, 1, 1, 1, 1, 1])
    glyph1.coordinates = GlyphCoordinates([(i, i) for i in range(7)])

    glyph2 = Glyph()
    glyph2.numberOfContours = 2
    glyph2.endPtsOfContours = [3, 6]
    glyph2.flags = array.array("B", [1, 1, 1, 1, 1, 1, 1])
    glyph2.coordinates = GlyphCoordinates([(i, i) for i in range(7)])

    with pytest.raises(ValueError, match="Incompatible endPtsOfContours"):
        dropImpliedOnCurvePoints(glyph1, glyph2)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
