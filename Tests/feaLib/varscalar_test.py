import pytest

from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.ttLib.tables._f_v_a_r import Axis


@pytest.fixture
def axes():
    wght = Axis()
    wght.minValue = 200
    wght.defaultValue = 400
    wght.maxValue = 800
    wght.axisTag = "wght"

    return [wght]


def test_interpolate(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)
    assert v.value_at_location({"wght": 400}) == 10
    assert v.value_at_location({"wght": 500}) == 12.5
    assert v.value_at_location({"wght": 800}) == 20


def test_add(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)

    v = v + 30
    assert v.value_at_location({"wght": 400}) == 40
    assert v.value_at_location({"wght": 500}) == 42.5
    assert v.value_at_location({"wght": 800}) == 50


def test_sub(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)

    v = v - 30
    assert v.value_at_location({"wght": 400}) == -20
    assert v.value_at_location({"wght": 500}) == -17.5
    assert v.value_at_location({"wght": 800}) == -10


def test_add_varscalar(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)

    v2 = VariableScalar()
    v2.axes = axes
    v2.add_value({"wght": 400}, 30)
    v2.add_value({"wght": 800}, 80)

    v = v + v2

    assert v.value_at_location({"wght": 400}) == 40
    assert v.value_at_location({"wght": 500}) == 55
    assert v.value_at_location({"wght": 800}) == 100


def test_mul(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)

    v = v * 3
    assert v.value_at_location({"wght": 400}) == 30
    assert v.value_at_location({"wght": 500}) == 37.5
    assert v.value_at_location({"wght": 800}) == 60


def test_neg(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, 20)

    v = -v
    assert v.value_at_location({"wght": 400}) == -10
    assert v.value_at_location({"wght": 500}) == -12.5
    assert v.value_at_location({"wght": 800}) == -20


def test_abs(axes):
    v = VariableScalar()
    v.axes = axes
    v.add_value({"wght": 400}, 10)
    v.add_value({"wght": 800}, -20)

    v = abs(v)
    assert v.value_at_location({"wght": 400}) == 10
    assert v.value_at_location({"wght": 500}) == 12.5
    assert v.value_at_location({"wght": 800}) == 20
