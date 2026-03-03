from types import SimpleNamespace

from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.varLib.models import VariationModel


def test_variable_scalar_repr():
    scalar = VariableScalar()
    scalar.add_value({"wght": 400}, 1)
    scalar.add_value({"wght": 500.5}, 4)
    scalar.add_value({"wght": 700}, 10)

    assert str(scalar) == "(wght=400:1 wght=500.5:4 wght=700:10)"


def test_model_uses_axes_order():
    """VariableScalar.model() should use the axis order from self.axes,
    not the default alphabetical order, to ensure consistent deltas
    regardless of axis tag sorting."""
    axes = [
        SimpleNamespace(axisTag="wght", minValue=100, defaultValue=400, maxValue=900),
        SimpleNamespace(axisTag="wdth", minValue=62.5, defaultValue=100, maxValue=100),
    ]

    scalar = VariableScalar()
    scalar.axes = axes
    scalar.add_value({"wght": 100, "wdth": 100}, 151)
    scalar.add_value({"wght": 400, "wdth": 100}, 176)
    scalar.add_value({"wght": 900, "wdth": 100}, 221)
    scalar.add_value({"wght": 100, "wdth": 62.5}, 98)
    scalar.add_value({"wght": 400, "wdth": 62.5}, 111)
    scalar.add_value({"wght": 900, "wdth": 62.5}, 161)
    scalar.add_value({"wght": 705, "wdth": 62.5}, 136)

    # Build a reference model with explicit axisOrder matching self.axes
    locations = [dict(scalar._normalized_location(k)) for k in scalar.values.keys()]
    ref_model = VariationModel(locations, axisOrder=["wght", "wdth"])
    ref_deltas, ref_supports = ref_model.getDeltasAndSupports(
        list(scalar.values.values()), round=round
    )

    # VariableScalar.model() should produce the same deltas
    deltas, supports = scalar.get_deltas_and_supports()

    assert deltas == ref_deltas
    assert supports == ref_supports
