import math
import pytest
from fontTools.misc.arrayTools import Vector as ArrayVector
from fontTools.misc.vector import Vector


def test_Vector():
    v = Vector((100, 200))
    assert repr(v) == "Vector((100, 200))"
    assert v == Vector((100, 200))
    assert v == Vector([100, 200])
    assert v == (100, 200)
    assert (100, 200) == v
    assert v == [100, 200]
    assert [100, 200] == v
    assert v is Vector(v)
    assert v + 10 == (110, 210)
    assert 10 + v == (110, 210)
    assert v + Vector((1, 2)) == (101, 202)
    assert v - Vector((1, 2)) == (99, 198)
    assert v * 2 == (200, 400)
    assert 2 * v == (200, 400)
    assert v * 0.5 == (50, 100)
    assert v / 2 == (50, 100)
    assert 2 / v == (0.02, 0.01)
    v = Vector((3, 4))
    assert abs(v) == 5  # length
    assert v.length() == 5
    assert v.normalized() == Vector((0.6, 0.8))
    assert abs(Vector((1, 1, 1))) == math.sqrt(3)
    assert bool(Vector((0, 0, 1)))
    assert not bool(Vector((0, 0, 0)))
    v1 = Vector((2, 3))
    v2 = Vector((3, 4))
    assert v1.dot(v2) == 18
    v = Vector((2, 4))
    assert round(v / 3) == (1, 1)
    with pytest.raises(
        AttributeError,
        match="'Vector' object has no attribute 'newAttr'",
    ):
        v.newAttr = 12


def test_deprecated():
    with pytest.warns(
        DeprecationWarning,
        match="fontTools.misc.arrayTools.Vector has been deprecated",
    ):
        ArrayVector((1, 2))
    with pytest.warns(
        DeprecationWarning,
        match="the 'keep' argument has been deprecated",
    ):
        Vector((1, 2), keep=True)
    v = Vector((1, 2))
    with pytest.warns(
        DeprecationWarning,
        match="the 'toInt' method has been deprecated",
    ):
        v.toInt()
    with pytest.warns(
        DeprecationWarning,
        match="the 'values' attribute has been deprecated",
    ):
        v.values
    with pytest.raises(
        AttributeError,
        match="the 'values' attribute has been deprecated",
    ):
        v.values = [12, 23]
