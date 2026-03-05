from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor
from fontTools.feaLib.variableScalar import VariableScalar, VariableScalarBuilder
from fontTools.varLib.models import VariationModel


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


def test_model_uses_axes_order():
    """VariableScalarBuilder.model() should use the axis order from
    axis_triples, not the default alphabetical order, to ensure consistent
    deltas regardless of axis tag sorting."""

    builder = VariableScalarBuilder(
        axis_triples={
            "wght": (100, 400, 900),
            "wdth": (62.5, 100, 100),
        },
        axis_mappings={},
        model_cache={},
    )

    scalar = VariableScalar()
    scalar.add_value({"wght": 100, "wdth": 100}, 151)
    scalar.add_value({"wght": 400, "wdth": 100}, 176)
    scalar.add_value({"wght": 900, "wdth": 100}, 221)
    scalar.add_value({"wght": 100, "wdth": 62.5}, 98)
    scalar.add_value({"wght": 400, "wdth": 62.5}, 111)
    scalar.add_value({"wght": 900, "wdth": 62.5}, 161)
    scalar.add_value({"wght": 705, "wdth": 62.5}, 136)

    # Build a reference model with explicit axisOrder matching builder axis order
    full_values = builder.normalised_values(scalar)
    locations = [dict(loc) for loc in full_values.keys()]
    ref_model = VariationModel(locations, axisOrder=["wght", "wdth"])
    ref_deltas, ref_supports = ref_model.getDeltasAndSupports(
        list(scalar.values.values()), round=round
    )

    # VariableScalarBuilder.model() should produce the same deltas
    deltas, supports = builder.get_deltas_and_supports(scalar)

    assert deltas == ref_deltas
    assert supports == ref_supports
