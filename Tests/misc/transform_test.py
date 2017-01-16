from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.transform import Transform, Identity, Offset, Scale
import math
import pytest


class TransformTest(object):

    def test_examples(self):
        t = Transform()
        assert repr(t) == "<Transform [1 0 0 1 0 0]>"
        assert t.scale(2) == Transform(2, 0, 0, 2, 0, 0)
        assert t.scale(2.5, 5.5) == Transform(2.5, 0, 0, 5.5, 0, 0)
        assert t.scale(2, 3).transformPoint((100, 100)) == (200, 300)

    def test__init__(self):
        assert Transform(12) == Transform(12, 0, 0, 1, 0, 0)
        assert Transform(dx=12) == Transform(1, 0, 0, 1, 12, 0)
        assert Transform(yx=12) == Transform(1, 0, 12, 1, 0, 0)

    def test_transformPoints(self):
        t = Transform(2, 0, 0, 3, 0, 0)
        assert t.transformPoints(
            [(0, 0), (0, 100), (100, 100), (100, 0)]
        ) == [(0, 0), (0, 300), (200, 300), (200, 0)]

    def test_translate(self):
        t = Transform()
        assert t.translate(20, 30) == Transform(1, 0, 0, 1, 20, 30)

    def test_scale(self):
        t = Transform()
        assert t.scale(5) == Transform(5, 0, 0, 5, 0, 0)
        assert t.scale(5, 6) == Transform(5, 0, 0, 6, 0, 0)

    def test_rotate(self):
        t = Transform()
        assert t.rotate(math.pi / 2) == Transform(0, 1, -1, 0, 0, 0)
        t = Transform()
        assert t.rotate(-math.pi / 2) == Transform(0, -1, 1, 0, 0, 0)
        t = Transform()
        assert tuple(t.rotate(math.radians(30))) == pytest.approx(
            tuple(Transform(0.866025, 0.5, -0.5, 0.866025, 0, 0)))

    def test_skew(self):
        t = Transform().skew(math.pi / 4)
        assert tuple(t) == pytest.approx(tuple(Transform(1, 0, 1, 1, 0, 0)))

    def test_transform(self):
        t = Transform(2, 0, 0, 3, 1, 6)
        assert t.transform((4, 3, 2, 1, 5, 6)) == Transform(8, 9, 4, 3, 11, 24)

    def test_reverseTransform(self):
        t = Transform(2, 0, 0, 3, 1, 6)
        reverse_t = t.reverseTransform((4, 3, 2, 1, 5, 6))
        assert reverse_t == Transform(8, 6, 6, 3, 21, 15)
        t = Transform(4, 3, 2, 1, 5, 6)
        reverse_t = t.transform((2, 0, 0, 3, 1, 6))
        assert reverse_t == Transform(8, 6, 6, 3, 21, 15)

    def test_inverse(self):
        t = Transform().translate(2, 3).scale(4, 5)
        assert t.transformPoint((10, 20)) == (42, 103)
        it = t.inverse()
        assert it.transformPoint((42, 103)) == (10.0, 20.0)
        assert Transform().inverse() == Transform()

    def test_toPS(self):
        t = Transform().scale(2, 3).translate(4, 5)
        assert t.toPS() == '[2 0 0 3 8 15]'

    def test__ne__(self):
        assert Transform() != Transform(2, 0, 0, 2, 0, 0)

    def test__hash__(self):
        t = Transform(12, 0, 0, 13, 0, 0)
        d = {t: None}
        assert t in d.keys()

    def test__bool__(self):
        assert not bool(Transform())
        assert Transform(2, 0, 0, 2, 0, 0)
        assert Transform(1, 0, 0, 1, 1, 0)

    def test__repr__(self):
        assert repr(Transform(1, 2, 3, 4, 5, 6)) == '<Transform [1 2 3 4 5 6]>'

    def test_Identity(self):
        assert isinstance(Identity, Transform)
        assert Identity == Transform(1, 0, 0, 1, 0, 0)

    def test_Offset(self):
        assert Offset() == Transform(1, 0, 0, 1, 0, 0)
        assert Offset(1) == Transform(1, 0, 0, 1, 1, 0)
        assert Offset(1, 2) == Transform(1, 0, 0, 1, 1, 2)

    def test_Scale(self):
        assert Scale(1) == Transform(1, 0, 0, 1, 0, 0)
        assert Scale(2) == Transform(2, 0, 0, 2, 0, 0)
        assert Scale(1, 2) == Transform(1, 0, 0, 2, 0, 0)
