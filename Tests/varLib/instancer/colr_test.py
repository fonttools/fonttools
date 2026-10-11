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


@pytest.mark.parametrize("format", [17, 19, 21, 23])
@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("center", [37, 30000, -32768])
def test_scale_outside_f2dot14_becomes_transform(font, format, sign, center):
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
    dx = dy = 0
    depth = 0
    while paint.Format == ot.PaintFormat.PaintTransform:
        matrix = paint.Transform
        assert matrix.xy == matrix.yx == 0
        dx += xx * matrix.dx
        dy += yy * matrix.dy
        xx *= matrix.xx
        yy *= matrix.yy
        paint = paint.Paint
        depth += 1
        assert depth <= 5
    assert paint.Format == ot.PaintFormat.PaintSolid
    assert xx == yy == sign * 2.5
    cx, cy = (center, -29) if format in (19, 23) else (0, 0)
    assert (dx, dy) == (cx * (1 - sign * 2.5), cy * (1 - sign * 2.5))


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
