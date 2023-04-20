from fontTools.misc.transform import (
    Transform,
    Identity,
    Offset,
    Scale,
    DecomposedTransform,
)
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
        assert t.transformPoints([(0, 0), (0, 100), (100, 100), (100, 0)]) == [
            (0, 0),
            (0, 300),
            (200, 300),
            (200, 0),
        ]

    def test_transformVector(self):
        t = Transform(2, 0, 0, 3, -10, 30)
        assert t.transformVector((-4, 5)) == (-8, 15)

    def test_transformVectors(self):
        t = Transform(2, 0, 0, 3, -10, 30)
        assert t.transformVectors([(-4, 5), (-6, 7)]) == [(-8, 15), (-12, 21)]

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
            tuple(Transform(0.866025, 0.5, -0.5, 0.866025, 0, 0))
        )

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
        assert t.toPS() == "[2 0 0 3 8 15]"

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
        assert repr(Transform(1, 2, 3, 4, 5, 6)) == "<Transform [1 2 3 4 5 6]>"

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

    def test_decompose(self):
        t = Transform(2, 0, 0, 3, 5, 7)
        d = t.toDecomposed()
        assert d.scaleX == 2
        assert d.scaleY == 3
        assert d.translateX == 5
        assert d.translateY == 7

    def test_decompose(self):
        t = Transform(-1, 0, 0, 1, 0, 0)
        d = t.toDecomposed()
        assert d.scaleX == -1
        assert d.scaleY == 1
        assert d.rotation == 0

        t = Transform(1, 0, 0, -1, 0, 0)
        d = t.toDecomposed()
        assert d.scaleX == 1
        assert d.scaleY == -1
        assert d.rotation == 0


class DecomposedTransformTest(object):
    def test_identity(self):
        t = DecomposedTransform()
        assert (
            repr(t)
            == "DecomposedTransform(translateX=0, translateY=0, rotation=0, scaleX=1, scaleY=1, skewX=0, skewY=0, tCenterX=0, tCenterY=0)"
        )
        assert t == DecomposedTransform(scaleX=1.0)

    def test_scale(self):
        t = DecomposedTransform(scaleX=2, scaleY=3)
        assert t.scaleX == 2
        assert t.scaleY == 3

    def test_toTransform(self):
        t = DecomposedTransform(scaleX=2, scaleY=3)
        assert t.toTransform() == (2, 0, 0, 3, 0, 0)

    @pytest.mark.parametrize(
        "decomposed",
        [
            DecomposedTransform(scaleX=1, scaleY=0),
            DecomposedTransform(scaleX=0, scaleY=1),
            DecomposedTransform(scaleX=1, scaleY=0, rotation=30),
            DecomposedTransform(scaleX=0, scaleY=1, rotation=30),
            DecomposedTransform(scaleX=1, scaleY=1),
            DecomposedTransform(scaleX=-1, scaleY=1),
            DecomposedTransform(scaleX=1, scaleY=-1),
            DecomposedTransform(scaleX=-1, scaleY=-1),
            DecomposedTransform(rotation=90),
            DecomposedTransform(rotation=-90),
            DecomposedTransform(skewX=45),
            DecomposedTransform(skewY=45),
            DecomposedTransform(scaleX=-1, skewX=45),
            DecomposedTransform(scaleX=-1, skewY=45),
            DecomposedTransform(scaleY=-1, skewX=45),
            DecomposedTransform(scaleY=-1, skewY=45),
            DecomposedTransform(scaleX=-1, skewX=45, rotation=30),
            DecomposedTransform(scaleX=-1, skewY=45, rotation=30),
            DecomposedTransform(scaleY=-1, skewX=45, rotation=30),
            DecomposedTransform(scaleY=-1, skewY=45, rotation=30),
            DecomposedTransform(scaleX=-1, skewX=45, rotation=-30),
            DecomposedTransform(scaleX=-1, skewY=45, rotation=-30),
            DecomposedTransform(scaleY=-1, skewX=45, rotation=-30),
            DecomposedTransform(scaleY=-1, skewY=45, rotation=-30),
            DecomposedTransform(scaleX=-2, skewX=45, rotation=30),
            DecomposedTransform(scaleX=-2, skewY=45, rotation=30),
            DecomposedTransform(scaleY=-2, skewX=45, rotation=30),
            DecomposedTransform(scaleY=-2, skewY=45, rotation=30),
            DecomposedTransform(scaleX=-2, skewX=45, rotation=-30),
            DecomposedTransform(scaleX=-2, skewY=45, rotation=-30),
            DecomposedTransform(scaleY=-2, skewX=45, rotation=-30),
            DecomposedTransform(scaleY=-2, skewY=45, rotation=-30),
        ],
    )
    def test_roundtrip(lst, decomposed):
        assert decomposed.toTransform().toDecomposed().toTransform() == pytest.approx(
            tuple(decomposed.toTransform())
        ), decomposed
