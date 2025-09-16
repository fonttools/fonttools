from fontTools.feaLib.variableScalar import VariableScalar


def test_variable_scalar_repr():
    scalar = VariableScalar()
    scalar.add_value({"wght": 400}, 1)
    scalar.add_value({"wght": 500.5}, 4)
    scalar.add_value({"wght": 700}, 10)

    assert str(scalar) == "(wght=400:1 wght=500.5:4 wght=700:10)"
