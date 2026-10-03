from collections import OrderedDict
from io import BytesIO

import pytest

from fontTools.designspaceLib import (
    AxisDescriptor,
    AxisMappingDescriptor,
    DesignSpaceDocument,
    RuleDescriptor,
    SourceDescriptor,
    evaluateConditions,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import _add_avar, build, load_designspace, models
from fontTools.varLib.errors import VarLibValidationError
from fontTools.varLib.instancer import instantiateVariableFont


def make_axis():
    return AxisDescriptor(
        name="Optical size",
        tag="opsz",
        minimum=0,
        default=50,
        maximum=100,
        map=[(0, 100), (25, 80), (50, 40), (75, 10), (100, 0)],
    )


def make_master(width):
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder([".notdef", "a", "a.alt"])
    builder.setupCharacterMap({0x61: "a"})
    glyphs = {}
    for name in (".notdef", "a", "a.alt"):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((width - 100, 0))
        pen.lineTo((width - 100, 700))
        pen.lineTo((0, 700))
        pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (width, 0) for name in glyphs})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Reversed", "styleName": "Regular"})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200)
    builder.setupPost()
    return builder.font


def make_designspace(axis):
    document = DesignSpaceDocument()
    document.addAxis(axis)
    for _, value in axis.map:
        source = SourceDescriptor()
        source.location = {axis.name: value}
        source.font = make_master(value * 10 + 500)
        document.addSource(source)
    return document


def reload_font(font):
    stream = BytesIO()
    font.save(stream)
    return TTFont(BytesIO(stream.getvalue()))


@pytest.mark.parametrize(
    "minimum,default,maximum,mapping,expected",
    [
        (0, 50, 100, [(0, 100), (25, 80), (50, 40), (100, 0)], [-1, -2 / 3, 0, 1]),
        (
            9,
            144,
            144,
            [(9, 38), (42, 33), (72, 28), (144, 23)],
            [-1, -2 / 3, -1 / 3, 0],
        ),
        (0, 0, 100, [(0, 100), (25, 80), (100, 0)], [0, 0.2, 1]),
        (0, 50, 100, [(0, 0), (25, 10), (50, 40), (100, 100)], [-1, -0.75, 0, 1]),
    ],
)
def test_master_normalization_preserves_user_axis_direction(
    minimum, default, maximum, mapping, expected
):
    axis = make_axis()
    axis.minimum, axis.default, axis.maximum = minimum, default, maximum
    axis.map = mapping
    document = make_designspace(axis)
    document.addAxis(
        AxisDescriptor(name="Weight", tag="wght", minimum=0, default=0, maximum=1)
    )
    for source, value in zip(document.sources, expected):
        source.location["Weight"] = 0 if value == 0 else 0.5

    data = load_designspace(document)

    assert [loc[axis.name] for loc in data.normalized_master_locs] == pytest.approx(
        expected
    )
    assert [loc["Weight"] for loc in data.normalized_master_locs] == [
        0 if value == 0 else 0.5 for value in expected
    ]
    assert axis.map == mapping


def test_reversed_axis_avar_is_increasing_and_retains_plateau():
    axis = make_axis()
    axis.map.insert(2, (35, 80))
    original_map = list(axis.map)

    avar = _add_avar(TTFont(), OrderedDict([(axis.name, axis)]), [], [axis.tag])

    assert avar.segments[axis.tag] == pytest.approx(
        {-1: -1, -0.5: -2 / 3, -0.3: -2 / 3, 0: 0, 0.5: 0.75, 1: 1}
    )
    assert axis.map == original_map


@pytest.mark.parametrize(
    "mapping",
    [
        [(0, 100), (25, 20), (50, 40), (100, 0)],
        [(0, 0), (25, 80), (50, 40), (100, 100)],
    ],
)
def test_nonmonotonic_axis_map_is_rejected(mapping):
    axis = make_axis()
    axis.map = mapping
    with pytest.raises(VarLibValidationError):
        _add_avar(TTFont(), OrderedDict([(axis.name, axis)]), [], [axis.tag])


def test_reversed_axis_build_and_interpolation():
    document = make_designspace(make_axis())
    font, _, _ = build(document)
    font = reload_font(font)

    axis = font["fvar"].axes[0]
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (0, 50, 100)
    for user_value, width in [
        (0, 1500),
        (25, 1300),
        (50, 900),
        (62.5, 750),
        (75, 600),
        (100, 500),
    ]:
        instance = instantiateVariableFont(font, {"opsz": user_value})
        assert instance["hmtx"].metrics["a"][0] == width
        assert instance["glyf"]["a"].xMax == width - 100


@pytest.mark.parametrize(
    "reversed_axis,minimum,maximum,expected",
    [
        (True, 20, 80, (-2 / 3, 0.5)),
        (True, None, 80, (-2 / 3, 1)),
        (True, 20, None, (-1, 0.5)),
        (False, 20, 80, (-0.5, 2 / 3)),
        (False, None, 80, (-1, 2 / 3)),
        (False, 20, None, (-0.5, 1)),
    ],
)
def test_feature_variation_bounds_follow_design_axis_direction(
    reversed_axis, minimum, maximum, expected
):
    axis = make_axis()
    if not reversed_axis:
        axis.map = [(0, 0), (25, 10), (50, 40), (75, 80), (100, 100)]
    document = make_designspace(axis)
    rule = RuleDescriptor()
    rule.conditionSets = [[{"name": axis.name, "minimum": minimum, "maximum": maximum}]]
    rule.subs = [("a", "a.alt")]
    document.addRule(rule)

    font, _, _ = build(document)
    font = reload_font(font)
    records = font["GSUB"].table.FeatureVariations.FeatureVariationRecord
    assert len(records) == 1
    condition = records[0].ConditionSet.ConditionTable[0]
    assert condition.AxisIndex == 0
    bounds = condition.FilterRangeMinValue, condition.FilterRangeMaxValue
    assert bounds == pytest.approx(expected, abs=1 / 16384)
    samples = (
        [(95, -11 / 12), (65, -5 / 12), (40, 0), (5, 0.875)]
        if reversed_axis
        else [(5, -0.875), (30, -0.25), (60, 1 / 3), (95, 11 / 12)]
    )
    for design_value, normalized_value in samples:
        assert (bounds[0] <= normalized_value <= bounds[1]) == evaluateConditions(
            rule.conditionSets[0], {axis.name: design_value}
        )


@pytest.mark.parametrize("reversed_axis", [False, True])
def test_invalid_feature_variation_bounds_are_not_sorted(reversed_axis):
    axis = make_axis()
    if not reversed_axis:
        axis.map = [(0, 0), (50, 40), (100, 100)]
    document = make_designspace(axis)
    rule = RuleDescriptor()
    rule.conditionSets = [[{"name": axis.name, "minimum": 80, "maximum": 20}]]
    rule.subs = [("a", "a.alt")]
    document.addRule(rule)
    with pytest.raises(VarLibValidationError):
        build(document)


def test_reversed_axis_avar2_mapping_uses_user_axis_direction():
    axis = make_axis()
    document = make_designspace(axis)
    document.axisMappings = [
        AxisMappingDescriptor(
            inputLocation={axis.name: 80}, outputLocation={axis.name: 70}
        ),
        AxisMappingDescriptor(
            inputLocation={axis.name: 10}, outputLocation={axis.name: 20}
        ),
    ]

    font, _, _ = build(document)
    font = reload_font(font)
    assert font["avar"].majorVersion == 2
    for normalized_input, expected in [(-0.5, -0.5), (0, 0), (0.5, 0.5)]:
        result = font["avar"].renormalizeLocation(
            {"opsz": normalized_input}, font, dropZeroes=False
        )
        assert result["opsz"] == pytest.approx(expected, abs=1 / 16384)


def test_generic_normalize_value_still_rejects_reversed_triple():
    with pytest.raises(ValueError):
        models.normalizeValue(80, (100, 40, 0))
