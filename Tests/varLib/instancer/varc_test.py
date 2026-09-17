from io import BytesIO
from pathlib import Path

import pytest

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib import builder
from fontTools.varLib.instancer import instantiateVariableFont


def _condition(format, **fields):
    result = otTables.ConditionTable()
    result.Format = format
    result.__dict__.update(fields)
    return result


@pytest.fixture(params=[False, True], ids=["no-avar", "avar2"])
def varc_font(request):
    # Based on HarfBuzz's generate-varc-instancing-fonts.py fixture: an unrelated
    # leading axis, a condition-only axis, and component-internal variations.
    path = Path(__file__).parents[2] / "ttLib" / "data" / "varc-ac01-conditional.ttf"
    font = TTFont(path, recalcTimestamp=False)
    variations = font["gvar"].variations  # Load before changing the axis order.
    for tag in reversed(("DUMY", "COND")):
        axis = Axis()
        axis.axisTag = tag
        axis.minValue, axis.defaultValue, axis.maxValue = -1, 0, 1
        axis.axisNameID = font["fvar"].axes[0].axisNameID
        font["fvar"].axes.insert(0, axis)

    varc = font["VARC"].table
    varc.AxisIndicesList.Item = [
        [i + 2 for i in indices] for indices in varc.AxisIndicesList.Item
    ]
    for region in varc.MultiVarStore.SparseVarRegionList.Region:
        for axis in region.SparseVarRegionAxis:
            axis.AxisIndex += 2

    weight = varc.ConditionList.ConditionTable[0]
    weight.AxisIndex += 2
    middle = _condition(
        1, AxisIndex=1, FilterRangeMinValue=0.25, FilterRangeMaxValue=0.5
    )
    high = _condition(1, AxisIndex=1, FilterRangeMinValue=0.5, FilterRangeMaxValue=1)
    either = _condition(4, ConditionTable=[middle, high])
    varc.ConditionList.ConditionTable[0] = _condition(
        3, ConditionTable=[weight, either]
    )

    name = "glyph00003"
    points = len(font["glyf"][name].getCoordinates(font["glyf"])[0])
    variations[name].extend(
        [
            TupleVariation({"DUMY": (0, 1, 1)}, [(20, 0)] * points + [(0, 0)] * 4),
            TupleVariation(
                {"0000": (-1, -0.5, -0.25)}, [(0, 20)] * points + [(0, 0)] * 4
            ),
        ]
    )
    if request.param:
        for axis in font["fvar"].axes:
            if axis.axisTag.startswith("000"):
                axis.flags = 1
        avar = font["avar"] = newTable("avar")
        avar.majorVersion, avar.minorVersion = 2, 0
        avar.segments = {a.axisTag: {-1: -1, 0: 0, 1: 1} for a in font["fvar"].axes}
        avar.table = otTables.avar()
        avar.table.VarIdxMap = None
        avar.table.VarStore = None
    return _roundtrip(font)


def _roundtrip(font):
    stream = BytesIO()
    font.save(stream)
    stream.seek(0)
    return TTFont(stream)


def _draw(font, location):
    glyphs = font.getGlyphSet(location=location)
    pen = DecomposingRecordingPen(glyphs)
    glyphs["uniAC01"].draw(pen)
    return pen.value


@pytest.mark.parametrize("limit", [0.5, (0, 0.5, 1)])
def test_instance_unrelated_axis(varc_font, limit):
    result = _roundtrip(instantiateVariableFont(varc_font, {"DUMY": limit}))
    assert "VARC" in result
    assert len(result["fvar"].axes) == (9 if limit == 0.5 else 10)
    if limit != 0.5:
        axis = result["fvar"].axes[0]
        assert (axis.minValue, axis.defaultValue, axis.maxValue) == limit

    for sample in range(8):
        location = {
            "DUMY": 1 if limit != 0.5 and sample & 1 else 0.5,
            "wght": 840.3 if sample & 2 else 356.5,
            "opsz": 1 if sample & 1 else 0,
            "COND": 1 if sample & 4 else 0,
        }
        expected = _draw(varc_font, location)
        actual = _draw(result, location)
        assert expected
        assert len(actual) == len(expected)
        for (actual_op, actual_points), (expected_op, expected_points) in zip(
            actual, expected
        ):
            assert actual_op == expected_op
            assert len(actual_points) == len(expected_points)
            for actual_point, expected_point in zip(actual_points, expected_points):
                # Instancing expands and rounds inferred gvar deltas.
                assert actual_point == pytest.approx(expected_point, abs=0.5)


@pytest.mark.parametrize("tag", ["wght", "opsz", "0000", "COND"])
@pytest.mark.parametrize("restrict_range", [False, True], ids=["pin", "restrict"])
def test_reject_referenced_axis(varc_font, tag, restrict_range):
    axis = next(a for a in varc_font["fvar"].axes if a.axisTag == tag)
    limit = axis.defaultValue
    if restrict_range:
        limit = (
            axis.minValue,
            axis.defaultValue,
            (axis.defaultValue + axis.maxValue) / 2,
        )
    with pytest.raises(
        NotImplementedError, match="Instancing across VarComponent axes"
    ):
        instantiateVariableFont(varc_font, {tag: limit})


def test_reject_full_instance(varc_font):
    with pytest.raises(
        NotImplementedError, match="Instancing across VarComponent axes"
    ):
        instantiateVariableFont(varc_font, {}, static=True)


def test_nested_conditions(varc_font):
    location = {"wght": 840.3, "COND": 0}
    before = _draw(varc_font, location)
    location["COND"] = 1
    assert _draw(varc_font, location) != before


def test_remap_negated_condition(varc_font):
    conditions = varc_font["VARC"].table.ConditionList.ConditionTable
    conditions[0] = _condition(5, ConditionTable=conditions[0])
    result = _roundtrip(instantiateVariableFont(varc_font, {"DUMY": 0.5}))
    negated = result["VARC"].table.ConditionList.ConditionTable[0]
    assert negated.Format == 5
    weight, either = negated.ConditionTable.ConditionTable
    axes = result["fvar"].axes
    assert axes[weight.AxisIndex].axisTag == "wght"
    assert [axes[c.AxisIndex].axisTag for c in either.ConditionTable] == [
        "COND",
        "COND",
    ]


@pytest.mark.parametrize("varc_font", [True], indirect=True, ids=["avar2"])
def test_avar2_preserves_component_internal_variation(varc_font):
    # Drive hidden axis 0000 from DUMY through avar2. A hidden axis has no
    # identity term, so its font-level reachable range is just the delta range,
    # here [0, 1]. A VARC component still overrides 0000 to about -0.54 and
    # therefore reaches the negative gvar tuple added by the fixture.
    axes = varc_font["fvar"].axes
    axis_tags = [axis.axisTag for axis in axes]
    region_list = builder.buildVarRegionList([{"DUMY": (0, 1, 1)}], axis_tags)
    var_data = builder.buildVarData([0], [[16384]], optimize=False)
    avar = varc_font["avar"]
    avar.table.VarStore = builder.buildVarStore(region_list, [var_data])
    mapping = [otTables.NO_VARIATION_INDEX] * len(axes)
    mapping[axis_tags.index("0000")] = 0
    avar.table.VarIdxMap = builder.buildDeltaSetIndexMap(mapping)
    varc_font = _roundtrip(varc_font)

    location = {"DUMY": 0, "wght": 356.5, "opsz": 0, "COND": 0}
    expected = _draw(varc_font, location)
    assert expected
    # DUMY already has this full range, so this instancing request is a no-op.
    result = _roundtrip(instantiateVariableFont(varc_font, {"DUMY": (-1, 0, 1)}))
    actual = _draw(result, location)

    assert any(
        variation.axes.get("0000") == (-1, -0.5, -0.25)
        for variation in result["gvar"].variations["glyph00003"]
    )
    assert len(actual) == len(expected)
    for (actual_op, actual_points), (expected_op, expected_points) in zip(
        actual, expected
    ):
        assert actual_op == expected_op
        assert len(actual_points) == len(expected_points)
        for actual_point, expected_point in zip(actual_points, expected_points):
            assert actual_point == pytest.approx(expected_point, abs=0.5)
