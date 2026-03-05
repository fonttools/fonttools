import warnings
from types import SimpleNamespace

from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor
from fontTools.feaLib.variableScalar import VariableScalar, VariableScalarBuilder
from fontTools.varLib.varStore import OnlineVarStoreBuilder
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


def test_deprecated_add_to_variation_store():
    """The deprecated VariableScalar.add_to_variation_store() shim should
    produce the same result as going through VariableScalarBuilder, while
    emitting a DeprecationWarning.

    This is the pattern used by babelfont + fontFeatures:
    https://github.com/simoncozens/babelfont/blob/3.1.3/src/babelfont/Font.py#L205-L206
    https://github.com/simoncozens/fontFeatures/blob/v1.9.0/Lib/fontFeatures/ttLib/Routine.py#L46
    """
    axes = [
        SimpleNamespace(axisTag="wght", minValue=100, defaultValue=400, maxValue=900),
        SimpleNamespace(axisTag="wdth", minValue=75, defaultValue=100, maxValue=125),
    ]

    scalar = VariableScalar()
    scalar.axes = axes
    scalar.add_value({"wght": 100, "wdth": 100}, 10)
    scalar.add_value({"wght": 400, "wdth": 100}, 20)
    scalar.add_value({"wght": 900, "wdth": 100}, 40)

    # Use the deprecated shim (like fontFeatures does)
    store_builder = OnlineVarStoreBuilder([ax.axisTag for ax in axes])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        default, index = scalar.add_to_variation_store(store_builder)
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()

    assert default == 20
    assert index is not None

    # Compare with the new API
    builder = VariableScalarBuilder(
        axis_triples={ax.axisTag: (ax.minValue, ax.defaultValue, ax.maxValue) for ax in axes},
        axis_mappings={},
        model_cache={},
    )
    store_builder2 = OnlineVarStoreBuilder([ax.axisTag for ax in axes])
    default2, index2 = builder.add_to_variation_store(scalar, store_builder2)

    assert default == default2
    assert index == index2
