from io import BytesIO
from pathlib import Path

import pytest

from fontTools.colorLib.builder import buildCOLR
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.builder import (
    buildDeltaSetIndexMap,
    buildVarData,
    buildVarRegionList,
    buildVarStore,
)
from fontTools.varLib.instancer import instantiateVariableFont


@pytest.fixture
def font():
    font = TTFont()
    font.importXML(Path(__file__).parent / "data" / "COLRv1-alpha.ttx")
    return font


def roundtrip(font):
    stream = BytesIO()
    font.save(stream)
    stream.seek(0)
    return TTFont(stream)


def instance(font, limits):
    return roundtrip(instantiateVariableFont(font, limits, overlap=False))


def paints(font):
    return [p.Paint for p in font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord]


@pytest.mark.parametrize("weight,width,alpha", [(900, 100, 1), (650, 125, 0.5)])
def test_full_instance_clamps_solid_and_gradient_alpha(font, weight, width, alpha):
    result = instance(font, {"wght": weight, "wdth": width})
    assert "fvar" not in result
    colr = result["COLR"].table
    assert colr.VarStore is None
    assert colr.VarIndexMap is None
    first, second, gradient = paints(result)
    assert first.Format == second.Format == ot.PaintFormat.PaintSolid
    assert first.Alpha == alpha
    assert second.Alpha == 0
    assert gradient.Format == ot.PaintFormat.PaintLinearGradient
    assert type(gradient.ColorLine) is ot.ColorLine
    assert [s.Alpha for s in gradient.ColorLine.ColorStop] == [alpha, 0]
    assert all(type(s) is ot.ColorStop for s in gradient.ColorLine.ColorStop)


def test_partial_and_composed_instances(font):
    partial = instance(font, {"wght": 650})
    first, second, gradient = paints(partial)
    assert first.Format == second.Format == ot.PaintFormat.PaintVarSolid
    assert first.Alpha == 1.5
    assert second.Alpha == -1.5
    assert gradient.ColorLine.ColorStop[0].Alpha == 1.5
    assert partial["COLR"].table.VarStore.VarRegionList.RegionAxisCount == 1
    assert [a.axisTag for a in partial["fvar"].axes] == ["wdth"]
    composed = instance(partial, {"wdth": 125})
    direct = instance(font, {"wght": 650, "wdth": 125})
    assert composed.getTableData("COLR") == direct.getTableData("COLR")


@pytest.mark.parametrize("split_store", [False, True])
@pytest.mark.parametrize("move_default", [False, True])
def test_optimizes_mapped_partial_store(font, split_store, move_default):
    colr = font["COLR"].table
    mapping = list(range(6))
    if split_store:
        # Reverse the rows and split them across two outer indices. The map
        # restores their original meanings, including consecutive stop fields.
        rows = list(reversed(colr.VarStore.VarData[0].Item))
        colr.VarStore.VarData = [
            buildVarData([0, 1], rows[:3]),
            buildVarData([0, 1], rows[3:]),
        ]
        colr.VarStore.VarDataCount = 2
        mapping = [0x10002, 0x10001, 0x10000, 2, 1, 0]
    colr.VarIndexMap = buildDeltaSetIndexMap(mapping + [ot.NO_VARIATION_INDEX])
    partial = instance(font, {"wght": (400, 650, 900) if move_default else 650})
    table = partial["COLR"].table
    # Duplicate and zero rows are removed, while the mapping slots stay intact.
    assert sum(data.ItemCount for data in table.VarStore.VarData) == (
        2 if move_default else 1
    )
    mapping = table.VarIndexMap.mapping
    assert len(mapping) == 7
    assert mapping[0] == mapping[3] != ot.NO_VARIATION_INDEX
    assert mapping[1] == mapping[5]
    assert mapping[2] == mapping[4] == mapping[6] == ot.NO_VARIATION_INDEX
    first, second, gradient = paints(partial)
    assert (first.VarIndexBase, second.VarIndexBase) == (0, 1)
    assert [s.VarIndexBase for s in gradient.ColorLine.ColorStop] == [2, 4]
    assert gradient.VarIndexBase == ot.NO_VARIATION_INDEX
    for weight in ((400, 650, 900) if move_default else (650,)):
        for width in (75, 100, 125):
            limits = {"wdth": width}
            if move_default:
                limits["wght"] = weight
            composed = instance(partial, limits)
            direct = instance(font, {"wght": weight, "wdth": width})
            assert composed.getTableData("COLR") == direct.getTableData("COLR")


@pytest.mark.parametrize("empty_map", [False, True])
def test_partial_implicit_mapping_preserves_consecutive_rows(font, empty_map):
    if empty_map:
        mapping = ot.DeltaSetIndexMap()
        mapping.mapping = []
        font["COLR"].table.VarIndexMap = mapping
    partial = instance(font, {"wght": 650})
    assert partial["COLR"].table.VarStore.VarData[0].ItemCount == 6
    for width in (75, 100, 125):
        composed = instance(partial, {"wdth": width})
        direct = instance(font, {"wght": 650, "wdth": width})
        assert composed.getTableData("COLR") == direct.getTableData("COLR")


@pytest.mark.parametrize(
    "mapping", [[3], [ot.NO_VARIATION_INDEX, 3], [3, ot.NO_VARIATION_INDEX]]
)
def test_optimized_short_map_repeats_last_entry(font, mapping):
    font["COLR"].table.VarIndexMap = buildDeltaSetIndexMap(mapping)
    paints(font)[0].VarIndexBase = 3
    partial = instance(font, {"wght": 650})
    table = partial["COLR"].table
    assert sum(data.ItemCount for data in table.VarStore.VarData) == 1
    assert table.VarIndexMap.mapping == [
        0 if index == 3 else ot.NO_VARIATION_INDEX for index in mapping
    ]
    for width in (75, 100, 125):
        composed = instance(partial, {"wdth": width})
        direct = instance(font, {"wght": 650, "wdth": width})
        assert composed.getTableData("COLR") == direct.getTableData("COLR")


def test_moved_default_and_axis_range(font):
    result = instance(font, {"wght": (400, 650, 900)})
    assert paints(result)[0].Alpha == 1.5
    assert result["COLR"].table.VarStore.VarRegionList.RegionAxisCount == 2
    for weight in (400, 650, 900):
        actual = instance(result, {"wght": weight, "wdth": 125})
        expected = instance(font, {"wght": weight, "wdth": 125})
        assert actual.getTableData("COLR") == expected.getTableData("COLR")


@pytest.mark.parametrize("mapping", [None, [], [0], [ot.NO_VARIATION_INDEX]])
def test_implicit_empty_short_and_sentinel_maps(font, mapping):
    table = font["COLR"].table
    first = paints(font)[0]
    first.VarIndexBase = ot.NO_VARIATION_INDEX if mapping is None else 3
    table.VarIndexMap = None if mapping is None else buildDeltaSetIndexMap(mapping)
    # Other fields may address later mapping entries, which repeat the last.
    result = instance(font, {"wght": 650})
    assert paints(result)[0].Alpha == (1.5 if mapping in ([], [0]) else 1)
    assert result["COLR"].table.VarStore.VarRegionList.RegionAxisCount == 1


def test_layer_paints_transforms_angles_and_clips(font):
    region_list = buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"])
    rows = [
        [d]
        for d in [
            32768,
            0,
            0,
            0,
            65536,
            -65536,
            1,
            -1,
            3,
            -3,
            5,
            -5,
            8192,
            0,
            100,
            -100,
        ]
    ]
    store = buildVarStore(region_list, [buildVarData([0], rows)])
    solid = dict(Format=ot.PaintFormat.PaintSolid, PaletteIndex=0, Alpha=1)
    color_line = dict(
        Extend="pad",
        ColorStop=[
            dict(
                StopOffset=0,
                PaletteIndex=0,
                Alpha=1,
                VarIndexBase=ot.NO_VARIATION_INDEX,
            )
        ],
    )
    transform = dict(
        Format=ot.PaintFormat.PaintVarTransform,
        Paint=solid,
        Transform=dict(xx=1, yx=0, xy=0, yy=1, dx=0, dy=0, VarIndexBase=0),
    )
    linear = dict(
        Format=ot.PaintFormat.PaintVarLinearGradient,
        ColorLine=color_line,
        x0=0,
        y0=0,
        x1=100,
        y1=100,
        x2=200,
        y2=200,
        VarIndexBase=6,
    )
    rotate = dict(
        Format=ot.PaintFormat.PaintVarRotate, Paint=solid, angle=270, VarIndexBase=12
    )
    sweep = dict(
        Format=ot.PaintFormat.PaintVarSweepGradient,
        ColorLine=color_line,
        centerX=100,
        centerY=100,
        startAngle=0,
        endAngle=90,
        VarIndexBase=ot.NO_VARIATION_INDEX,
    )
    layers = dict(
        Format=ot.PaintFormat.PaintColrLayers, Layers=[transform, linear, rotate, sweep]
    )
    font["COLR"] = buildCOLR(
        {"a": layers},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
        clipBoxes={"a": (0, 0, 400, 700, 12)},
    )
    result = instance(roundtrip(font), {"wght": 900, "wdth": 100})
    table = result["COLR"].table
    transform, linear, rotate, sweep = table.LayerList.Paint
    assert transform.Format == ot.PaintFormat.PaintTransform
    assert type(transform.Transform) is ot.Affine2x3
    assert (transform.Transform.xx, transform.Transform.dx, transform.Transform.dy) == (
        1.5,
        1,
        -1,
    )
    assert linear.Format == ot.PaintFormat.PaintLinearGradient
    assert (linear.x0, linear.y0, linear.x1, linear.y1, linear.x2, linear.y2) == (
        1,
        -1,
        103,
        97,
        205,
        195,
    )
    assert rotate.Format == ot.PaintFormat.PaintRotate
    assert rotate.angle == -360
    assert sweep.Format == ot.PaintFormat.PaintSweepGradient
    assert (sweep.startAngle, sweep.endAngle) == (0, 90)
    clip = table.ClipList.clips["a"]
    assert clip.Format == 1
    assert (clip.xMin, clip.yMin, clip.xMax, clip.yMax) == (8192, 0, 500, 600)


def test_shared_paints_are_instanced_once(font):
    first = paints(font)[0]
    font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord[1].Paint = first
    partial = instantiateVariableFont(font, {"wght": 650}, overlap=False)
    assert paints(partial)[0] is paints(partial)[1]
    assert paints(partial)[0].Alpha == 1.5


def test_constant_store_becomes_static_with_an_axis_remaining(font):
    for data in font["COLR"].table.VarStore.VarData:
        for row in data.Item:
            row[1] = 0
    result = instance(font, {"wght": 650})
    assert [a.axisTag for a in result["fvar"].axes] == ["wdth"]
    assert result["COLR"].table.VarStore is None
    assert all(p.Format in (2, 4) for p in paints(result))


@pytest.mark.parametrize("format", [17, 19, 21, 23])
@pytest.mark.parametrize("sign", [1, -1])
def test_scale_outside_f2dot14_becomes_transform(font, format, sign):
    regions = buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"])
    store = buildVarStore(
        regions, [buildVarData([0], [[sign * 16384]] * 2 + [[0]] * 2)]
    )
    paint = dict(
        Format=format,
        Paint=dict(Format=ot.PaintFormat.PaintSolid, PaletteIndex=0, Alpha=1),
        VarIndexBase=0,
    )
    if format in (21, 23):
        paint["scale"] = sign * 1.5
    else:
        paint["scaleX"] = paint["scaleY"] = sign * 1.5
    if format in (19, 23):
        paint["centerX"], paint["centerY"] = 37, -29
        if format == 23:
            store.VarData[0].Item[1][0] = 0
    font["COLR"] = buildCOLR(
        {"a": paint}, version=1, glyphMap=font.getReverseGlyphMap(), varStore=store
    )
    result = instance(roundtrip(font), {"wght": 900, "wdth": 100})
    paint = paints(result)[0]
    assert paint.Format == ot.PaintFormat.PaintTransform
    matrix = paint.Transform
    assert matrix.xx == matrix.yy == sign * 2.5
    assert matrix.xy == matrix.yx == 0
    cx, cy = (37, -29) if format in (19, 23) else (0, 0)
    assert (matrix.dx, matrix.dy) == (cx * (1 - sign * 2.5), cy * (1 - sign * 2.5))


def _radial_alpha(paint, x, y):
    from math import sqrt

    if paint.Format == ot.PaintFormat.PaintSolid:
        return None if paint.Alpha == 0 else paint.Alpha
    dx, dy, dr = paint.x1 - paint.x0, paint.y1 - paint.y0, paint.r1 - paint.r0
    px, py = x - paint.x0, y - paint.y0
    a = dx * dx + dy * dy - dr * dr
    b = -2 * (px * dx + py * dy + paint.r0 * dr)
    c = px * px + py * py - paint.r0 * paint.r0
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    roots = [(-b - sqrt(discriminant)) / (2 * a), (-b + sqrt(discriminant)) / (2 * a)]
    roots = [root for root in roots if paint.r0 + root * dr >= -1e-8]
    if not roots:
        return None
    t = max(roots)
    stops = sorted(paint.ColorLine.ColorStop, key=lambda stop: stop.StopOffset)
    first, last = stops[0].StopOffset, stops[-1].StopOffset
    width = last - first
    if paint.ColorLine.Extend == ot.ExtendMode.REPEAT:
        t = first + (t - first) % width
    elif paint.ColorLine.Extend == ot.ExtendMode.REFLECT:
        q = (t - first) % (2 * width)
        t = first + (q if q <= width else 2 * width - q)
    if t < first:
        return stops[0].Alpha
    for left, right in zip(stops, stops[1:]):
        if t < right.StopOffset:
            q = (t - left.StopOffset) / (right.StopOffset - left.StopOffset)
            return left.Alpha + q * (right.Alpha - left.Alpha)
    return stops[-1].Alpha


def _negative_radial_font(font, radii, extend, middle=0.5):
    line = dict(
        Extend=extend,
        ColorStop=[
            dict(
                StopOffset=offset,
                PaletteIndex=0,
                Alpha=alpha,
                VarIndexBase=ot.NO_VARIATION_INDEX,
            )
            for offset, alpha in [(0, 0.25), (middle, 0.5), (1, 1)]
        ],
    )
    paint = dict(
        Format=7,
        ColorLine=line,
        x0=10,
        y0=15,
        r0=100,
        x1=410,
        y1=215,
        r1=100,
        VarIndexBase=0,
    )
    rows = [[0], [0], [radii[0] - 100], [0], [0], [radii[1] - 100]]
    font["COLR"] = buildCOLR(
        {"a": paint},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=buildVarStore(
            buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
            [buildVarData([0], rows)],
        ),
    )
    return roundtrip(font)


@pytest.mark.parametrize(
    "radii", [(-100, 500), (500, -100), (-100, -200), (-200, -100), (-100, -100)]
)
@pytest.mark.parametrize("extend", ["pad", "repeat", "reflect"])
@pytest.mark.parametrize("unordered", [False, True])
def test_full_negative_radial_preserves_geometry_and_color_line(
    font, radii, extend, unordered
):
    from copy import deepcopy

    font = _negative_radial_font(font, radii, extend)
    if unordered:
        stops = paints(font)[0].ColorLine.ColorStop
        stops[:] = [stops[2], stops[0], stops[1]]
    expected = deepcopy(paints(font)[0])
    expected.r0, expected.r1 = radii
    result = instance(font, {"wght": 900, "wdth": 100})
    actual = paints(result)[0]
    assert result["COLR"].table.VarStore is None
    if actual.Format == ot.PaintFormat.PaintRadialGradient:
        assert actual.r0 >= 0 and actual.r1 >= 0
    else:
        assert radii[0] == radii[1]
        assert actual.Format == ot.PaintFormat.PaintSolid and actual.Alpha == 0
    for x in (-2000, -1000, -200, 0, 100, 400, 800, 1500):
        for y in (-1200, -100, 0, 100, 300, 1500):
            value = _radial_alpha(expected, x, y)
            if value is None:
                assert _radial_alpha(actual, x, y) is None
            else:
                assert _radial_alpha(actual, x, y) == pytest.approx(value)
    for pinned in ("wght", "wdth"):
        limits = {"wght": 900, "wdth": 100}
        partial = instance(font, {pinned: limits.pop(pinned)})
        composed = instance(partial, limits)
        assert composed.getTableData("COLR") == result.getTableData("COLR")


def test_full_negative_radial_preserves_fractional_stop_precision(font):
    radii = (500, -100)
    font = _negative_radial_font(font, radii, "pad", middle=1 / 16384)
    result = instance(font, {"wght": 900, "wdth": 100})
    paint = paints(result)[0]
    assert (paint.r0, paint.r1) == (650, 50)
    assert [stop.StopOffset for stop in paint.ColorLine.ColorStop] == [
        0.25,
        0.25 + 1 / 16384,
        1.25,
    ]
    from copy import deepcopy

    expected = deepcopy(paints(font)[0])
    expected.r0, expected.r1 = radii
    for x in (-200, 0, 100, 400, 800):
        for y in (-100, 0, 300):
            value = _radial_alpha(expected, x, y)
            if value is None:
                assert _radial_alpha(paint, x, y) is None
            else:
                assert _radial_alpha(paint, x, y) == pytest.approx(value)

    for pinned in ("wght", "wdth"):
        limits = {"wght": 900, "wdth": 100}
        partial = instance(font, {pinned: limits.pop(pinned)})
        composed = instance(partial, limits)
        assert composed.getTableData("COLR") == result.getTableData("COLR")


def test_negative_radial_keeps_shared_color_lines_unchanged(font):
    from copy import deepcopy

    font = _negative_radial_font(font, (-100, 500), "pad")
    original = paints(font)[0]
    other = deepcopy(original)
    other.VarIndexBase = ot.NO_VARIATION_INDEX
    other.ColorLine = original.ColorLine
    record = ot.BaseGlyphPaintRecord()
    record.BaseGlyph, record.Paint = "b", other
    font["COLR"].table.BaseGlyphList.BaseGlyphPaintRecord.append(record)
    negative, unchanged = paints(instance(font, {"wght": 900, "wdth": 100}))
    assert [s.StopOffset for s in negative.ColorLine.ColorStop] == [-1, -0.5, 0]
    assert [s.StopOffset for s in unchanged.ColorLine.ColorStop] == [0, 0.5, 1]


@pytest.mark.parametrize(
    "deltas", [(-1, -1, 1, 1), (1, 1, -1, -1), (1, -1, 1, -1), (-1, 1, -1, 1)]
)
@pytest.mark.parametrize("weight", [400, 525, 650, 775, 900])
def test_clip_edges_round_outward_in_full_and_composed_instances(font, deltas, weight):
    from math import floor, ceil

    store = buildVarStore(
        buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
        [buildVarData([0], [[delta] for delta in deltas])],
    )
    font["COLR"] = buildCOLR(
        {"a": dict(Format=2, PaletteIndex=0, Alpha=1)},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
        clipBoxes={"a": (50, 50, 500, 500, 0)},
    )
    font = roundtrip(font)
    scalar = (weight - 400) / 500
    expected = tuple(
        (floor if i < 2 else ceil)(base + scalar * delta)
        for i, (base, delta) in enumerate(zip((50, 50, 500, 500), deltas))
    )
    for partial_limits, final_limits in [
        ({}, {"wght": weight, "wdth": 100}),
        ({"wght": weight}, {"wdth": 100}),
        ({"wdth": 100}, {"wght": weight}),
    ]:
        partial = instance(font, partial_limits) if partial_limits else font
        result = instance(partial, final_limits)
        clip = result["COLR"].table.ClipList.clips["a"]
        assert clip.Format == 1
        assert (clip.xMin, clip.yMin, clip.xMax, clip.yMax) == expected
