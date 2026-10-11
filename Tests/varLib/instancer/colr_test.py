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
from fontTools.varLib.varStore import VarStoreInstancer


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


@pytest.mark.parametrize("explicit_map", [False, True])
def test_partial_overflow_keeps_unbounded_alpha_in_the_store(font, explicit_map):
    colr = font["COLR"].table
    for index in (0, 3):
        colr.VarStore.VarData[0].Item[index] = [32768, -49152]
    if explicit_map:
        colr.VarIndexMap = buildDeltaSetIndexMap(list(range(6)))
    partial = instance(font, {"wght": 900})
    store = partial["COLR"].table.VarStore
    assert store.VarRegionList.RegionAxisCount == 1
    instancer = VarStoreInstancer(store, partial["fvar"].axes, {})
    assert paints(partial)[0].Alpha + instancer[0] / 16384 == 3
    assert any(
        all(a.StartCoord == a.PeakCoord == a.EndCoord == 0 for a in r.VarRegionAxis)
        for r in store.VarRegionList.Region
    )
    for width in (100, 112.5, 118.75, 125):
        composed = instance(partial, {"wdth": width})
        direct = instance(font, {"wght": 900, "wdth": width})
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


@pytest.mark.parametrize("delta", [16384, 2147483647])
@pytest.mark.parametrize("format", [17, 19, 21, 23])
@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("center", [37, 30000, -32768])
def test_scale_outside_f2dot14_becomes_transform(font, format, sign, center, delta):
    regions = buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"])
    store = buildVarStore(
        regions, [buildVarData([0], [[sign * delta]] * 2 + [[0]] * 2)]
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
        paint["centerX"], paint["centerY"] = center, -29
        if format == 23:
            store.VarData[0].Item[1][0] = 0
    font["COLR"] = buildCOLR(
        {"a": paint}, version=1, glyphMap=font.getReverseGlyphMap(), varStore=store
    )
    result = instance(roundtrip(font), {"wght": 900, "wdth": 100})
    paint = paints(result)[0]
    assert paint.Format == ot.PaintFormat.PaintTransform
    xx = yy = 1
    xy = yx = dx = dy = 0
    depth = 0
    while paint.Format == ot.PaintFormat.PaintTransform:
        matrix = paint.Transform
        dx, dy = (
            dx + xx * matrix.dx + xy * matrix.dy,
            dy + yx * matrix.dx + yy * matrix.dy,
        )
        xx, xy, yx, yy = (
            xx * matrix.xx + xy * matrix.yx,
            xx * matrix.xy + xy * matrix.yy,
            yx * matrix.xx + yy * matrix.yx,
            yx * matrix.xy + yy * matrix.yy,
        )
        paint = paint.Paint
        depth += 1
        assert depth <= 20
    assert paint.Format == ot.PaintFormat.PaintSolid
    assert xy == yx == 0
    expected = sign * (1.5 + delta / 16384)
    assert xx == yy == expected
    cx, cy = (center, -29) if format in (19, 23) else (0, 0)
    assert (dx, dy) == (cx * (1 - expected), cy * (1 - expected))


@pytest.mark.parametrize("explicit_map", [False, True])
def test_partial_scale_and_stop_overflows_and_moved_default(explicit_map):
    font = TTFont()
    font.importXML(Path(__file__).parent / "data" / "COLRv1-partial-overflow.ttx")
    if explicit_map:
        font["COLR"].table.VarIndexMap = buildDeltaSetIndexMap(list(range(4)))
    partial = instance(font, {"wght": 1})
    for width in (0.5, 0.75, 1):
        composed = instance(partial, {"wdth": width})
        direct = instance(font, {"wght": 1, "wdth": width})
        assert composed.getTableData("COLR") == direct.getTableData("COLR")
    rebased = instance(font, {"wght": (0, 0.5, 1)})
    for weight, width in ((0, 0.5), (0.5, 0.75), (1, 1)):
        limits = {"wght": weight, "wdth": width}
        assert instance(rebased, limits).getTableData("COLR") == instance(
            font, limits
        ).getTableData("COLR")


def test_constant_colr_regions_apply_at_the_default(font):
    store = buildVarStore(
        buildVarRegionList([{}], ["wght", "wdth"]), [buildVarData([0], [[32768]])]
    )
    font["COLR"] = buildCOLR(
        {"a": dict(Format=3, PaletteIndex=0, Alpha=0, VarIndexBase=0)},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
    )
    direct = instance(font, {"wght": 400, "wdth": 100})
    assert paints(direct)[0].Alpha == 1
    partial = instance(font, {"wght": 400})
    assert instance(partial, {"wdth": 100}).getTableData("COLR") == direct.getTableData(
        "COLR"
    )


@pytest.mark.parametrize("field", ["translate", "radius", "affine", "clip"])
def test_partial_overflow_of_integer_and_fixed_fields(font, field):
    rows = [[0, 0] for _ in range(6)]
    solid = dict(Format=2, PaletteIndex=0, Alpha=1)
    clips = None
    if field == "translate":
        paint = dict(Format=15, Paint=solid, dx=30000, dy=0, VarIndexBase=0)
        rows[0] = [10000, -40000]
    elif field == "radius":
        paint = dict(
            Format=7,
            ColorLine=dict(
                Extend="pad",
                ColorStop=[
                    dict(
                        StopOffset=0,
                        PaletteIndex=0,
                        Alpha=1,
                        VarIndexBase=ot.NO_VARIATION_INDEX,
                    )
                ],
            ),
            x0=0,
            y0=0,
            r0=100,
            x1=400,
            y1=0,
            r1=500,
            VarIndexBase=0,
        )
        rows[2] = [-200, 400]
    elif field == "affine":
        paint = dict(
            Format=13,
            Paint=solid,
            Transform=dict(xx=30000, yx=0, xy=0, yy=1, dx=0, dy=0, VarIndexBase=0),
        )
        rows[0] = [10000 * 65536, -30000 * 65536]
    else:
        paint = solid
        clips = {"a": (0, 0, 30000, 100, 0)}
        rows[2] = [10000, -40000]
    store = buildVarStore(
        buildVarRegionList(
            [{"wght": (0, 1, 1)}, {"wdth": (0, 1, 1)}], ["wght", "wdth"]
        ),
        [buildVarData([0, 1], rows)],
    )
    font["COLR"] = buildCOLR(
        {"a": paint},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
        clipBoxes=clips,
    )
    partial = instance(roundtrip(font), {"wght": 900})
    for width in (112.5, 118.75, 125):
        assert instance(partial, {"wdth": width}).getTableData("COLR") == instance(
            font, {"wght": 900, "wdth": width}
        ).getTableData("COLR")


def test_partial_default_sum_larger_than_a_long_delta(font):
    regions = buildVarRegionList(
        [{"wght": (0, 1, 1)}, {"wght": (0, 1, 1)}, {"wdth": (0, 1, 1)}],
        ["wght", "wdth"],
    )
    store = buildVarStore(
        regions, [buildVarData([0, 1, 2], [[2147483647, 2147483647, -2147483647]])]
    )
    font["COLR"] = buildCOLR(
        {"a": dict(Format=3, PaletteIndex=0, Alpha=1, VarIndexBase=0)},
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
    )
    partial = instance(font, {"wght": 900})
    instancer = VarStoreInstancer(
        partial["COLR"].table.VarStore, partial["fvar"].axes, {}
    )
    assert instancer[0] == 4294967294
    assert paints(instance(partial, {"wdth": 125}))[0].Alpha == 1


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("explicit_map", [False, True])
def test_rebased_long_delta_sums_keep_retained_variation(font, sign, explicit_map):
    regions = buildVarRegionList(
        [{"wght": (0, 1, 1)}] * 2 + [{"wdth": (0, 1, 1)}] * 2,
        ["wght", "wdth"],
    )
    row = [sign * 2147483647] * 2 + [-sign * 2147483647] * 2
    store = buildVarStore(regions, [buildVarData(list(range(4)), [row])])
    font["COLR"] = buildCOLR(
        {
            "a": dict(
                Format=21,
                Paint=dict(Format=2, PaletteIndex=0, Alpha=1),
                scale=1.5,
                VarIndexBase=0,
            )
        },
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
        varIndexMap=buildDeltaSetIndexMap([0]) if explicit_map else None,
    )
    for weight in (400, 900):
        partial = instance(roundtrip(font), {"wght": weight})
        width = 100 + 25 * (16383 if weight == 900 else 1) / 16384
        direct = instance(font, {"wght": weight, "wdth": width})
        composed = instance(partial, {"wdth": width})
        assert direct.getTableData("COLR") == composed.getTableData("COLR")
        assert paints(direct)[0].Transform.xx == 1.5 + sign * (
            16 if weight == 900 else -16
        )


@pytest.mark.parametrize(
    "sx,sy",
    [
        (2**32 + 1 / 16384, 1),
        (1, -(2**33 - 1 / 16384)),
        (-(2**28) + 33 / 16384, 2**30 + 3 / 16384),
        (131073 + 8191 / 16384, 0),
    ],
)
def test_large_scale_factors_survive_fixed_serialization(font, sx, sy):
    from fontTools.varLib.instancer.colr import _scaleMatrices

    paint = dict(Format=2, PaletteIndex=0, Alpha=1)
    for xx, yx, xy, yy, dx, dy in reversed(_scaleMatrices(sx, sy)):
        paint = dict(
            Format=12,
            Paint=paint,
            Transform=dict(xx=xx, yx=yx, xy=xy, yy=yy, dx=dx, dy=dy),
        )
    font["COLR"] = buildCOLR(
        {"a": paint}, version=1, glyphMap=font.getReverseGlyphMap()
    )
    paint = paints(roundtrip(font))[0]
    xx = yy = 1
    xy = yx = 0
    while paint.Format == 12:
        matrix = paint.Transform
        xx, xy, yx, yy = (
            xx * matrix.xx + xy * matrix.yx,
            xx * matrix.xy + xy * matrix.yy,
            yx * matrix.xx + yy * matrix.yx,
            yx * matrix.xy + yy * matrix.yy,
        )
        paint = paint.Paint
    assert (xx, yx, xy, yy) == (sx, 0, 0, sy)


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


def test_full_negative_radial_rejects_unrepresentable_stop_precision(font):
    font = _negative_radial_font(font, (500, -100), "pad", middle=1 / 16384)
    with pytest.raises(
        ValueError, match="negative radii cannot be represented without rounding"
    ):
        instance(font, {"wght": 900, "wdth": 100})


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


def test_negative_radial_wide_stops_use_full_unsigned_radius_range(font):
    rows = [[0], [0], [-2], [0], [0], [-1], [32769 * 16384], [0], [65534 * 16384], [0]]
    font["COLR"] = buildCOLR(
        {
            "a": dict(
                Format=7,
                x0=0,
                y0=0,
                r0=1,
                x1=0,
                y1=0,
                r1=1,
                VarIndexBase=0,
                ColorLine=dict(
                    Extend="pad",
                    ColorStop=[
                        dict(StopOffset=0, PaletteIndex=0, Alpha=0.25, VarIndexBase=6),
                        dict(StopOffset=1, PaletteIndex=0, Alpha=1, VarIndexBase=8),
                    ],
                ),
            )
        },
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=buildVarStore(
            buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
            [buildVarData([0], rows)],
        ),
    )
    result = paints(instance(roundtrip(font), {"wght": 900, "wdth": 100}))[0]
    assert result.r0 == 0 and result.r1 == 32768
    assert [stop.StopOffset for stop in result.ColorLine.ColorStop] == [
        1,
        32767 / 16384,
    ]


@pytest.mark.parametrize(
    "dx,dy",
    [
        (40000, -40000),
        (-40000, 40000),
        (2**32 + 1, -(2**32 + 3)),
        (2**46 + 3, -(2**46) + 5),
        (2**46 + 3, 0),
    ],
)
def test_large_translation_factors_roundtrip(font, dx, dy):
    from fontTools.varLib.instancer.colr import _translateMatrices, _wrapTransforms
    from fontTools.misc.transform import Transform

    child = (
        buildCOLR(
            {"a": dict(Format=2, PaletteIndex=0, Alpha=1)},
            version=1,
            glyphMap=font.getReverseGlyphMap(),
        )
        .table.BaseGlyphList.BaseGlyphPaintRecord[0]
        .Paint
    )
    root = _wrapTransforms(child, _translateMatrices(dx, dy))
    font["COLR"] = buildCOLR({"a": root}, version=1, glyphMap=font.getReverseGlyphMap())
    result = paints(roundtrip(font))[0]
    matrix, depth = Transform(), 0
    while result.Format == ot.PaintFormat.PaintTransform:
        affine = result.Transform
        matrix = matrix.transform(
            (affine.xx, affine.yx, affine.xy, affine.yy, affine.dx, affine.dy)
        )
        result = result.Paint
        depth += 1
        assert depth <= 10
    assert tuple(matrix) == (1, 0, 0, 1, dx, dy)


@pytest.mark.parametrize("explicit_map", [False, True])
@pytest.mark.parametrize("sign", [-1, 1])
def test_full_large_translate_and_both_partial_orders(font, explicit_map, sign):
    from fontTools.misc.transform import Transform

    rows = [[sign * 10000], [-sign * 10000]]
    store = buildVarStore(
        buildVarRegionList([{"wght": (0, 1, 1)}], ["wght", "wdth"]),
        [buildVarData([0], rows)],
    )
    font["COLR"] = buildCOLR(
        {
            "a": dict(
                Format=15,
                Paint=dict(Format=2, PaletteIndex=0, Alpha=1),
                dx=sign * 30000,
                dy=-sign * 30000,
                VarIndexBase=0,
            )
        },
        version=1,
        glyphMap=font.getReverseGlyphMap(),
        varStore=store,
        varIndexMap=buildDeltaSetIndexMap([0, 0, 1]) if explicit_map else None,
    )
    if explicit_map:
        paints(font)[0].VarIndexBase = 1
    font = roundtrip(font)
    for partial_limits, final_limits in [
        ({}, {"wght": 900, "wdth": 100}),
        ({"wght": 900}, {"wdth": 100}),
        ({"wdth": 100}, {"wght": 900}),
    ]:
        partial = instance(font, partial_limits) if partial_limits else font
        result = instance(partial, final_limits)
        paint = paints(result)[0]
        assert paint.Format == ot.PaintFormat.PaintTransform
        matrix = Transform()
        while paint.Format == ot.PaintFormat.PaintTransform:
            affine = paint.Transform
            matrix = matrix.transform(
                (affine.xx, affine.yx, affine.xy, affine.yy, affine.dx, affine.dy)
            )
            paint = paint.Paint
        assert tuple(matrix) == (1, 0, 0, 1, sign * 40000, -sign * 40000)
        assert result["COLR"].table.VarStore is None
