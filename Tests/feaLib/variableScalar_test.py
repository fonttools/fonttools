from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor
from fontTools.feaLib.variableScalar import VariableScalar, VariableScalarBuilder


def test_variable_scalar_repr():
    scalar = VariableScalar()
    scalar.add_value({"wght": 400}, 1)
    scalar.add_value({"wght": 500.5}, 4)
    scalar.add_value({"wght": 700}, 10)

    assert str(scalar) == "(wght=400:1 wght=500.5:4 wght=700:10)"


def test_variable_scalar_interpolation():
    """Test interpolation of a single value, and construction of a builder from
    a designspace."""

    # Add some values at locations in design coordinates.
    scalar = VariableScalar()
    scalar.add_value({"wght": 100}, 1)
    scalar.add_value({"wght": 400}, 4)
    scalar.add_value({"wght": 900}, 9)

    # Describe two axes, with only one used explicitly.
    doc = DesignSpaceDocument()
    doc.addAxis(
        AxisDescriptor(
            tag="wght",
            minimum=100,
            default=400,
            maximum=900,
            map=[
                (1, 100),
                (400, 400),
                (900, 1000),
            ],
        )
    )
    doc.addAxis(
        AxisDescriptor(
            tag="opsz",
            minimum=1,
            default=12,
            maximum=72,
        )
    )

    # Construct a builder from the designspace.
    builder = VariableScalarBuilder.from_designspace(doc)
    value = builder.value_at_location(scalar, (("wght", 200),))

    # The interpolation should have survived the translation from
    # user-coordinates to design-coordinates and back again.
    assert value == 2.0
