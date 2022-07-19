from copy import deepcopy
from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib import builder
from fontTools.colorLib.geometry import round_start_circle_stable_containment, Circle
from fontTools.colorLib.builder import LayerListBuilder
from fontTools.colorLib.table_builder import TableBuilder
from fontTools.colorLib.errors import ColorLibError
import pytest
from typing import List


def _build(cls, source):
    return LayerListBuilder().tableBuilder.build(cls, source)


def _buildPaint(source):
    return LayerListBuilder().buildPaint(source)


def test_buildCOLR_v0():
    color_layer_lists = {
        "a": [("a.color0", 0), ("a.color1", 1)],
        "b": [("b.color1", 1), ("b.color0", 0)],
    }

    colr = builder.buildCOLR(color_layer_lists)

    assert colr.tableTag == "COLR"
    assert colr.version == 0
    assert colr.ColorLayers["a"][0].name == "a.color0"
    assert colr.ColorLayers["a"][0].colorID == 0
    assert colr.ColorLayers["a"][1].name == "a.color1"
    assert colr.ColorLayers["a"][1].colorID == 1
    assert colr.ColorLayers["b"][0].name == "b.color1"
    assert colr.ColorLayers["b"][0].colorID == 1
    assert colr.ColorLayers["b"][1].name == "b.color0"
    assert colr.ColorLayers["b"][1].colorID == 0


def test_buildCOLR_v0_layer_as_list():
    # when COLRv0 layers are encoded as plist in UFO lib, both python tuples and
    # lists are encoded as plist array elements; but the latter are always decoded
    # as python lists, thus after roundtripping a plist tuples become lists.
    # Before FontTools 4.17.0 we were treating tuples and lists as equivalent;
    # with 4.17.0, a paint of type list is used to identify a PaintColrLayers.
    # This broke backward compatibility as ufo2ft is simply passing through the
    # color layers as read from the UFO lib plist, and as such the latter use lists
    # instead of tuples for COLRv0 layers (layerGlyph, paletteIndex) combo.
    # We restore backward compat by accepting either tuples or lists (of length 2
    # and only containing a str and an int) as individual top-level layers.
    # https://github.com/googlefonts/ufo2ft/issues/426
    color_layer_lists = {
        "a": [["a.color0", 0], ["a.color1", 1]],
        "b": [["b.color1", 1], ["b.color0", 0]],
    }

    colr = builder.buildCOLR(color_layer_lists)

    assert colr.tableTag == "COLR"
    assert colr.version == 0
    assert colr.ColorLayers["a"][0].name == "a.color0"
    assert colr.ColorLayers["a"][0].colorID == 0
    assert colr.ColorLayers["a"][1].name == "a.color1"
    assert colr.ColorLayers["a"][1].colorID == 1
    assert colr.ColorLayers["b"][0].name == "b.color1"
    assert colr.ColorLayers["b"][0].colorID == 1
    assert colr.ColorLayers["b"][1].name == "b.color0"
    assert colr.ColorLayers["b"][1].colorID == 0


def test_buildCPAL_v0():
    palettes = [
        [(0.68, 0.20, 0.32, 1.0), (0.45, 0.68, 0.21, 1.0)],
        [(0.68, 0.20, 0.32, 0.6), (0.45, 0.68, 0.21, 0.6)],
        [(0.68, 0.20, 0.32, 0.3), (0.45, 0.68, 0.21, 0.3)],
    ]

    cpal = builder.buildCPAL(palettes)

    assert cpal.tableTag == "CPAL"
    assert cpal.version == 0
    assert cpal.numPaletteEntries == 2

    assert len(cpal.palettes) == 3
    assert [tuple(c) for c in cpal.palettes[0]] == [
        (82, 51, 173, 255),
        (54, 173, 115, 255),
    ]
    assert [tuple(c) for c in cpal.palettes[1]] == [
        (82, 51, 173, 153),
        (54, 173, 115, 153),
    ]
    assert [tuple(c) for c in cpal.palettes[2]] == [
        (82, 51, 173, 76),
        (54, 173, 115, 76),
    ]


def test_buildCPAL_palettes_different_lengths():
    with pytest.raises(ColorLibError, match="have different lengths"):
        builder.buildCPAL([[(1, 1, 1, 1)], [(0, 0, 0, 1), (0.5, 0.5, 0.5, 1)]])


def test_buildPaletteLabels():
    name_table = newTable("name")
    name_table.names = []

    name_ids = builder.buildPaletteLabels(
        [None, "hi", {"en": "hello", "de": "hallo"}], name_table
    )

    assert name_ids == [0xFFFF, 256, 257]

    assert len(name_table.names) == 3
    assert str(name_table.names[0]) == "hi"
    assert name_table.names[0].nameID == 256

    assert str(name_table.names[1]) == "hallo"
    assert name_table.names[1].nameID == 257

    assert str(name_table.names[2]) == "hello"
    assert name_table.names[2].nameID == 257


def test_build_CPAL_v1_types_no_labels():
    palettes = [
        [(0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0)],
        [(0.1, 0.2, 0.3, 0.6), (0.4, 0.5, 0.6, 0.6)],
        [(0.1, 0.2, 0.3, 0.3), (0.4, 0.5, 0.6, 0.3)],
    ]
    paletteTypes = [
        builder.ColorPaletteType.USABLE_WITH_LIGHT_BACKGROUND,
        builder.ColorPaletteType.USABLE_WITH_DARK_BACKGROUND,
        builder.ColorPaletteType.USABLE_WITH_LIGHT_BACKGROUND
        | builder.ColorPaletteType.USABLE_WITH_DARK_BACKGROUND,
    ]

    cpal = builder.buildCPAL(palettes, paletteTypes=paletteTypes)

    assert cpal.tableTag == "CPAL"
    assert cpal.version == 1
    assert cpal.numPaletteEntries == 2
    assert len(cpal.palettes) == 3

    assert cpal.paletteTypes == paletteTypes
    assert cpal.paletteLabels == [cpal.NO_NAME_ID] * len(palettes)
    assert cpal.paletteEntryLabels == [cpal.NO_NAME_ID] * cpal.numPaletteEntries


def test_build_CPAL_v1_labels():
    palettes = [
        [(0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0)],
        [(0.1, 0.2, 0.3, 0.6), (0.4, 0.5, 0.6, 0.6)],
        [(0.1, 0.2, 0.3, 0.3), (0.4, 0.5, 0.6, 0.3)],
    ]
    paletteLabels = ["First", {"en": "Second", "it": "Seconda"}, None]
    paletteEntryLabels = ["Foo", "Bar"]

    with pytest.raises(TypeError, match="nameTable is required"):
        builder.buildCPAL(palettes, paletteLabels=paletteLabels)
    with pytest.raises(TypeError, match="nameTable is required"):
        builder.buildCPAL(palettes, paletteEntryLabels=paletteEntryLabels)

    name_table = newTable("name")
    name_table.names = []

    cpal = builder.buildCPAL(
        palettes,
        paletteLabels=paletteLabels,
        paletteEntryLabels=paletteEntryLabels,
        nameTable=name_table,
    )

    assert cpal.tableTag == "CPAL"
    assert cpal.version == 1
    assert cpal.numPaletteEntries == 2
    assert len(cpal.palettes) == 3

    assert cpal.paletteTypes == [cpal.DEFAULT_PALETTE_TYPE] * len(palettes)
    assert cpal.paletteLabels == [256, 257, cpal.NO_NAME_ID]
    assert cpal.paletteEntryLabels == [258, 259]

    assert name_table.getDebugName(256) == "First"
    assert name_table.getDebugName(257) == "Second"
    assert name_table.getDebugName(258) == "Foo"
    assert name_table.getDebugName(259) == "Bar"


def test_invalid_ColorPaletteType():
    with pytest.raises(ValueError, match="not a valid ColorPaletteType"):
        builder.ColorPaletteType(-1)
    with pytest.raises(ValueError, match="not a valid ColorPaletteType"):
        builder.ColorPaletteType(4)
    with pytest.raises(ValueError, match="not a valid ColorPaletteType"):
        builder.ColorPaletteType("abc")


def test_buildCPAL_v1_invalid_args_length():
    with pytest.raises(ColorLibError, match="Expected 2 paletteTypes, got 1"):
        builder.buildCPAL([[(0, 0, 0, 0)], [(1, 1, 1, 1)]], paletteTypes=[1])

    with pytest.raises(ColorLibError, match="Expected 2 paletteLabels, got 1"):
        builder.buildCPAL(
            [[(0, 0, 0, 0)], [(1, 1, 1, 1)]],
            paletteLabels=["foo"],
            nameTable=newTable("name"),
        )

    with pytest.raises(ColorLibError, match="Expected 1 paletteEntryLabels, got 0"):
        cpal = builder.buildCPAL(
            [[(0, 0, 0, 0)], [(1, 1, 1, 1)]],
            paletteEntryLabels=[],
            nameTable=newTable("name"),
        )


def test_buildCPAL_invalid_color():
    with pytest.raises(
        ColorLibError,
        match=r"In palette\[0\]\[1\]: expected \(R, G, B, A\) tuple, got \(1, 1, 1\)",
    ):
        builder.buildCPAL([[(1, 1, 1, 1), (1, 1, 1)]])

    with pytest.raises(
        ColorLibError,
        match=(
            r"palette\[1\]\[0\] has invalid out-of-range "
            r"\[0..1\] color: \(1, 1, -1, 2\)"
        ),
    ):
        builder.buildCPAL([[(0, 0, 0, 0)], [(1, 1, -1, 2)]])


def test_buildPaintSolid():
    p = _buildPaint((ot.PaintFormat.PaintSolid, 0))
    assert p.Format == ot.PaintFormat.PaintSolid
    assert p.PaletteIndex == 0
    assert p.Alpha == 1.0


def test_buildPaintSolid_Alpha():
    p = _buildPaint((ot.PaintFormat.PaintSolid, 1, 0.5))
    assert p.Format == ot.PaintFormat.PaintSolid
    assert p.PaletteIndex == 1
    assert p.Alpha == 0.5


def test_buildPaintVarSolid():
    p = _buildPaint((ot.PaintFormat.PaintVarSolid, 3, 0.5, 2))
    assert p.Format == ot.PaintFormat.PaintVarSolid
    assert p.PaletteIndex == 3
    assert p.Alpha == 0.5
    assert p.VarIndexBase == 2


def test_buildVarColorStop_DefaultAlpha():
    s = _build(ot.ColorStop, (0.1, 2))
    assert s.StopOffset == 0.1
    assert s.PaletteIndex == 2
    assert s.Alpha == builder._DEFAULT_ALPHA


def test_buildVarColorStop_DefaultAlpha():
    s = _build(ot.VarColorStop, (0.1, 2))
    assert s.StopOffset == 0.1
    assert s.PaletteIndex == 2
    assert s.Alpha == builder._DEFAULT_ALPHA


def test_buildColorStop():
    s = _build(ot.ColorStop, {"StopOffset": 0.2, "PaletteIndex": 3, "Alpha": 0.4})
    assert s.StopOffset == 0.2
    assert s.PaletteIndex == 3
    assert s.Alpha == 0.4


def test_buildColorStop_Variable():
    s = _build(
        ot.VarColorStop,
        {
            "StopOffset": 0.0,
            "PaletteIndex": 0,
            "Alpha": 0.3,
            "VarIndexBase": 1,
        },
    )
    assert s.StopOffset == 0.0
    assert s.PaletteIndex == 0
    assert s.Alpha == 0.3
    assert s.VarIndexBase == 1


def test_buildColorLine_StopList():
    stops = [(0.0, 0), (0.5, 1), (1.0, 2)]

    cline = _build(ot.ColorLine, {"ColorStop": stops})
    assert cline.Extend == builder.ExtendMode.PAD
    assert cline.StopCount == 3
    assert [(cs.StopOffset, cs.PaletteIndex) for cs in cline.ColorStop] == stops

    cline = _build(ot.ColorLine, {"Extend": "pad", "ColorStop": stops})
    assert cline.Extend == builder.ExtendMode.PAD

    cline = _build(
        ot.ColorLine, {"ColorStop": stops, "Extend": builder.ExtendMode.REPEAT}
    )
    assert cline.Extend == builder.ExtendMode.REPEAT

    cline = _build(
        ot.ColorLine, {"ColorStop": stops, "Extend": builder.ExtendMode.REFLECT}
    )
    assert cline.Extend == builder.ExtendMode.REFLECT

    cline = _build(
        ot.ColorLine, {"ColorStop": [_build(ot.ColorStop, s) for s in stops]}
    )
    assert [(cs.StopOffset, cs.PaletteIndex) for cs in cline.ColorStop] == stops


def test_buildVarColorLine_StopMap():
    stops = [
        {"StopOffset": 0.0, "PaletteIndex": 0, "Alpha": 0.5, "VarIndexBase": 1},
        {"StopOffset": 1.0, "PaletteIndex": 1, "Alpha": 0.3, "VarIndexBase": 3},
    ]
    cline = _build(ot.VarColorLine, {"ColorStop": stops})
    assert [
        {
            "StopOffset": cs.StopOffset,
            "PaletteIndex": cs.PaletteIndex,
            "Alpha": cs.Alpha,
            "VarIndexBase": cs.VarIndexBase,
        }
        for cs in cline.ColorStop
    ] == stops


def checkBuildAffine2x3(cls, variable=False):
    matrix = _build(cls, (1.5, 0, 0.5, 2.0, 1.0, -3.0))
    assert matrix.xx == 1.5
    assert matrix.yx == 0.0
    assert matrix.xy == 0.5
    assert matrix.yy == 2.0
    assert matrix.dx == 1.0
    assert matrix.dy == -3.0
    if variable:
        assert matrix.VarIndexBase == 0xFFFFFFFF


def test_buildAffine2x3():
    checkBuildAffine2x3(ot.Affine2x3)


def test_buildVarAffine2x3():
    checkBuildAffine2x3(ot.VarAffine2x3, variable=True)


def _sample_stops(variable):
    cls = ot.ColorStop if not variable else ot.VarColorStop
    stop_sources = [
        {"StopOffset": 0.0, "PaletteIndex": 0},
        {"StopOffset": 0.5, "PaletteIndex": 1},
        {"StopOffset": 1.0, "PaletteIndex": 2, "Alpha": 0.8},
    ]
    if variable:
        for i, src in enumerate(stop_sources, start=123):
            src["VarIndexBase"] = i
    return [_build(cls, src) for src in stop_sources]


def _is_var(fmt):
    return fmt.name.startswith("PaintVar")


def _is_around_center(fmt):
    return fmt.name.endswith("AroundCenter")


def _is_uniform_scale(fmt):
    return "ScaleUniform" in fmt.name


def checkBuildPaintLinearGradient(fmt):
    variable = _is_var(fmt)
    color_stops = _sample_stops(variable)

    x0, y0, x1, y1, x2, y2 = (1, 2, 3, 4, 5, 6)
    source = {
        "Format": fmt,
        "ColorLine": {"ColorStop": color_stops},
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
    }
    if variable:
        source["VarIndexBase"] = 7
    gradient = _buildPaint(source)
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops

    gradient = _buildPaint(gradient)
    assert (gradient.x0, gradient.y0) == (1, 2)
    assert (gradient.x1, gradient.y1) == (3, 4)
    assert (gradient.x2, gradient.y2) == (5, 6)
    if variable:
        assert gradient.VarIndexBase == 7


def test_buildPaintLinearGradient():
    assert not _is_var(ot.PaintFormat.PaintLinearGradient)
    checkBuildPaintLinearGradient(ot.PaintFormat.PaintLinearGradient)


def test_buildPaintVarLinearGradient():
    assert _is_var(ot.PaintFormat.PaintVarLinearGradient)
    checkBuildPaintLinearGradient(ot.PaintFormat.PaintVarLinearGradient)


def checkBuildPaintRadialGradient(fmt):
    variable = _is_var(fmt)
    color_stops = _sample_stops(variable)
    line_cls = ot.VarColorLine if variable else ot.ColorLine

    color_line = _build(
        line_cls, {"ColorStop": color_stops, "Extend": builder.ExtendMode.REPEAT}
    )
    c0 = (100, 200)
    c1 = (150, 250)
    r0 = 10
    r1 = 5
    varIndexBase = 0

    source = [fmt, color_line, *c0, r0, *c1, r1]
    if variable:
        source.append(varIndexBase)

    gradient = _build(ot.Paint, tuple(source))
    assert gradient.Format == fmt
    assert gradient.ColorLine == color_line
    assert (gradient.x0, gradient.y0) == c0
    assert (gradient.x1, gradient.y1) == c1
    assert gradient.r0 == r0
    assert gradient.r1 == r1
    if variable:
        assert gradient.VarIndexBase == varIndexBase

    source = {
        "Format": fmt,
        "ColorLine": {"ColorStop": color_stops},
        "x0": c0[0],
        "y0": c0[1],
        "x1": c1[0],
        "y1": c1[1],
        "r0": r0,
        "r1": r1,
    }
    if variable:
        source["VarIndexBase"] = varIndexBase
    gradient = _build(ot.Paint, source)
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops
    assert (gradient.x0, gradient.y0) == c0
    assert (gradient.x1, gradient.y1) == c1
    assert gradient.r0 == r0
    assert gradient.r1 == r1
    if variable:
        assert gradient.VarIndexBase == varIndexBase


def test_buildPaintRadialGradient():
    assert not _is_var(ot.PaintFormat.PaintRadialGradient)
    checkBuildPaintRadialGradient(ot.PaintFormat.PaintRadialGradient)


def test_buildPaintVarRadialGradient():
    assert _is_var(ot.PaintFormat.PaintVarRadialGradient)
    checkBuildPaintRadialGradient(ot.PaintFormat.PaintVarRadialGradient)


def checkPaintSweepGradient(fmt):
    variable = _is_var(fmt)
    source = {
        "Format": fmt,
        "ColorLine": {"ColorStop": _sample_stops(variable)},
        "centerX": 127,
        "centerY": 129,
        "startAngle": 15,
        "endAngle": 42,
    }
    if variable:
        source["VarIndexBase"] = 666
    paint = _buildPaint(source)

    assert paint.Format == fmt
    assert paint.centerX == 127
    assert paint.centerY == 129
    assert paint.startAngle == 15
    assert paint.endAngle == 42
    if variable:
        assert paint.VarIndexBase == 666


def test_buildPaintSweepGradient():
    assert not _is_var(ot.PaintFormat.PaintSweepGradient)
    checkPaintSweepGradient(ot.PaintFormat.PaintSweepGradient)


def test_buildPaintVarSweepGradient():
    assert _is_var(ot.PaintFormat.PaintVarSweepGradient)
    checkPaintSweepGradient(ot.PaintFormat.PaintVarSweepGradient)


def test_buildPaintGlyph_Solid():
    layer = _build(
        ot.Paint,
        (
            ot.PaintFormat.PaintGlyph,
            (
                ot.PaintFormat.PaintSolid,
                2,
            ),
            "a",
        ),
    )
    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.PaintFormat.PaintSolid
    assert layer.Paint.PaletteIndex == 2

    layer = _build(
        ot.Paint,
        (
            ot.PaintFormat.PaintGlyph,
            (ot.PaintFormat.PaintSolid, 3, 0.9),
            "a",
        ),
    )
    assert layer.Paint.Format == ot.PaintFormat.PaintSolid
    assert layer.Paint.PaletteIndex == 3
    assert layer.Paint.Alpha == 0.9


def test_buildPaintGlyph_VarLinearGradient():
    layer = _build(
        ot.Paint,
        {
            "Format": ot.PaintFormat.PaintGlyph,
            "Glyph": "a",
            "Paint": {
                "Format": ot.PaintFormat.PaintVarLinearGradient,
                "ColorLine": {"ColorStop": [(0.0, 3), (1.0, 4)]},
                "x0": 100,
                "y0": 200,
                "x1": 150,
                "y1": 250,
            },
        },
    )

    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.PaintFormat.PaintVarLinearGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset == 0.0
    assert layer.Paint.ColorLine.ColorStop[0].PaletteIndex == 3
    assert layer.Paint.ColorLine.ColorStop[1].StopOffset == 1.0
    assert layer.Paint.ColorLine.ColorStop[1].PaletteIndex == 4
    assert layer.Paint.x0 == 100
    assert layer.Paint.y0 == 200
    assert layer.Paint.x1 == 150
    assert layer.Paint.y1 == 250


def test_buildPaintGlyph_RadialGradient():
    layer = _build(
        ot.Paint,
        (
            int(ot.PaintFormat.PaintGlyph),
            (
                ot.PaintFormat.PaintRadialGradient,
                (
                    "pad",
                    [
                        (0.0, 5),
                        {"StopOffset": 0.5, "PaletteIndex": 6, "Alpha": 0.8},
                        (1.0, 7),
                    ],
                ),
                50,
                50,
                30,
                75,
                75,
                10,
            ),
            "a",
        ),
    )
    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Paint.Format == ot.PaintFormat.PaintRadialGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset == 0.0
    assert layer.Paint.ColorLine.ColorStop[0].PaletteIndex == 5
    assert layer.Paint.ColorLine.ColorStop[1].StopOffset == 0.5
    assert layer.Paint.ColorLine.ColorStop[1].PaletteIndex == 6
    assert layer.Paint.ColorLine.ColorStop[1].Alpha == 0.8
    assert layer.Paint.ColorLine.ColorStop[2].StopOffset == 1.0
    assert layer.Paint.ColorLine.ColorStop[2].PaletteIndex == 7
    assert layer.Paint.x0 == 50
    assert layer.Paint.y0 == 50
    assert layer.Paint.r0 == 30
    assert layer.Paint.x1 == 75
    assert layer.Paint.y1 == 75
    assert layer.Paint.r1 == 10


def test_buildPaintGlyph_Dict_Solid():
    layer = _build(
        ot.Paint,
        (
            int(ot.PaintFormat.PaintGlyph),
            (int(ot.PaintFormat.PaintSolid), 1),
            "a",
        ),
    )
    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.PaintFormat.PaintSolid
    assert layer.Paint.PaletteIndex == 1


def test_buildPaintGlyph_Dict_VarLinearGradient():
    layer = _build(
        ot.Paint,
        {
            "Format": ot.PaintFormat.PaintGlyph,
            "Glyph": "a",
            "Paint": {
                "Format": int(ot.PaintFormat.PaintVarLinearGradient),
                "ColorLine": {"ColorStop": [(0.0, 0), (1.0, 1)]},
                "x0": 0,
                "y0": 0,
                "x1": 10,
                "y1": 10,
            },
        },
    )
    assert layer.Format == ot.PaintFormat.PaintGlyph
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.PaintFormat.PaintVarLinearGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset == 0.0


def test_buildPaintGlyph_Dict_RadialGradient():
    layer = _buildPaint(
        {
            "Glyph": "a",
            "Paint": {
                "Format": int(ot.PaintFormat.PaintRadialGradient),
                "ColorLine": {"ColorStop": [(0.0, 0), (1.0, 1)]},
                "x0": 0,
                "y0": 0,
                "r0": 4,
                "x1": 10,
                "y1": 10,
                "r1": 0,
            },
            "Format": int(ot.PaintFormat.PaintGlyph),
        },
    )
    assert layer.Paint.Format == ot.PaintFormat.PaintRadialGradient
    assert layer.Paint.r0 == 4


def test_buildPaintColrGlyph():
    paint = _buildPaint((int(ot.PaintFormat.PaintColrGlyph), "a"))
    assert paint.Format == ot.PaintFormat.PaintColrGlyph
    assert paint.Glyph == "a"


def checkBuildPaintTransform(fmt):
    variable = _is_var(fmt)
    if variable:
        affine_cls = ot.VarAffine2x3
    else:
        affine_cls = ot.Affine2x3

    affine_src = [1, 2, 3, 4, 5, 6]
    if variable:
        affine_src.append(7)

    paint = _buildPaint(
        (
            int(fmt),
            (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0, 1.0), "a"),
            _build(affine_cls, tuple(affine_src)),
        ),
    )

    assert paint.Format == fmt
    assert paint.Paint.Format == ot.PaintFormat.PaintGlyph
    assert paint.Paint.Paint.Format == ot.PaintFormat.PaintSolid

    assert paint.Transform.xx == 1.0
    assert paint.Transform.yx == 2.0
    assert paint.Transform.xy == 3.0
    assert paint.Transform.yy == 4.0
    assert paint.Transform.dx == 5.0
    assert paint.Transform.dy == 6.0
    if variable:
        assert paint.Transform.VarIndexBase == 7

    affine_src = [1, 2, 3, 0.3333, 10, 10]
    if variable:
        affine_src.append(456)  # VarIndexBase
    paint = _build(
        ot.Paint,
        {
            "Format": fmt,
            "Transform": tuple(affine_src),
            "Paint": {
                "Format": int(ot.PaintFormat.PaintRadialGradient),
                "ColorLine": {"ColorStop": [(0.0, 0), (1.0, 1)]},
                "x0": 100,
                "y0": 101,
                "x1": 102,
                "y1": 103,
                "r0": 0,
                "r1": 50,
            },
        },
    )

    assert paint.Format == fmt
    assert paint.Transform.xx == 1.0
    assert paint.Transform.yx == 2.0
    assert paint.Transform.xy == 3.0
    assert paint.Transform.yy == 0.3333
    assert paint.Transform.dx == 10
    assert paint.Transform.dy == 10
    if variable:
        assert paint.Transform.VarIndexBase == 456
    assert paint.Paint.Format == ot.PaintFormat.PaintRadialGradient


def test_buildPaintTransform():
    assert not _is_var(ot.PaintFormat.PaintTransform)
    checkBuildPaintTransform(ot.PaintFormat.PaintTransform)


def test_buildPaintVarTransform():
    assert _is_var(ot.PaintFormat.PaintVarTransform)
    checkBuildPaintTransform(ot.PaintFormat.PaintVarTransform)


def test_buildPaintComposite():
    composite = _build(
        ot.Paint,
        {
            "Format": int(ot.PaintFormat.PaintComposite),
            "CompositeMode": "src_over",
            "SourcePaint": {
                "Format": ot.PaintFormat.PaintComposite,
                "CompositeMode": "src_over",
                "SourcePaint": {
                    "Format": int(ot.PaintFormat.PaintGlyph),
                    "Glyph": "c",
                    "Paint": (ot.PaintFormat.PaintSolid, 2),
                },
                "BackdropPaint": {
                    "Format": int(ot.PaintFormat.PaintGlyph),
                    "Glyph": "b",
                    "Paint": (ot.PaintFormat.PaintSolid, 1),
                },
            },
            "BackdropPaint": {
                "Format": ot.PaintFormat.PaintGlyph,
                "Glyph": "a",
                "Paint": {
                    "Format": ot.PaintFormat.PaintSolid,
                    "PaletteIndex": 0,
                    "Alpha": 0.5,
                },
            },
        },
    )

    assert composite.Format == ot.PaintFormat.PaintComposite
    assert composite.SourcePaint.Format == ot.PaintFormat.PaintComposite
    assert composite.SourcePaint.SourcePaint.Format == ot.PaintFormat.PaintGlyph
    assert composite.SourcePaint.SourcePaint.Glyph == "c"
    assert composite.SourcePaint.SourcePaint.Paint.Format == ot.PaintFormat.PaintSolid
    assert composite.SourcePaint.SourcePaint.Paint.PaletteIndex == 2
    assert composite.SourcePaint.CompositeMode == ot.CompositeMode.SRC_OVER
    assert composite.SourcePaint.BackdropPaint.Format == ot.PaintFormat.PaintGlyph
    assert composite.SourcePaint.BackdropPaint.Glyph == "b"
    assert composite.SourcePaint.BackdropPaint.Paint.Format == ot.PaintFormat.PaintSolid
    assert composite.SourcePaint.BackdropPaint.Paint.PaletteIndex == 1
    assert composite.CompositeMode == ot.CompositeMode.SRC_OVER
    assert composite.BackdropPaint.Format == ot.PaintFormat.PaintGlyph
    assert composite.BackdropPaint.Glyph == "a"
    assert composite.BackdropPaint.Paint.Format == ot.PaintFormat.PaintSolid
    assert composite.BackdropPaint.Paint.PaletteIndex == 0
    assert composite.BackdropPaint.Paint.Alpha == 0.5


def checkBuildPaintTranslate(fmt):
    variable = _is_var(fmt)

    source = {
        "Format": fmt,
        "Paint": (
            ot.PaintFormat.PaintGlyph,
            (ot.PaintFormat.PaintSolid, 0, 1.0),
            "a",
        ),
        "dx": 123,
        "dy": -345,
    }
    if variable:
        source["VarIndexBase"] = 678

    paint = _build(ot.Paint, source)

    assert paint.Format == fmt
    assert paint.Paint.Format == ot.PaintFormat.PaintGlyph
    assert paint.dx == 123
    assert paint.dy == -345
    if variable:
        assert paint.VarIndexBase == 678


def test_buildPaintTranslate():
    assert not _is_var(ot.PaintFormat.PaintTranslate)
    checkBuildPaintTranslate(ot.PaintFormat.PaintTranslate)


def test_buildPaintVarTranslate():
    assert _is_var(ot.PaintFormat.PaintVarTranslate)
    checkBuildPaintTranslate(ot.PaintFormat.PaintVarTranslate)


def checkBuildPaintScale(fmt):
    variable = _is_var(fmt)
    around_center = _is_around_center(fmt)
    uniform = _is_uniform_scale(fmt)

    source = {
        "Format": fmt,
        "Paint": (
            ot.PaintFormat.PaintGlyph,
            (ot.PaintFormat.PaintSolid, 0, 1.0),
            "a",
        ),
    }
    if uniform:
        source["scale"] = 1.5
    else:
        source["scaleX"] = 1.0
        source["scaleY"] = 2.0
    if around_center:
        source["centerX"] = 127
        source["centerY"] = 129
    if variable:
        source["VarIndexBase"] = 666

    paint = _build(ot.Paint, source)

    assert paint.Format == fmt
    assert paint.Paint.Format == ot.PaintFormat.PaintGlyph
    if uniform:
        assert paint.scale == 1.5
    else:
        assert paint.scaleX == 1.0
        assert paint.scaleY == 2.0
    if around_center:
        assert paint.centerX == 127
        assert paint.centerY == 129
    if variable:
        assert paint.VarIndexBase == 666


def test_buildPaintScale():
    assert not _is_var(ot.PaintFormat.PaintScale)
    assert not _is_uniform_scale(ot.PaintFormat.PaintScale)
    assert not _is_around_center(ot.PaintFormat.PaintScale)
    checkBuildPaintScale(ot.PaintFormat.PaintScale)


def test_buildPaintVarScale():
    assert _is_var(ot.PaintFormat.PaintVarScale)
    assert not _is_uniform_scale(ot.PaintFormat.PaintVarScale)
    assert not _is_around_center(ot.PaintFormat.PaintVarScale)
    checkBuildPaintScale(ot.PaintFormat.PaintVarScale)


def test_buildPaintScaleAroundCenter():
    assert not _is_var(ot.PaintFormat.PaintScaleAroundCenter)
    assert not _is_uniform_scale(ot.PaintFormat.PaintScaleAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintScaleAroundCenter)
    checkBuildPaintScale(ot.PaintFormat.PaintScaleAroundCenter)


def test_buildPaintVarScaleAroundCenter():
    assert _is_var(ot.PaintFormat.PaintVarScaleAroundCenter)
    assert not _is_uniform_scale(ot.PaintFormat.PaintScaleAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintVarScaleAroundCenter)
    checkBuildPaintScale(ot.PaintFormat.PaintVarScaleAroundCenter)


def test_buildPaintScaleUniform():
    assert not _is_var(ot.PaintFormat.PaintScaleUniform)
    assert _is_uniform_scale(ot.PaintFormat.PaintScaleUniform)
    assert not _is_around_center(ot.PaintFormat.PaintScaleUniform)
    checkBuildPaintScale(ot.PaintFormat.PaintScaleUniform)


def test_buildPaintVarScaleUniform():
    assert _is_var(ot.PaintFormat.PaintVarScaleUniform)
    assert _is_uniform_scale(ot.PaintFormat.PaintVarScaleUniform)
    assert not _is_around_center(ot.PaintFormat.PaintVarScaleUniform)
    checkBuildPaintScale(ot.PaintFormat.PaintVarScaleUniform)


def test_buildPaintScaleUniformAroundCenter():
    assert not _is_var(ot.PaintFormat.PaintScaleUniformAroundCenter)
    assert _is_uniform_scale(ot.PaintFormat.PaintScaleUniformAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintScaleUniformAroundCenter)
    checkBuildPaintScale(ot.PaintFormat.PaintScaleUniformAroundCenter)


def test_buildPaintVarScaleUniformAroundCenter():
    assert _is_var(ot.PaintFormat.PaintVarScaleUniformAroundCenter)
    assert _is_uniform_scale(ot.PaintFormat.PaintVarScaleUniformAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintVarScaleUniformAroundCenter)
    checkBuildPaintScale(ot.PaintFormat.PaintVarScaleUniformAroundCenter)


def checkBuildPaintRotate(fmt):
    variable = _is_var(fmt)
    around_center = _is_around_center(fmt)

    source = {
        "Format": fmt,
        "Paint": (
            ot.PaintFormat.PaintGlyph,
            (ot.PaintFormat.PaintSolid, 0, 1.0),
            "a",
        ),
        "angle": 15,
    }
    if around_center:
        source["centerX"] = 127
        source["centerY"] = 129

    paint = _build(ot.Paint, source)

    assert paint.Format == fmt
    assert paint.Paint.Format == ot.PaintFormat.PaintGlyph
    assert paint.angle == 15
    if around_center:
        assert paint.centerX == 127
        assert paint.centerY == 129
    if variable:
        assert paint.VarIndexBase == 0xFFFFFFFF


def test_buildPaintRotate():
    assert not _is_var(ot.PaintFormat.PaintRotate)
    assert not _is_around_center(ot.PaintFormat.PaintRotate)
    checkBuildPaintRotate(ot.PaintFormat.PaintRotate)


def test_buildPaintVarRotate():
    assert _is_var(ot.PaintFormat.PaintVarRotate)
    assert not _is_around_center(ot.PaintFormat.PaintVarRotate)
    checkBuildPaintRotate(ot.PaintFormat.PaintVarRotate)


def test_buildPaintRotateAroundCenter():
    assert not _is_var(ot.PaintFormat.PaintRotateAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintRotateAroundCenter)
    checkBuildPaintRotate(ot.PaintFormat.PaintRotateAroundCenter)


def test_buildPaintVarRotateAroundCenter():
    assert _is_var(ot.PaintFormat.PaintVarRotateAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintVarRotateAroundCenter)
    checkBuildPaintRotate(ot.PaintFormat.PaintVarRotateAroundCenter)


def checkBuildPaintSkew(fmt):
    variable = _is_var(fmt)
    around_center = _is_around_center(fmt)

    source = {
        "Format": fmt,
        "Paint": (
            ot.PaintFormat.PaintGlyph,
            (ot.PaintFormat.PaintSolid, 0, 1.0),
            "a",
        ),
        "xSkewAngle": 15,
        "ySkewAngle": 42,
    }
    if around_center:
        source["centerX"] = 127
        source["centerY"] = 129
    if variable:
        source["VarIndexBase"] = 0

    paint = _build(ot.Paint, source)

    assert paint.Format == fmt
    assert paint.Paint.Format == ot.PaintFormat.PaintGlyph
    assert paint.xSkewAngle == 15
    assert paint.ySkewAngle == 42
    if around_center:
        assert paint.centerX == 127
        assert paint.centerY == 129
    if variable:
        assert paint.VarIndexBase == 0


def test_buildPaintSkew():
    assert not _is_var(ot.PaintFormat.PaintSkew)
    assert not _is_around_center(ot.PaintFormat.PaintSkew)
    checkBuildPaintSkew(ot.PaintFormat.PaintSkew)


def test_buildPaintVarSkew():
    assert _is_var(ot.PaintFormat.PaintVarSkew)
    assert not _is_around_center(ot.PaintFormat.PaintVarSkew)
    checkBuildPaintSkew(ot.PaintFormat.PaintVarSkew)


def test_buildPaintSkewAroundCenter():
    assert not _is_var(ot.PaintFormat.PaintSkewAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintSkewAroundCenter)
    checkBuildPaintSkew(ot.PaintFormat.PaintSkewAroundCenter)


def test_buildPaintVarSkewAroundCenter():
    assert _is_var(ot.PaintFormat.PaintVarSkewAroundCenter)
    assert _is_around_center(ot.PaintFormat.PaintVarSkewAroundCenter)
    checkBuildPaintSkew(ot.PaintFormat.PaintVarSkewAroundCenter)


def test_buildColrV1():
    colorGlyphs = {
        "a": (
            ot.PaintFormat.PaintColrLayers,
            [
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0), "b"),
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintVarSolid, 1), "c"),
            ],
        ),
        "d": (
            ot.PaintFormat.PaintColrLayers,
            [
                (
                    ot.PaintFormat.PaintGlyph,
                    {
                        "Format": int(ot.PaintFormat.PaintSolid),
                        "PaletteIndex": 2,
                        "Alpha": 0.8,
                    },
                    "e",
                ),
                (
                    ot.PaintFormat.PaintGlyph,
                    {
                        "Format": int(ot.PaintFormat.PaintVarRadialGradient),
                        "ColorLine": {
                            "ColorStop": [(0.0, 3), (1.0, 4)],
                            "Extend": "reflect",
                        },
                        "x0": 0,
                        "y0": 0,
                        "x1": 0,
                        "y1": 0,
                        "r0": 10,
                        "r1": 0,
                    },
                    "f",
                ),
            ],
        ),
        "g": (
            ot.PaintFormat.PaintColrLayers,
            [(ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 5), "h")],
        ),
    }
    glyphMap = {
        ".notdef": 0,
        "a": 4,
        "b": 3,
        "c": 2,
        "d": 1,
        "e": 5,
        "f": 6,
        "g": 7,
        "h": 8,
    }

    # TODO(anthrotype) should we split into two tests? - seems two distinct validations
    layers, baseGlyphs = builder.buildColrV1(colorGlyphs, glyphMap)
    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphPaintRecord[0].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphPaintRecord[1].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphPaintRecord[2].BaseGlyph == "g"

    layers, baseGlyphs = builder.buildColrV1(colorGlyphs)
    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphPaintRecord[0].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphPaintRecord[1].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphPaintRecord[2].BaseGlyph == "g"


def test_buildColrV1_more_than_255_paints():
    num_paints = 364
    colorGlyphs = {
        "a": (
            ot.PaintFormat.PaintColrLayers,
            [
                {
                    "Format": int(ot.PaintFormat.PaintGlyph),
                    "Paint": (ot.PaintFormat.PaintSolid, 0),
                    "Glyph": name,
                }
                for name in (f"glyph{i}" for i in range(num_paints))
            ],
        ),
    }
    layers, baseGlyphs = builder.buildColrV1(colorGlyphs)
    paints = layers.Paint

    assert len(paints) == num_paints + 1

    assert all(paints[i].Format == ot.PaintFormat.PaintGlyph for i in range(255))

    assert paints[255].Format == ot.PaintFormat.PaintColrLayers
    assert paints[255].FirstLayerIndex == 0
    assert paints[255].NumLayers == 255

    assert all(
        paints[i].Format == ot.PaintFormat.PaintGlyph
        for i in range(256, num_paints + 1)
    )

    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphPaintRecord[0].BaseGlyph == "a"
    assert (
        baseGlyphs.BaseGlyphPaintRecord[0].Paint.Format
        == ot.PaintFormat.PaintColrLayers
    )
    assert baseGlyphs.BaseGlyphPaintRecord[0].Paint.FirstLayerIndex == 255
    assert baseGlyphs.BaseGlyphPaintRecord[0].Paint.NumLayers == num_paints + 1 - 255


def test_split_color_glyphs_by_version():
    layerBuilder = LayerListBuilder()
    colorGlyphs = {
        "a": [
            ("b", 0),
            ("c", 1),
            ("d", 2),
            ("e", 3),
        ]
    }

    colorGlyphsV0, colorGlyphsV1 = builder._split_color_glyphs_by_version(colorGlyphs)

    assert colorGlyphsV0 == {"a": [("b", 0), ("c", 1), ("d", 2), ("e", 3)]}
    assert not colorGlyphsV1

    colorGlyphs = {"a": (ot.PaintFormat.PaintGlyph, 0, "b")}

    colorGlyphsV0, colorGlyphsV1 = builder._split_color_glyphs_by_version(colorGlyphs)

    assert not colorGlyphsV0
    assert colorGlyphsV1 == colorGlyphs

    colorGlyphs = {
        "a": [("b", 0)],
        "c": [
            ("d", 1),
            (
                "e",
                {
                    "format": 3,
                    "colorLine": {"stops": [(0.0, 2), (1.0, 3)]},
                    "p0": (0, 0),
                    "p1": (10, 10),
                },
            ),
        ],
    }

    colorGlyphsV0, colorGlyphsV1 = builder._split_color_glyphs_by_version(colorGlyphs)

    assert colorGlyphsV0 == {"a": [("b", 0)]}
    assert "a" not in colorGlyphsV1
    assert "c" in colorGlyphsV1
    assert len(colorGlyphsV1["c"]) == 2


def assertIsColrV1(colr):
    assert colr.version == 1
    assert not hasattr(colr, "ColorLayers")
    assert hasattr(colr, "table")
    assert isinstance(colr.table, ot.COLR)


def assertNoV0Content(colr):
    assert colr.table.BaseGlyphRecordCount == 0
    assert colr.table.BaseGlyphRecordArray is None
    assert colr.table.LayerRecordCount == 0
    assert colr.table.LayerRecordArray is None


def test_build_layerv1list_empty():
    # Nobody uses PaintColrLayers, no layerlist
    colr = builder.buildCOLR(
        {
            # BaseGlyph, tuple form
            "a": (
                int(ot.PaintFormat.PaintGlyph),
                (int(ot.PaintFormat.PaintSolid), 2, 0.8),
                "b",
            ),
            # BaseGlyph, map form
            "b": {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintLinearGradient),
                    "ColorLine": {
                        "ColorStop": [(0.0, 2), (1.0, 3)],
                        "Extend": "reflect",
                    },
                    "x0": 1,
                    "y0": 2,
                    "x1": 3,
                    "y1": 4,
                    "x2": 2,
                    "y2": 2,
                },
                "Glyph": "bb",
            },
        },
        version=1,
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, none in LayerList
    assert colr.table.BaseGlyphList.BaseGlyphCount == 2
    assert len(colr.table.BaseGlyphList.BaseGlyphPaintRecord) == 2
    assert colr.table.LayerList is None


def _paint_names(paints) -> List[str]:
    # prints a predictable string from a paint list to enable
    # semi-readable assertions on a LayerList order.
    result = []
    for paint in paints:
        if paint.Format == int(ot.PaintFormat.PaintGlyph):
            result.append(paint.Glyph)
        elif paint.Format == int(ot.PaintFormat.PaintColrLayers):
            result.append(
                f"Layers[{paint.FirstLayerIndex}:{paint.FirstLayerIndex+paint.NumLayers}]"
            )
    return result


def test_build_layerv1list_simple():
    # Two colr glyphs, each with two layers the first of which is common
    # All layers use the same solid paint
    solid_paint = {
        "Format": int(ot.PaintFormat.PaintSolid),
        "PaletteIndex": 2,
        "Alpha": 0.8,
    }
    backdrop = {
        "Format": int(ot.PaintFormat.PaintGlyph),
        "Paint": solid_paint,
        "Glyph": "back",
    }
    a_foreground = {
        "Format": int(ot.PaintFormat.PaintGlyph),
        "Paint": solid_paint,
        "Glyph": "a_fore",
    }
    b_foreground = {
        "Format": int(ot.PaintFormat.PaintGlyph),
        "Paint": solid_paint,
        "Glyph": "b_fore",
    }

    # list => PaintColrLayers, contents should land in LayerList
    colr = builder.buildCOLR(
        {
            "a": (
                ot.PaintFormat.PaintColrLayers,
                [
                    backdrop,
                    a_foreground,
                ],
            ),
            "b": {
                "Format": ot.PaintFormat.PaintColrLayers,
                "Layers": [
                    backdrop,
                    b_foreground,
                ],
            },
        },
        version=1,
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, 4 paints in LayerList
    # A single shared backdrop isn't worth accessing by slice
    assert colr.table.BaseGlyphList.BaseGlyphCount == 2
    assert len(colr.table.BaseGlyphList.BaseGlyphPaintRecord) == 2
    assert colr.table.LayerList.LayerCount == 4
    assert _paint_names(colr.table.LayerList.Paint) == [
        "back",
        "a_fore",
        "back",
        "b_fore",
    ]


def test_build_layerv1list_with_sharing():
    # Three colr glyphs, each with two layers in common
    solid_paint = {
        "Format": int(ot.PaintFormat.PaintSolid),
        "PaletteIndex": 2,
        "Alpha": 0.8,
    }
    backdrop = [
        {
            "Format": int(ot.PaintFormat.PaintGlyph),
            "Paint": solid_paint,
            "Glyph": "back1",
        },
        {
            "Format": ot.PaintFormat.PaintGlyph,
            "Paint": solid_paint,
            "Glyph": "back2",
        },
    ]
    a_foreground = {
        "Format": ot.PaintFormat.PaintGlyph,
        "Paint": solid_paint,
        "Glyph": "a_fore",
    }
    b_background = {
        "Format": ot.PaintFormat.PaintGlyph,
        "Paint": solid_paint,
        "Glyph": "b_back",
    }
    b_foreground = {
        "Format": ot.PaintFormat.PaintGlyph,
        "Paint": solid_paint,
        "Glyph": "b_fore",
    }
    c_background = {
        "Format": ot.PaintFormat.PaintGlyph,
        "Paint": solid_paint,
        "Glyph": "c_back",
    }

    # list => PaintColrLayers, which means contents should be in LayerList
    colr = builder.buildCOLR(
        {
            "a": (ot.PaintFormat.PaintColrLayers, backdrop + [a_foreground]),
            "b": (
                ot.PaintFormat.PaintColrLayers,
                [b_background] + backdrop + [b_foreground],
            ),
            "c": (ot.PaintFormat.PaintColrLayers, [c_background] + backdrop),
        },
        version=1,
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, 4 paints in LayerList
    # A single shared backdrop isn't worth accessing by slice
    baseGlyphs = colr.table.BaseGlyphList.BaseGlyphPaintRecord
    assert colr.table.BaseGlyphList.BaseGlyphCount == 3
    assert len(baseGlyphs) == 3
    assert _paint_names([b.Paint for b in baseGlyphs]) == [
        "Layers[0:3]",
        "Layers[3:6]",
        "Layers[6:8]",
    ]
    assert _paint_names(colr.table.LayerList.Paint) == [
        "back1",
        "back2",
        "a_fore",
        "b_back",
        "Layers[0:2]",
        "b_fore",
        "c_back",
        "Layers[0:2]",
    ]
    assert colr.table.LayerList.LayerCount == 8


def test_build_layerv1list_with_overlaps():
    paints = [
        {
            "Format": ot.PaintFormat.PaintGlyph,
            "Paint": {
                "Format": ot.PaintFormat.PaintSolid,
                "PaletteIndex": 2,
                "Alpha": 0.8,
            },
            "Glyph": c,
        }
        for c in "abcdefghi"
    ]

    # list => PaintColrLayers, which means contents should be in LayerList
    colr = builder.buildCOLR(
        {
            "a": (ot.PaintFormat.PaintColrLayers, paints[0:4]),
            "b": (ot.PaintFormat.PaintColrLayers, paints[0:6]),
            "c": (ot.PaintFormat.PaintColrLayers, paints[2:8]),
        },
        version=1,
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    baseGlyphs = colr.table.BaseGlyphList.BaseGlyphPaintRecord
    # assert colr.table.BaseGlyphList.BaseGlyphCount == 2

    assert _paint_names(colr.table.LayerList.Paint) == [
        "a",
        "b",
        "c",
        "d",
        "Layers[0:4]",
        "e",
        "f",
        "Layers[2:4]",
        "Layers[5:7]",
        "g",
        "h",
    ]
    assert _paint_names([b.Paint for b in baseGlyphs]) == [
        "Layers[0:4]",
        "Layers[4:7]",
        "Layers[7:11]",
    ]
    assert colr.table.LayerList.LayerCount == 11


def test_explicit_version_1():
    colr = builder.buildCOLR(
        {
            "a": (
                ot.PaintFormat.PaintColrLayers,
                [
                    (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0), "b"),
                    (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 1), "c"),
                ],
            )
        },
        version=1,
    )
    assert colr.version == 1
    assert not hasattr(colr, "ColorLayers")
    assert hasattr(colr, "table")
    assert isinstance(colr.table, ot.COLR)
    assert colr.table.VarStore is None


class BuildCOLRTest(object):
    def test_automatic_version_all_solid_color_glyphs(self):
        colr = builder.buildCOLR({"a": [("b", 0), ("c", 1)]})
        assert colr.version == 0
        assert hasattr(colr, "ColorLayers")
        assert colr.ColorLayers["a"][0].name == "b"
        assert colr.ColorLayers["a"][1].name == "c"

    def test_automatic_version_no_solid_color_glyphs(self):
        colr = builder.buildCOLR(
            {
                "a": (
                    ot.PaintFormat.PaintColrLayers,
                    [
                        (
                            ot.PaintFormat.PaintGlyph,
                            {
                                "Format": int(ot.PaintFormat.PaintRadialGradient),
                                "ColorLine": {
                                    "ColorStop": [(0.0, 0), (1.0, 1)],
                                    "Extend": "repeat",
                                },
                                "x0": 1,
                                "y0": 0,
                                "x1": 10,
                                "y1": 0,
                                "r0": 4,
                                "r1": 2,
                            },
                            "b",
                        ),
                        (
                            ot.PaintFormat.PaintGlyph,
                            {
                                "Format": ot.PaintFormat.PaintSolid,
                                "PaletteIndex": 2,
                                "Alpha": 0.8,
                            },
                            "c",
                        ),
                    ],
                ),
                "d": (
                    ot.PaintFormat.PaintColrLayers,
                    [
                        {
                            "Format": ot.PaintFormat.PaintGlyph,
                            "Glyph": "e",
                            "Paint": {
                                "Format": ot.PaintFormat.PaintLinearGradient,
                                "ColorLine": {
                                    "ColorStop": [(0.0, 2), (1.0, 3)],
                                    "Extend": "reflect",
                                },
                                "x0": 1,
                                "y0": 2,
                                "x1": 3,
                                "y1": 4,
                                "x2": 2,
                                "y2": 2,
                            },
                        }
                    ],
                ),
            }
        )
        assertIsColrV1(colr)
        assert colr.table.BaseGlyphRecordCount == 0
        assert colr.table.BaseGlyphRecordArray is None
        assert colr.table.LayerRecordCount == 0
        assert colr.table.LayerRecordArray is None

    def test_automatic_version_mixed_solid_and_gradient_glyphs(self):
        colr = builder.buildCOLR(
            {
                "a": [("b", 0), ("c", 1)],
                "d": (
                    ot.PaintFormat.PaintColrLayers,
                    [
                        (
                            ot.PaintFormat.PaintGlyph,
                            {
                                "Format": ot.PaintFormat.PaintLinearGradient,
                                "ColorLine": {"ColorStop": [(0.0, 2), (1.0, 3)]},
                                "x0": 1,
                                "y0": 2,
                                "x1": 3,
                                "y1": 4,
                                "x2": 2,
                                "y2": 2,
                            },
                            "e",
                        ),
                        (
                            ot.PaintFormat.PaintGlyph,
                            (ot.PaintFormat.PaintSolid, 2, 0.8),
                            "f",
                        ),
                    ],
                ),
            }
        )
        assertIsColrV1(colr)
        assert colr.table.VarStore is None

        assert colr.table.BaseGlyphRecordCount == 1
        assert isinstance(colr.table.BaseGlyphRecordArray, ot.BaseGlyphRecordArray)
        assert colr.table.LayerRecordCount == 2
        assert isinstance(colr.table.LayerRecordArray, ot.LayerRecordArray)

        assert isinstance(colr.table.BaseGlyphList, ot.BaseGlyphList)
        assert colr.table.BaseGlyphList.BaseGlyphCount == 1
        assert isinstance(
            colr.table.BaseGlyphList.BaseGlyphPaintRecord[0], ot.BaseGlyphPaintRecord
        )
        assert colr.table.BaseGlyphList.BaseGlyphPaintRecord[0].BaseGlyph == "d"
        assert isinstance(colr.table.LayerList, ot.LayerList)
        assert colr.table.LayerList.Paint[0].Glyph == "e"

    def test_explicit_version_0(self):
        colr = builder.buildCOLR({"a": [("b", 0), ("c", 1)]}, version=0)
        assert colr.version == 0
        assert hasattr(colr, "ColorLayers")

    def test_explicit_version_1(self):
        colr = builder.buildCOLR(
            {
                "a": (
                    ot.PaintFormat.PaintColrLayers,
                    [
                        (
                            ot.PaintFormat.PaintGlyph,
                            (ot.PaintFormat.PaintSolid, 0),
                            "b",
                        ),
                        (
                            ot.PaintFormat.PaintGlyph,
                            (ot.PaintFormat.PaintSolid, 1),
                            "c",
                        ),
                    ],
                )
            },
            version=1,
        )
        assert colr.version == 1
        assert not hasattr(colr, "ColorLayers")
        assert hasattr(colr, "table")
        assert isinstance(colr.table, ot.COLR)
        assert colr.table.VarStore is None

    def test_paint_one_colr_layers(self):
        # A set of one layers should flip to just that layer
        colr = builder.buildCOLR(
            {
                "a": (
                    ot.PaintFormat.PaintColrLayers,
                    [
                        (
                            ot.PaintFormat.PaintGlyph,
                            (ot.PaintFormat.PaintSolid, 0),
                            "b",
                        ),
                    ],
                )
            },
        )

        assert colr.table.LayerList is None, "PaintColrLayers should be gone"
        assert colr.table.BaseGlyphList.BaseGlyphCount == 1
        paint = colr.table.BaseGlyphList.BaseGlyphPaintRecord[0].Paint
        assert paint.Format == ot.PaintFormat.PaintGlyph
        assert paint.Paint.Format == ot.PaintFormat.PaintSolid

    def test_build_clip_list(self):
        colr = builder.buildCOLR(
            {
                "a": (
                    ot.PaintFormat.PaintGlyph,
                    (ot.PaintFormat.PaintSolid, 0),
                    "b",
                ),
                "c": (
                    ot.PaintFormat.PaintGlyph,
                    (ot.PaintFormat.PaintSolid, 1),
                    "d",
                ),
            },
            clipBoxes={
                "a": (0, 0, 1000, 1000, 0),  # optional 5th: varIndexBase
                "c": (-100.8, -200.4, 1100.1, 1200.5),  # floats get rounded
                "e": (0, 0, 10, 10),  # 'e' does _not_ get ignored despite being missing
            },
        )

        assert colr.table.ClipList.Format == 1
        clipBoxes = colr.table.ClipList.clips
        assert [
            (baseGlyph, clipBox.as_tuple()) for baseGlyph, clipBox in clipBoxes.items()
        ] == [
            ("a", (0, 0, 1000, 1000, 0)),
            ("c", (-101, -201, 1101, 1201)),
            ("e", (0, 0, 10, 10)),
        ]
        assert clipBoxes["a"].Format == 2
        assert clipBoxes["c"].Format == 1
        assert clipBoxes["e"].Format == 1

    def test_duplicate_base_glyphs(self):
        # If > 1 base glyphs refer to equivalent list of layers we expect them to share
        # the same PaintColrLayers.
        layers = {
            "Format": ot.PaintFormat.PaintColrLayers,
            "Layers": [
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 0), "d"),
                (ot.PaintFormat.PaintGlyph, (ot.PaintFormat.PaintSolid, 1), "e"),
            ],
        }
        # I copy the layers to ensure equality is by content, not by identity
        colr = builder.buildCOLR(
            {"a": layers, "b": deepcopy(layers), "c": deepcopy(layers)}
        ).table

        baseGlyphs = colr.BaseGlyphList.BaseGlyphPaintRecord
        assert len(baseGlyphs) == 3

        assert baseGlyphs[0].BaseGlyph == "a"
        assert baseGlyphs[1].BaseGlyph == "b"
        assert baseGlyphs[2].BaseGlyph == "c"

        expected = {"Format": 1, "FirstLayerIndex": 0, "NumLayers": 2}
        assert baseGlyphs[0].Paint.__dict__ == expected
        assert baseGlyphs[1].Paint.__dict__ == expected
        assert baseGlyphs[2].Paint.__dict__ == expected


class TrickyRadialGradientTest:
    @staticmethod
    def circle_inside_circle(c0, r0, c1, r1, rounded=False):
        if rounded:
            return Circle(c0, r0).round().inside(Circle(c1, r1).round())
        else:
            return Circle(c0, r0).inside(Circle(c1, r1))

    def round_start_circle(self, c0, r0, c1, r1, inside=True):
        assert self.circle_inside_circle(c0, r0, c1, r1) is inside
        assert self.circle_inside_circle(c0, r0, c1, r1, rounded=True) is not inside
        r = round_start_circle_stable_containment(c0, r0, c1, r1)
        assert (
            self.circle_inside_circle(r.centre, r.radius, c1, r1, rounded=True)
            is inside
        )
        return r.centre, r.radius

    def test_noto_emoji_mosquito_u1f99f(self):
        # https://github.com/googlefonts/picosvg/issues/158
        c0 = (385.23508, 70.56727999999998)
        r0 = 0
        c1 = (642.99108, 104.70327999999995)
        r1 = 260.0072
        assert self.round_start_circle(c0, r0, c1, r1, inside=True) == ((386, 71), 0)

    def test_noto_emoji_horns_sign_u1f918_1f3fc(self):
        # This radial gradient is taken from noto-emoji's 'SIGNS OF THE HORNS'
        # (1f918_1f3fc). We check that c0 is inside c1 both before and after rounding.
        c0 = (-437.6789059060543, -2116.9237094478003)
        r0 = 0.0
        c1 = (-488.7330118252256, -1876.5036857045086)
        r1 = 245.77147821915673
        assert self.circle_inside_circle(c0, r0, c1, r1)
        assert self.circle_inside_circle(c0, r0, c1, r1, rounded=True)

    @pytest.mark.parametrize(
        "c0, r0, c1, r1, inside, expected",
        [
            # inside before round, outside after round
            ((1.4, 0), 0, (2.6, 0), 1.3, True, ((2, 0), 0)),
            ((1, 0), 0.6, (2.8, 0), 2.45, True, ((2, 0), 1)),
            ((6.49, 6.49), 0, (0.49, 0.49), 8.49, True, ((5, 5), 0)),
            # outside before round, inside after round
            ((0, 0), 0, (2, 0), 1.5, False, ((-1, 0), 0)),
            ((0, -0.5), 0, (0, -2.5), 1.5, False, ((0, 1), 0)),
            # the following ones require two nudges to round correctly
            ((0.5, 0), 0, (9.4, 0), 8.8, False, ((-1, 0), 0)),
            ((1.5, 1.5), 0, (0.49, 0.49), 1.49, True, ((0, 0), 0)),
            # limit case when circle almost exactly overlap
            ((0.5000001, 0), 0.5000001, (0.499999, 0), 0.4999999, True, ((0, 0), 0)),
            # concentrical circles, r0 > r1
            ((0, 0), 1.49, (0, 0), 1, False, ((0, 0), 2)),
        ],
    )
    def test_nudge_start_circle_position(self, c0, r0, c1, r1, inside, expected):
        assert self.round_start_circle(c0, r0, c1, r1, inside) == expected
