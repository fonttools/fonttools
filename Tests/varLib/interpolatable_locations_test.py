import sys
import pytest

from fontTools.misc.fixedTools import floatToFixed
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import builder
from fontTools.varLib.avar.map import map as map_forward
from fontTools.varLib.interpolatableHelpers import LocationLabeler


@pytest.fixture
def avar2_font():
    font = TTFont()
    font["fvar"] = newTable("fvar")
    for tag, triple, hidden in (
        ("wght", (100, 400, 900), False),
        ("GRAD", (-250, 0, 150), False),
        ("XOPQ", (0, 0, 1), True),
    ):
        axis = Axis()
        axis.axisTag = tag
        axis.minValue, axis.defaultValue, axis.maxValue = triple
        axis.flags = int(hidden)
        font["fvar"].axes.append(axis)
    avar = font["avar"] = newTable("avar")
    avar.majorVersion = 2
    avar.segments = {a.axisTag: {-1: -1, 0: 0, 1: 1} for a in font["fvar"].axes}
    avar.table = otTables.avar()
    avar.table.VarIdxMap = None
    avar.table.VarStore = builder.buildVarStore(
        builder.buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "GRAD", "XOPQ"]),
        [builder.buildVarData([0], [[0], [0], [16384]])],
    )
    return font


def labeler(font):
    return LocationLabeler(
        {a.axisTag: {-1: -1, 0: 0, 1: 1} for a in font["fvar"].axes}, font=font
    )


def test_reachable_input_keeps_normalized_location(avar2_font):
    pytest.importorskip("scipy")
    labels = labeler(avar2_font)({"GRAD": -1})
    assert labels == (
        "normalized: GRAD=-1.0",
        "input: GRAD=-250.0",
    )


@pytest.mark.parametrize("location", [{"XOPQ": 1}, {"wght": 0.5}])
def test_unreachable_input_shows_only_actual_coordinates(avar2_font, location):
    pytest.importorskip("scipy")
    # XOPQ's output equals wght's: neither of these isolated peaks is reachable.
    # In particular, omitting XOPQ must constrain it to zero, rather than
    # allowing reverse() to report an apparent exact inverse for wght alone.
    labels = labeler(avar2_font)(location)
    assert len(labels) == 1
    assert labels[0].startswith("normalized: ")
    assert "approx" not in labels[0]
    assert "error" not in labels[0]


def test_labels_cache_complete_targets(avar2_font, monkeypatch):
    pytest.importorskip("scipy")
    from fontTools.varLib.avar import reverse as module

    original = module.reverse
    calls = []

    def recording_reverse(font, location, **kwargs):
        calls.append(location)
        return original(font, location, **kwargs)

    monkeypatch.setattr(module, "reverse", recording_reverse)
    formatter = labeler(avar2_font)
    first = formatter({"wght": 0.5, "XOPQ": 0.5})
    assert first == formatter({"XOPQ": 0.5, "wght": 0.5, "GRAD": 0})
    assert len(calls) == 1
    assert calls[0] == {"wght": 0.5, "GRAD": 0, "XOPQ": 0.5}
    assert first == (
        "normalized: XOPQ=0.5 wght=0.5",
        "input: wght=650.0",
    )


def test_pretty_input_is_verified(avar2_font):
    pytest.importorskip("scipy")
    avar = avar2_font["avar"]
    avar.table.VarStore.VarData[0].Item = [[0], [0], [0]]
    avar.segments["wght"] = {-1: -1, 0: 0, 1 / 1024: 0.9, 1: 1}
    labels = labeler(avar2_font)({"wght": 0.6})
    assert len(labels) == 2
    inputs = {
        tag: float(value)
        for tag, value in (
            item.split("=") for item in labels[1][len("input: ") :].split()
        )
    }
    actual = map_forward(avar2_font, inputs, outputNormalized=True)
    assert abs(actual["wght"] - 0.6) <= 1 / 16384
    # Shortening this solution to 400.33 would move the output by ~0.008.
    assert inputs["wght"] != 400.33


def test_no_scipy_keeps_internal_locations(avar2_font, monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.optimize", None)
    formatter = labeler(avar2_font)
    assert formatter({"GRAD": -1}) == ("normalized: GRAD=-1.0",)
    assert formatter({"XOPQ": 1}) == ("normalized: XOPQ=1.0",)
    assert formatter.reverse_unavailable


def test_midpoint_half_f2dot14_unit_is_preserved():
    formatter = LocationLabeler({"wght": {-1: -1, 0: 0, 1: 1}})
    text = formatter({"wght": 1 / 32768})[0]
    displayed = float(text.split("=")[1])
    assert floatToFixed(displayed, 15) == 1


def test_simple_mapping_and_discrete_zero():
    formatter = LocationLabeler(
        {"Weight": {-1: 100, 0: 400, 1: 900}}, discrete_axes={"Style"}
    )
    assert formatter({"Weight": 0.5, "Style": 0}) == (
        "normalized: Style=0.0 Weight=0.5",
        "design: Style=0.0 Weight=650.0",
    )


def test_zero_location_is_explicit():
    formatter = LocationLabeler({"wght": {-1: 100, 0: 400, 1: 900}})
    assert formatter({"wght": 0}) == ("normalized: all zero", "design: default")


def test_midway_label_does_not_change_outline_blend():
    pytest.importorskip("cairo")
    from fontTools.ttLib.ttGlyphSet import LerpGlyphSet
    from fontTools.varLib.interpolatablePlot import InterpolatablePlot

    class RecordingPlot(InterpolatablePlot):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.labels = []
            self.midway = None

        def draw_label(self, label, **kwargs):
            self.labels.append(label)

        def draw_glyph(self, glyphset, glyphname, problems, which, **kwargs):
            if isinstance(glyphset, LerpGlyphSet):
                self.midway = glyphset
            return 1

        def draw_emoticon(self, *args, **kwargs):
            pass

    glyphsets = [{"A": object()}, {"A": object()}]
    plot = RecordingPlot(
        None,
        glyphsets,
        names=["Regular", "Bold"],
        locations=[{}, {"wght": 1}],
        location_labeler=LocationLabeler({"wght": {-1: 100, 0: 400, 1: 900}}),
    )
    plot.add_problem(
        "A",
        {"type": "underweight", "master_1_idx": 0, "master_2_idx": 1},
    )
    assert "nominal midway" in plot.labels
    assert "normalized: wght=0.5" in plot.labels
    assert "design: wght=650.0" in plot.labels
    assert plot.midway.glyphset1 is glyphsets[0]
    assert plot.midway.glyphset2 is glyphsets[1]
    assert plot.midway.factor == 0.5
