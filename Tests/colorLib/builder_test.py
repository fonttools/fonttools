from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib import builder
from fontTools.colorLib.geometry import round_start_circle_stable_containment, Circle
from fontTools.colorLib.builder import LayerV1ListBuilder, _build_n_ary_tree
from fontTools.colorLib.errors import ColorLibError
import pytest
from typing import List


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


def test_buildColorIndex():
    c = builder.buildColorIndex(0)
    assert c.PaletteIndex == 0
    assert c.Alpha.value == 1.0
    assert c.Alpha.varIdx == 0

    c = builder.buildColorIndex(1, alpha=0.5)
    assert c.PaletteIndex == 1
    assert c.Alpha.value == 0.5
    assert c.Alpha.varIdx == 0

    c = builder.buildColorIndex(3, alpha=builder.VariableFloat(0.5, varIdx=2))
    assert c.PaletteIndex == 3
    assert c.Alpha.value == 0.5
    assert c.Alpha.varIdx == 2


def test_buildPaintSolid():
    p = LayerV1ListBuilder().buildPaintSolid(0)
    assert p.Format == ot.Paint.Format.PaintSolid
    assert p.Color.PaletteIndex == 0
    assert p.Color.Alpha.value == 1.0
    assert p.Color.Alpha.varIdx == 0

    p = LayerV1ListBuilder().buildPaintSolid(1, alpha=0.5)
    assert p.Format == ot.Paint.Format.PaintSolid
    assert p.Color.PaletteIndex == 1
    assert p.Color.Alpha.value == 0.5
    assert p.Color.Alpha.varIdx == 0

    p = LayerV1ListBuilder().buildPaintSolid(
        3, alpha=builder.VariableFloat(0.5, varIdx=2)
    )
    assert p.Format == ot.Paint.Format.PaintSolid
    assert p.Color.PaletteIndex == 3
    assert p.Color.Alpha.value == 0.5
    assert p.Color.Alpha.varIdx == 2


def test_buildColorStop():
    s = builder.buildColorStop(0.1, 2)
    assert s.StopOffset == builder.VariableFloat(0.1)
    assert s.Color.PaletteIndex == 2
    assert s.Color.Alpha == builder._DEFAULT_ALPHA

    s = builder.buildColorStop(offset=0.2, paletteIndex=3, alpha=0.4)
    assert s.StopOffset == builder.VariableFloat(0.2)
    assert s.Color == builder.buildColorIndex(3, alpha=0.4)

    s = builder.buildColorStop(
        offset=builder.VariableFloat(0.0, varIdx=1),
        paletteIndex=0,
        alpha=builder.VariableFloat(0.3, varIdx=2),
    )
    assert s.StopOffset == builder.VariableFloat(0.0, varIdx=1)
    assert s.Color.PaletteIndex == 0
    assert s.Color.Alpha == builder.VariableFloat(0.3, varIdx=2)


def test_buildColorLine():
    stops = [(0.0, 0), (0.5, 1), (1.0, 2)]

    cline = builder.buildColorLine(stops)
    assert cline.Extend == builder.ExtendMode.PAD
    assert cline.StopCount == 3
    assert [
        (cs.StopOffset.value, cs.Color.PaletteIndex) for cs in cline.ColorStop
    ] == stops

    cline = builder.buildColorLine(stops, extend="pad")
    assert cline.Extend == builder.ExtendMode.PAD

    cline = builder.buildColorLine(stops, extend=builder.ExtendMode.REPEAT)
    assert cline.Extend == builder.ExtendMode.REPEAT

    cline = builder.buildColorLine(stops, extend=builder.ExtendMode.REFLECT)
    assert cline.Extend == builder.ExtendMode.REFLECT

    cline = builder.buildColorLine([builder.buildColorStop(*s) for s in stops])
    assert [
        (cs.StopOffset.value, cs.Color.PaletteIndex) for cs in cline.ColorStop
    ] == stops

    stops = [
        {"offset": (0.0, 1), "paletteIndex": 0, "alpha": (0.5, 2)},
        {"offset": (1.0, 3), "paletteIndex": 1, "alpha": (0.3, 4)},
    ]
    cline = builder.buildColorLine(stops)
    assert [
        {
            "offset": cs.StopOffset,
            "paletteIndex": cs.Color.PaletteIndex,
            "alpha": cs.Color.Alpha,
        }
        for cs in cline.ColorStop
    ] == stops


def test_buildAffine2x3():
    matrix = builder.buildAffine2x3((1.5, 0, 0.5, 2.0, 1.0, -3.0))
    assert matrix.xx == builder.VariableFloat(1.5)
    assert matrix.yx == builder.VariableFloat(0.0)
    assert matrix.xy == builder.VariableFloat(0.5)
    assert matrix.yy == builder.VariableFloat(2.0)
    assert matrix.dx == builder.VariableFloat(1.0)
    assert matrix.dy == builder.VariableFloat(-3.0)


def test_buildPaintLinearGradient():
    layerBuilder = LayerV1ListBuilder()
    color_stops = [
        builder.buildColorStop(0.0, 0),
        builder.buildColorStop(0.5, 1),
        builder.buildColorStop(1.0, 2, alpha=0.8),
    ]
    color_line = builder.buildColorLine(color_stops, extend=builder.ExtendMode.REPEAT)
    p0 = (builder.VariableInt(100), builder.VariableInt(200))
    p1 = (builder.VariableInt(150), builder.VariableInt(250))

    gradient = layerBuilder.buildPaintLinearGradient(color_line, p0, p1)
    assert gradient.Format == 3
    assert gradient.ColorLine == color_line
    assert (gradient.x0, gradient.y0) == p0
    assert (gradient.x1, gradient.y1) == p1
    assert (gradient.x2, gradient.y2) == p1

    gradient = layerBuilder.buildPaintLinearGradient({"stops": color_stops}, p0, p1)
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops

    gradient = layerBuilder.buildPaintLinearGradient(color_line, p0, p1, p2=(150, 230))
    assert (gradient.x2.value, gradient.y2.value) == (150, 230)
    assert (gradient.x2, gradient.y2) != (gradient.x1, gradient.y1)


def test_buildPaintRadialGradient():
    layerBuilder = LayerV1ListBuilder()
    color_stops = [
        builder.buildColorStop(0.0, 0),
        builder.buildColorStop(0.5, 1),
        builder.buildColorStop(1.0, 2, alpha=0.8),
    ]
    color_line = builder.buildColorLine(color_stops, extend=builder.ExtendMode.REPEAT)
    c0 = (builder.VariableInt(100), builder.VariableInt(200))
    c1 = (builder.VariableInt(150), builder.VariableInt(250))
    r0 = builder.VariableInt(10)
    r1 = builder.VariableInt(5)

    gradient = layerBuilder.buildPaintRadialGradient(color_line, c0, c1, r0, r1)
    assert gradient.Format == ot.Paint.Format.PaintRadialGradient
    assert gradient.ColorLine == color_line
    assert (gradient.x0, gradient.y0) == c0
    assert (gradient.x1, gradient.y1) == c1
    assert gradient.r0 == r0
    assert gradient.r1 == r1

    gradient = layerBuilder.buildPaintRadialGradient(
        {"stops": color_stops}, c0, c1, r0, r1
    )
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops


def test_buildPaintGlyph_Solid():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph("a", 2)
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.Paint.Format.PaintSolid
    assert layer.Paint.Color.PaletteIndex == 2

    layer = layerBuilder.buildPaintGlyph("a", layerBuilder.buildPaintSolid(3, 0.9))
    assert layer.Paint.Format == ot.Paint.Format.PaintSolid
    assert layer.Paint.Color.PaletteIndex == 3
    assert layer.Paint.Color.Alpha.value == 0.9


def test_buildPaintGlyph_LinearGradient():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph(
        "a",
        layerBuilder.buildPaintLinearGradient(
            {"stops": [(0.0, 3), (1.0, 4)]}, (100, 200), (150, 250)
        ),
    )
    assert layer.Paint.Format == ot.Paint.Format.PaintLinearGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset.value == 0.0
    assert layer.Paint.ColorLine.ColorStop[0].Color.PaletteIndex == 3
    assert layer.Paint.ColorLine.ColorStop[1].StopOffset.value == 1.0
    assert layer.Paint.ColorLine.ColorStop[1].Color.PaletteIndex == 4
    assert layer.Paint.x0.value == 100
    assert layer.Paint.y0.value == 200
    assert layer.Paint.x1.value == 150
    assert layer.Paint.y1.value == 250


def test_buildPaintGlyph_RadialGradient():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph(
        "a",
        layerBuilder.buildPaintRadialGradient(
            {
                "stops": [
                    (0.0, 5),
                    {"offset": 0.5, "paletteIndex": 6, "alpha": 0.8},
                    (1.0, 7),
                ]
            },
            (50, 50),
            (75, 75),
            30,
            10,
        ),
    )
    assert layer.Paint.Format == ot.Paint.Format.PaintRadialGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset.value == 0.0
    assert layer.Paint.ColorLine.ColorStop[0].Color.PaletteIndex == 5
    assert layer.Paint.ColorLine.ColorStop[1].StopOffset.value == 0.5
    assert layer.Paint.ColorLine.ColorStop[1].Color.PaletteIndex == 6
    assert layer.Paint.ColorLine.ColorStop[1].Color.Alpha.value == 0.8
    assert layer.Paint.ColorLine.ColorStop[2].StopOffset.value == 1.0
    assert layer.Paint.ColorLine.ColorStop[2].Color.PaletteIndex == 7
    assert layer.Paint.x0.value == 50
    assert layer.Paint.y0.value == 50
    assert layer.Paint.r0.value == 30
    assert layer.Paint.x1.value == 75
    assert layer.Paint.y1.value == 75
    assert layer.Paint.r1.value == 10


def test_buildPaintGlyph_Dict_Solid():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph("a", {"format": 2, "paletteIndex": 0})
    assert layer.Glyph == "a"
    assert layer.Paint.Format == ot.Paint.Format.PaintSolid
    assert layer.Paint.Color.PaletteIndex == 0


def test_buildPaintGlyph_Dict_LinearGradient():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph(
        "a",
        {
            "format": 3,
            "colorLine": {"stops": [(0.0, 0), (1.0, 1)]},
            "p0": (0, 0),
            "p1": (10, 10),
        },
    )
    assert layer.Paint.Format == ot.Paint.Format.PaintLinearGradient
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset.value == 0.0


def test_buildPaintGlyph_Dict_RadialGradient():
    layerBuilder = LayerV1ListBuilder()
    layer = layerBuilder.buildPaintGlyph(
        "a",
        {
            "format": 4,
            "colorLine": {"stops": [(0.0, 0), (1.0, 1)]},
            "c0": (0, 0),
            "c1": (10, 10),
            "r0": 4,
            "r1": 0,
        },
    )
    assert layer.Paint.Format == ot.Paint.Format.PaintRadialGradient
    assert layer.Paint.r0.value == 4


def test_buildPaintColrGlyph():
    paint = LayerV1ListBuilder().buildPaintColrGlyph("a")
    assert paint.Format == ot.Paint.Format.PaintColrGlyph
    assert paint.Glyph == "a"


def test_buildPaintTransform():
    layerBuilder = LayerV1ListBuilder()
    paint = layerBuilder.buildPaintTransform(
        transform=builder.buildAffine2x3((1, 2, 3, 4, 5, 6)),
        paint=layerBuilder.buildPaintGlyph(
            glyph="a",
            paint=layerBuilder.buildPaintSolid(paletteIndex=0, alpha=1.0),
        ),
    )

    assert paint.Format == ot.Paint.Format.PaintTransform
    assert paint.Paint.Format == ot.Paint.Format.PaintGlyph
    assert paint.Paint.Paint.Format == ot.Paint.Format.PaintSolid

    assert paint.Transform.xx.value == 1.0
    assert paint.Transform.yx.value == 2.0
    assert paint.Transform.xy.value == 3.0
    assert paint.Transform.yy.value == 4.0
    assert paint.Transform.dx.value == 5.0
    assert paint.Transform.dy.value == 6.0

    paint = layerBuilder.buildPaintTransform(
        (1, 0, 0, 0.3333, 10, 10),
        {
            "format": 4,
            "colorLine": {"stops": [(0.0, 0), (1.0, 1)]},
            "c0": (100, 100),
            "c1": (100, 100),
            "r0": 0,
            "r1": 50,
        },
    )

    assert paint.Format == ot.Paint.Format.PaintTransform
    assert paint.Transform.xx.value == 1.0
    assert paint.Transform.yx.value == 0.0
    assert paint.Transform.xy.value == 0.0
    assert paint.Transform.yy.value == 0.3333
    assert paint.Transform.dx.value == 10
    assert paint.Transform.dy.value == 10
    assert paint.Paint.Format == ot.Paint.Format.PaintRadialGradient


def test_buildPaintComposite():
    layerBuilder = LayerV1ListBuilder()
    composite = layerBuilder.buildPaintComposite(
        mode=ot.CompositeMode.SRC_OVER,
        source={
            "format": 11,
            "mode": "src_over",
            "source": {"format": 5, "glyph": "c", "paint": 2},
            "backdrop": {"format": 5, "glyph": "b", "paint": 1},
        },
        backdrop=layerBuilder.buildPaintGlyph(
            "a", layerBuilder.buildPaintSolid(paletteIndex=0, alpha=1.0)
        ),
    )

    assert composite.Format == ot.Paint.Format.PaintComposite
    assert composite.SourcePaint.Format == ot.Paint.Format.PaintComposite
    assert composite.SourcePaint.SourcePaint.Format == ot.Paint.Format.PaintGlyph
    assert composite.SourcePaint.SourcePaint.Glyph == "c"
    assert composite.SourcePaint.SourcePaint.Paint.Format == ot.Paint.Format.PaintSolid
    assert composite.SourcePaint.SourcePaint.Paint.Color.PaletteIndex == 2
    assert composite.SourcePaint.CompositeMode == ot.CompositeMode.SRC_OVER
    assert composite.SourcePaint.BackdropPaint.Format == ot.Paint.Format.PaintGlyph
    assert composite.SourcePaint.BackdropPaint.Glyph == "b"
    assert (
        composite.SourcePaint.BackdropPaint.Paint.Format == ot.Paint.Format.PaintSolid
    )
    assert composite.SourcePaint.BackdropPaint.Paint.Color.PaletteIndex == 1
    assert composite.CompositeMode == ot.CompositeMode.SRC_OVER
    assert composite.BackdropPaint.Format == ot.Paint.Format.PaintGlyph
    assert composite.BackdropPaint.Glyph == "a"
    assert composite.BackdropPaint.Paint.Format == ot.Paint.Format.PaintSolid
    assert composite.BackdropPaint.Paint.Color.PaletteIndex == 0


def test_buildPaintTranslate():
    layerBuilder = LayerV1ListBuilder()
    paint = layerBuilder.buildPaintTranslate(
        paint=layerBuilder.buildPaintGlyph(
            "a", layerBuilder.buildPaintSolid(paletteIndex=0, alpha=1.0)
        ),
        dx=123,
        dy=-345,
    )

    assert paint.Format == ot.Paint.Format.PaintTranslate
    assert paint.Paint.Format == ot.Paint.Format.PaintGlyph
    assert paint.dx.value == 123
    assert paint.dy.value == -345


def test_buildPaintRotate():
    layerBuilder = LayerV1ListBuilder()
    paint = layerBuilder.buildPaintRotate(
        paint=layerBuilder.buildPaintGlyph(
            "a", layerBuilder.buildPaintSolid(paletteIndex=0, alpha=1.0)
        ),
        angle=15,
        centerX=127,
        centerY=129,
    )

    assert paint.Format == ot.Paint.Format.PaintRotate
    assert paint.Paint.Format == ot.Paint.Format.PaintGlyph
    assert paint.angle.value == 15
    assert paint.centerX.value == 127
    assert paint.centerY.value == 129


def test_buildPaintSkew():
    layerBuilder = LayerV1ListBuilder()
    paint = layerBuilder.buildPaintSkew(
        paint=layerBuilder.buildPaintGlyph(
            "a", layerBuilder.buildPaintSolid(paletteIndex=0, alpha=1.0)
        ),
        xSkewAngle=15,
        ySkewAngle=42,
        centerX=127,
        centerY=129,
    )

    assert paint.Format == ot.Paint.Format.PaintSkew
    assert paint.Paint.Format == ot.Paint.Format.PaintGlyph
    assert paint.xSkewAngle.value == 15
    assert paint.ySkewAngle.value == 42
    assert paint.centerX.value == 127
    assert paint.centerY.value == 129


def test_buildColrV1():
    colorGlyphs = {
        "a": [("b", 0), ("c", 1)],
        "d": [
            ("e", {"format": 2, "paletteIndex": 2, "alpha": 0.8}),
            (
                "f",
                {
                    "format": 4,
                    "colorLine": {"stops": [(0.0, 3), (1.0, 4)], "extend": "reflect"},
                    "c0": (0, 0),
                    "c1": (0, 0),
                    "r0": 10,
                    "r1": 0,
                },
            ),
        ],
        "g": [("h", 5)],
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
    assert baseGlyphs.BaseGlyphV1Record[0].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphV1Record[1].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphV1Record[2].BaseGlyph == "g"

    layers, baseGlyphs = builder.buildColrV1(colorGlyphs)
    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphV1Record[0].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphV1Record[1].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphV1Record[2].BaseGlyph == "g"


def test_buildColrV1_more_than_255_paints():
    num_paints = 364
    colorGlyphs = {
        "a": [
            {
                "format": 5,  # PaintGlyph
                "paint": 0,
                "glyph": name,
            }
            for name in (f"glyph{i}" for i in range(num_paints))
        ],
    }
    layers, baseGlyphs = builder.buildColrV1(colorGlyphs)
    paints = layers.Paint

    assert len(paints) == num_paints + 1

    assert all(paints[i].Format == ot.Paint.Format.PaintGlyph for i in range(255))

    assert paints[255].Format == ot.Paint.Format.PaintColrLayers
    assert paints[255].FirstLayerIndex == 0
    assert paints[255].NumLayers == 255

    assert all(
        paints[i].Format == ot.Paint.Format.PaintGlyph
        for i in range(256, num_paints + 1)
    )

    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphV1Record[0].BaseGlyph == "a"
    assert (
        baseGlyphs.BaseGlyphV1Record[0].Paint.Format == ot.Paint.Format.PaintColrLayers
    )
    assert baseGlyphs.BaseGlyphV1Record[0].Paint.FirstLayerIndex == 255
    assert baseGlyphs.BaseGlyphV1Record[0].Paint.NumLayers == num_paints + 1 - 255


def test_split_color_glyphs_by_version():
    layerBuilder = LayerV1ListBuilder()
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

    colorGlyphs = {
        "a": [("b", layerBuilder.buildPaintSolid(paletteIndex=0, alpha=0.0))]
    }

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
    # Nobody uses PaintColrLayers (format 8), no layerlist
    colr = builder.buildCOLR(
        {
            "a": {
                "format": 5,  # PaintGlyph
                "paint": {"format": 2, "paletteIndex": 2, "alpha": 0.8},
                "glyph": "b",
            },
            # A list of 1 shouldn't become a PaintColrLayers
            "b": [
                {
                    "format": 5,  # PaintGlyph
                    "paint": {
                        "format": 3,
                        "colorLine": {
                            "stops": [(0.0, 2), (1.0, 3)],
                            "extend": "reflect",
                        },
                        "p0": (1, 2),
                        "p1": (3, 4),
                        "p2": (2, 2),
                    },
                    "glyph": "bb",
                }
            ],
        }
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, none in LayerV1List
    assert colr.table.BaseGlyphV1List.BaseGlyphCount == 2
    assert len(colr.table.BaseGlyphV1List.BaseGlyphV1Record) == 2
    assert colr.table.LayerV1List.LayerCount == 0
    assert len(colr.table.LayerV1List.Paint) == 0


def _paint_names(paints) -> List[str]:
    # prints a predictable string from a paint list to enable
    # semi-readable assertions on a LayerV1List order.
    result = []
    for paint in paints:
        if paint.Format == int(ot.Paint.Format.PaintGlyph):
            result.append(paint.Glyph)
        elif paint.Format == int(ot.Paint.Format.PaintColrLayers):
            result.append(
                f"Layers[{paint.FirstLayerIndex}:{paint.FirstLayerIndex+paint.NumLayers}]"
            )
    return result


def test_build_layerv1list_simple():
    # Two colr glyphs, each with two layers the first of which is common
    # All layers use the same solid paint
    solid_paint = {"format": 2, "paletteIndex": 2, "alpha": 0.8}
    backdrop = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "back",
    }
    a_foreground = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "a_fore",
    }
    b_foreground = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "b_fore",
    }

    # list => PaintColrLayers, which means contents should be in LayerV1List
    colr = builder.buildCOLR(
        {
            "a": [
                backdrop,
                a_foreground,
            ],
            "b": [
                backdrop,
                b_foreground,
            ],
        }
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, 4 paints in LayerV1List
    # A single shared backdrop isn't worth accessing by slice
    assert colr.table.BaseGlyphV1List.BaseGlyphCount == 2
    assert len(colr.table.BaseGlyphV1List.BaseGlyphV1Record) == 2
    assert colr.table.LayerV1List.LayerCount == 4
    assert _paint_names(colr.table.LayerV1List.Paint) == [
        "back",
        "a_fore",
        "back",
        "b_fore",
    ]


def test_build_layerv1list_with_sharing():
    # Three colr glyphs, each with two layers in common
    solid_paint = {"format": 2, "paletteIndex": 2, "alpha": 0.8}
    backdrop = [
        {
            "format": 5,  # PaintGlyph
            "paint": solid_paint,
            "glyph": "back1",
        },
        {
            "format": 5,  # PaintGlyph
            "paint": solid_paint,
            "glyph": "back2",
        },
    ]
    a_foreground = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "a_fore",
    }
    b_background = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "b_back",
    }
    b_foreground = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "b_fore",
    }
    c_background = {
        "format": 5,  # PaintGlyph
        "paint": solid_paint,
        "glyph": "c_back",
    }

    # list => PaintColrLayers, which means contents should be in LayerV1List
    colr = builder.buildCOLR(
        {
            "a": backdrop + [a_foreground],
            "b": [b_background] + backdrop + [b_foreground],
            "c": [c_background] + backdrop,
        }
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    # 2 v1 glyphs, 4 paints in LayerV1List
    # A single shared backdrop isn't worth accessing by slice
    baseGlyphs = colr.table.BaseGlyphV1List.BaseGlyphV1Record
    assert colr.table.BaseGlyphV1List.BaseGlyphCount == 3
    assert len(baseGlyphs) == 3
    assert _paint_names([b.Paint for b in baseGlyphs]) == [
        "Layers[0:3]",
        "Layers[3:6]",
        "Layers[6:8]",
    ]
    assert _paint_names(colr.table.LayerV1List.Paint) == [
        "back1",
        "back2",
        "a_fore",
        "b_back",
        "Layers[0:2]",
        "b_fore",
        "c_back",
        "Layers[0:2]",
    ]
    assert colr.table.LayerV1List.LayerCount == 8


def test_build_layerv1list_with_overlaps():
    paints = [
        {
            "format": 5,  # PaintGlyph
            "paint": {"format": 2, "paletteIndex": 2, "alpha": 0.8},
            "glyph": c,
        }
        for c in "abcdefghi"
    ]

    # list => PaintColrLayers, which means contents should be in LayerV1List
    colr = builder.buildCOLR(
        {
            "a": paints[0:4],
            "b": paints[0:6],
            "c": paints[2:8],
        }
    )

    assertIsColrV1(colr)
    assertNoV0Content(colr)

    baseGlyphs = colr.table.BaseGlyphV1List.BaseGlyphV1Record
    # assert colr.table.BaseGlyphV1List.BaseGlyphCount == 2

    assert _paint_names(colr.table.LayerV1List.Paint) == [
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
    assert colr.table.LayerV1List.LayerCount == 11


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
                "a": [
                    (
                        "b",
                        {
                            "format": 4,
                            "colorLine": {
                                "stops": [(0.0, 0), (1.0, 1)],
                                "extend": "repeat",
                            },
                            "c0": (1, 0),
                            "c1": (10, 0),
                            "r0": 4,
                            "r1": 2,
                        },
                    ),
                    ("c", {"format": 2, "paletteIndex": 2, "alpha": 0.8}),
                ],
                "d": [
                    (
                        "e",
                        {
                            "format": 3,
                            "colorLine": {
                                "stops": [(0.0, 2), (1.0, 3)],
                                "extend": "reflect",
                            },
                            "p0": (1, 2),
                            "p1": (3, 4),
                            "p2": (2, 2),
                        },
                    ),
                ],
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
                "d": [
                    (
                        "e",
                        {
                            "format": 3,
                            "colorLine": {"stops": [(0.0, 2), (1.0, 3)]},
                            "p0": (1, 2),
                            "p1": (3, 4),
                            "p2": (2, 2),
                        },
                    ),
                    ("f", {"format": 2, "paletteIndex": 2, "alpha": 0.8}),
                ],
            }
        )
        assertIsColrV1(colr)
        assert colr.table.VarStore is None

        assert colr.table.BaseGlyphRecordCount == 1
        assert isinstance(colr.table.BaseGlyphRecordArray, ot.BaseGlyphRecordArray)
        assert colr.table.LayerRecordCount == 2
        assert isinstance(colr.table.LayerRecordArray, ot.LayerRecordArray)

        assert isinstance(colr.table.BaseGlyphV1List, ot.BaseGlyphV1List)
        assert colr.table.BaseGlyphV1List.BaseGlyphCount == 1
        assert isinstance(
            colr.table.BaseGlyphV1List.BaseGlyphV1Record[0], ot.BaseGlyphV1Record
        )
        assert colr.table.BaseGlyphV1List.BaseGlyphV1Record[0].BaseGlyph == "d"
        assert isinstance(colr.table.LayerV1List, ot.LayerV1List)
        assert colr.table.LayerV1List.Paint[0].Glyph == "e"

    def test_explicit_version_0(self):
        colr = builder.buildCOLR({"a": [("b", 0), ("c", 1)]}, version=0)
        assert colr.version == 0
        assert hasattr(colr, "ColorLayers")

    def test_explicit_version_1(self):
        colr = builder.buildCOLR({"a": [("b", 0), ("c", 1)]}, version=1)
        assert colr.version == 1
        assert not hasattr(colr, "ColorLayers")
        assert hasattr(colr, "table")
        assert isinstance(colr.table, ot.COLR)
        assert colr.table.VarStore is None


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


@pytest.mark.parametrize(
    "lst, n, expected",
    [
        ([0], 2, [0]),
        ([0, 1], 2, [0, 1]),
        ([0, 1, 2], 2, [[0, 1], 2]),
        ([0, 1, 2], 3, [0, 1, 2]),
        ([0, 1, 2, 3], 2, [[0, 1], [2, 3]]),
        ([0, 1, 2, 3], 3, [[0, 1, 2], 3]),
        ([0, 1, 2, 3, 4], 3, [[0, 1, 2], 3, 4]),
        ([0, 1, 2, 3, 4, 5], 3, [[0, 1, 2], [3, 4, 5]]),
        (list(range(7)), 3, [[0, 1, 2], [3, 4, 5], 6]),
        (list(range(8)), 3, [[0, 1, 2], [3, 4, 5], [6, 7]]),
        (list(range(9)), 3, [[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
        (list(range(10)), 3, [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], 9]),
        (list(range(11)), 3, [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], 9, 10]),
        (list(range(12)), 3, [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], [9, 10, 11]]),
        (list(range(13)), 3, [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], [9, 10, 11], 12]),
        (
            list(range(14)),
            3,
            [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], [[9, 10, 11], 12, 13]],
        ),
        (
            list(range(15)),
            3,
            [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], [9, 10, 11], [12, 13, 14]],
        ),
        (
            list(range(16)),
            3,
            [[[0, 1, 2], [3, 4, 5], [6, 7, 8]], [[9, 10, 11], [12, 13, 14], 15]],
        ),
        (
            list(range(23)),
            3,
            [
                [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                [[9, 10, 11], [12, 13, 14], [15, 16, 17]],
                [[18, 19, 20], 21, 22],
            ],
        ),
        (
            list(range(27)),
            3,
            [
                [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                [[9, 10, 11], [12, 13, 14], [15, 16, 17]],
                [[18, 19, 20], [21, 22, 23], [24, 25, 26]],
            ],
        ),
        (
            list(range(28)),
            3,
            [
                [
                    [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                    [[9, 10, 11], [12, 13, 14], [15, 16, 17]],
                    [[18, 19, 20], [21, 22, 23], [24, 25, 26]],
                ],
                27,
            ],
        ),
        (list(range(257)), 256, [list(range(256)), 256]),
        (list(range(258)), 256, [list(range(256)), 256, 257]),
        (list(range(512)), 256, [list(range(256)), list(range(256, 512))]),
        (list(range(512 + 1)), 256, [list(range(256)), list(range(256, 512)), 512]),
        (
            list(range(256 ** 2)),
            256,
            [list(range(k * 256, k * 256 + 256)) for k in range(256)],
        ),
    ],
)
def test_build_n_ary_tree(lst, n, expected):
    assert _build_n_ary_tree(lst, n) == expected
