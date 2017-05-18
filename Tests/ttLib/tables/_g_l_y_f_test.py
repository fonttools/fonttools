from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
import sys
import pytest


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
        assert g2 == GlyphCoordinates([(-2,2)])

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
        assert g[0][0] == round(afloat)
