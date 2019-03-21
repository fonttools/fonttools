from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import otRound
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable, TTLibError
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables import ttProgram
import sys
import array
import pytest
import re
import os
import unittest


class GlyphCoordinatesTest(object):

    def test_translate(self):
        g = GlyphCoordinates([(1,2)])
        g.translate((.5,0))
        assert g == GlyphCoordinates([(1.5,2.0)])

    def test_scale(self):
        g = GlyphCoordinates([(1,2)])
        g.scale((.5,0))
        assert g == GlyphCoordinates([(0.5,0.0)])

    def test_transform(self):
        g = GlyphCoordinates([(1,2)])
        g.transform(((.5,0),(.2,.5)))
        assert g[0] == GlyphCoordinates([(0.9,1.0)])[0]

    def test__eq__(self):
        g = GlyphCoordinates([(1,2)])
        g2 = GlyphCoordinates([(1.0,2)])
        g3 = GlyphCoordinates([(1.5,2)])
        assert g == g2
        assert not g == g3
        assert not g2 == g3
        assert not g == object()

    def test__ne__(self):
        g = GlyphCoordinates([(1,2)])
        g2 = GlyphCoordinates([(1.0,2)])
        g3 = GlyphCoordinates([(1.5,2)])
        assert not (g != g2)
        assert g != g3
        assert g2 != g3
        assert g != object()

    def test__pos__(self):
        g = GlyphCoordinates([(1,2)])
        g2 = +g
        assert g == g2

    def test__neg__(self):
        g = GlyphCoordinates([(1,2)])
        g2 = -g
        assert g2 == GlyphCoordinates([(-1, -2)])

    @pytest.mark.skipif(sys.version_info[0] < 3,
                        reason="__round___ requires Python 3")
    def test__round__(self):
        g = GlyphCoordinates([(-1.5,2)])
        g2 = round(g)
        assert g2 == GlyphCoordinates([(-1,2)])

    def test__add__(self):
        g1 = GlyphCoordinates([(1,2)])
        g2 = GlyphCoordinates([(3,4)])
        g3 = GlyphCoordinates([(4,6)])
        assert g1 + g2 == g3
        assert g1 + (1, 1) == GlyphCoordinates([(2,3)])
        with pytest.raises(TypeError) as excinfo:
            assert g1 + object()
        assert 'unsupported operand' in str(excinfo.value)

    def test__sub__(self):
        g1 = GlyphCoordinates([(1,2)])
        g2 = GlyphCoordinates([(3,4)])
        g3 = GlyphCoordinates([(-2,-2)])
        assert g1 - g2 == g3
        assert g1 - (1, 1) == GlyphCoordinates([(0,1)])
        with pytest.raises(TypeError) as excinfo:
            assert g1 - object()
        assert 'unsupported operand' in str(excinfo.value)

    def test__rsub__(self):
        g = GlyphCoordinates([(1,2)])
        # other + (-self)
        assert (1, 1) - g == GlyphCoordinates([(0,-1)])

    def test__mul__(self):
        g = GlyphCoordinates([(1,2)])
        assert g * 3 == GlyphCoordinates([(3,6)])
        assert g * (3,2) == GlyphCoordinates([(3,4)])
        assert g * (1,1) == g
        with pytest.raises(TypeError) as excinfo:
            assert g * object()
        assert 'unsupported operand' in str(excinfo.value)

    def test__truediv__(self):
        g = GlyphCoordinates([(1,2)])
        assert g / 2 == GlyphCoordinates([(.5,1)])
        assert g / (1, 2) == GlyphCoordinates([(1,1)])
        assert g / (1, 1) == g
        with pytest.raises(TypeError) as excinfo:
            assert g / object()
        assert 'unsupported operand' in str(excinfo.value)

    def test__iadd__(self):
        g = GlyphCoordinates([(1,2)])
        g += (.5,0)
        assert g == GlyphCoordinates([(1.5, 2.0)])
        g2 = GlyphCoordinates([(3,4)])
        g += g2
        assert g == GlyphCoordinates([(4.5, 6.0)])

    def test__isub__(self):
        g = GlyphCoordinates([(1,2)])
        g -= (.5, 0)
        assert g == GlyphCoordinates([(0.5, 2.0)])
        g2 = GlyphCoordinates([(3,4)])
        g -= g2
        assert g == GlyphCoordinates([(-2.5, -2.0)])

    def __test__imul__(self):
        g = GlyphCoordinates([(1,2)])
        g *= (2,.5)
        g *= 2
        assert g == GlyphCoordinates([(4.0, 2.0)])
        g = GlyphCoordinates([(1,2)])
        g *= 2
        assert g == GlyphCoordinates([(2, 4)])

    def test__itruediv__(self):
        g = GlyphCoordinates([(1,3)])
        g /= (.5,1.5)
        g /= 2
        assert g == GlyphCoordinates([(1.0, 1.0)])

    def test__bool__(self):
        g = GlyphCoordinates([])
        assert bool(g) == False
        g = GlyphCoordinates([(0,0), (0.,0)])
        assert bool(g) == True
        g = GlyphCoordinates([(0,0), (1,0)])
        assert bool(g) == True
        g = GlyphCoordinates([(0,.5), (0,0)])
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
        g = GlyphCoordinates([(1, 1)], typecode="h")
        g.append((0x8000, 0))
        assert g.array.typecode == "d"
        assert g.array == array.array("d", [1.0, 1.0, 32768.0, 0.0])


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, 'data')

GLYF_TTX = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.ttx")
GLYF_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.glyf.bin")
HEAD_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.head.bin")
LOCA_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.loca.bin")
MAXP_BIN = os.path.join(DATA_DIR, "_g_l_y_f_outline_flag_bit6.maxp.bin")


def strip_ttLibVersion(string):
    return re.sub(' ttLibVersion=".*"', '', string)


class glyfTableTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    @classmethod
    def setUpClass(cls):
        with open(GLYF_BIN, 'rb') as f:
            cls.glyfData = f.read()
        with open(HEAD_BIN, 'rb') as f:
            cls.headData = f.read()
        with open(LOCA_BIN, 'rb') as f:
            cls.locaData = f.read()
        with open(MAXP_BIN, 'rb') as f:
            cls.maxpData = f.read()
        with open(GLYF_TTX, 'r') as f:
            cls.glyfXML = strip_ttLibVersion(f.read()).splitlines()

    def test_toXML(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        glyfTable = font['glyf'] = newTable('glyf')
        font['head'] = newTable('head')
        font['loca'] = newTable('loca')
        font['maxp'] = newTable('maxp')
        font['maxp'].decompile(self.maxpData, font)
        font['head'].decompile(self.headData, font)
        font['loca'].decompile(self.locaData, font)
        glyfTable.decompile(self.glyfData, font)
        out = UnicodeIO()
        font.saveXML(out)
        glyfXML = strip_ttLibVersion(out.getvalue()).splitlines()
        self.assertEqual(glyfXML, self.glyfXML)

    def test_fromXML(self):
        font = TTFont(sfntVersion="\x00\x01\x00\x00")
        font.importXML(GLYF_TTX)
        glyfTable = font['glyf']
        glyfData = glyfTable.compile(font)
        self.assertEqual(glyfData, self.glyfData)

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
        with self.assertRaisesRegex(TTLibError, "glyph '.' contains a recursive component reference"):
            glyph_A.getCoordinates(glyphSet)

    def test_trim_remove_hinting_composite_glyph(self):
        glyphSet = {"dummy": TTGlyphPen(None).glyph()}

        pen = TTGlyphPen(glyphSet)
        pen.addComponent("dummy", (1, 0, 0, 1, 0, 0))
        composite = pen.glyph()
        p = ttProgram.Program()
        p.fromAssembly(['SVTCA[0]'])
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


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
