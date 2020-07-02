from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib import builder
from fontTools.colorLib.errors import ColorLibError
import pytest


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


def test_buildSolidColorPaint():
    p = builder.buildSolidColorPaint(0)
    assert p.Format == 1
    assert p.Color.PaletteIndex == 0
    assert p.Color.Alpha.value == 1.0
    assert p.Color.Alpha.varIdx == 0

    p = builder.buildSolidColorPaint(1, alpha=0.5)
    assert p.Format == 1
    assert p.Color.PaletteIndex == 1
    assert p.Color.Alpha.value == 0.5
    assert p.Color.Alpha.varIdx == 0

    p = builder.buildSolidColorPaint(3, alpha=builder.VariableFloat(0.5, varIdx=2))
    assert p.Format == 1
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


def test_buildAffine2x2():
    matrix = builder.buildAffine2x2(1.5, 0, 0.5, 2.0)
    assert matrix.xx == builder.VariableFloat(1.5)
    assert matrix.xy == builder.VariableFloat(0.0)
    assert matrix.yx == builder.VariableFloat(0.5)
    assert matrix.yy == builder.VariableFloat(2.0)


def test_buildLinearGradientPaint():
    color_stops = [
        builder.buildColorStop(0.0, 0),
        builder.buildColorStop(0.5, 1),
        builder.buildColorStop(1.0, 2, alpha=0.8),
    ]
    color_line = builder.buildColorLine(color_stops, extend=builder.ExtendMode.REPEAT)
    p0 = (builder.VariableInt(100), builder.VariableInt(200))
    p1 = (builder.VariableInt(150), builder.VariableInt(250))

    gradient = builder.buildLinearGradientPaint(color_line, p0, p1)
    assert gradient.Format == 2
    assert gradient.ColorLine == color_line
    assert (gradient.x0, gradient.y0) == p0
    assert (gradient.x1, gradient.y1) == p1
    assert (gradient.x2, gradient.y2) == p1

    gradient = builder.buildLinearGradientPaint({"stops": color_stops}, p0, p1)
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops

    gradient = builder.buildLinearGradientPaint(color_line, p0, p1, p2=(150, 230))
    assert (gradient.x2.value, gradient.y2.value) == (150, 230)
    assert (gradient.x2, gradient.y2) != (gradient.x1, gradient.y1)


def test_buildRadialGradientPaint():
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

    gradient = builder.buildRadialGradientPaint(color_line, c0, c1, r0, r1)
    assert gradient.Format == 3
    assert gradient.ColorLine == color_line
    assert (gradient.x0, gradient.y0) == c0
    assert (gradient.x1, gradient.y1) == c1
    assert gradient.r0 == r0
    assert gradient.r1 == r1
    assert gradient.Transform is None

    gradient = builder.buildRadialGradientPaint({"stops": color_stops}, c0, c1, r0, r1)
    assert gradient.ColorLine.Extend == builder.ExtendMode.PAD
    assert gradient.ColorLine.ColorStop == color_stops

    matrix = builder.buildAffine2x2(2.0, 0.0, 0.0, 2.0)
    gradient = builder.buildRadialGradientPaint(
        color_line, c0, c1, r0, r1, transform=matrix
    )
    assert gradient.Transform == matrix

    gradient = builder.buildRadialGradientPaint(
        color_line, c0, c1, r0, r1, transform=(2.0, 0.0, 0.0, 2.0)
    )
    assert gradient.Transform == matrix


def test_buildLayerV1Record():
    layer = builder.buildLayerV1Record("a", 2)
    assert layer.LayerGlyph == "a"
    assert layer.Paint.Format == 1
    assert layer.Paint.Color.PaletteIndex == 2

    layer = builder.buildLayerV1Record("a", builder.buildSolidColorPaint(3, 0.9))
    assert layer.Paint.Format == 1
    assert layer.Paint.Color.PaletteIndex == 3
    assert layer.Paint.Color.Alpha.value == 0.9

    layer = builder.buildLayerV1Record(
        "a",
        builder.buildLinearGradientPaint(
            {"stops": [(0.0, 3), (1.0, 4)]}, (100, 200), (150, 250)
        ),
    )
    assert layer.Paint.Format == 2
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset.value == 0.0
    assert layer.Paint.ColorLine.ColorStop[0].Color.PaletteIndex == 3
    assert layer.Paint.ColorLine.ColorStop[1].StopOffset.value == 1.0
    assert layer.Paint.ColorLine.ColorStop[1].Color.PaletteIndex == 4
    assert layer.Paint.x0.value == 100
    assert layer.Paint.y0.value == 200
    assert layer.Paint.x1.value == 150
    assert layer.Paint.y1.value == 250

    layer = builder.buildLayerV1Record(
        "a",
        builder.buildRadialGradientPaint(
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
    assert layer.Paint.Format == 3
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


def test_buildLayerV1Record_from_dict():
    layer = builder.buildLayerV1Record("a", {"format": 1, "paletteIndex": 0})
    assert layer.LayerGlyph == "a"
    assert layer.Paint.Format == 1
    assert layer.Paint.Color.PaletteIndex == 0

    layer = builder.buildLayerV1Record(
        "a",
        {
            "format": 2,
            "colorLine": {"stops": [(0.0, 0), (1.0, 1)]},
            "p0": (0, 0),
            "p1": (10, 10),
        },
    )
    assert layer.Paint.Format == 2
    assert layer.Paint.ColorLine.ColorStop[0].StopOffset.value == 0.0

    layer = builder.buildLayerV1Record(
        "a",
        {
            "format": 3,
            "colorLine": {"stops": [(0.0, 0), (1.0, 1)]},
            "c0": (0, 0),
            "c1": (10, 10),
            "r0": 4,
            "r1": 0,
        },
    )
    assert layer.Paint.Format == 3
    assert layer.Paint.r0.value == 4


def test_buildLayerV1List():
    layers = [
        ("a", 1),
        ("b", {"format": 1, "paletteIndex": 2, "alpha": 0.5}),
        (
            "c",
            {
                "format": 2,
                "colorLine": {"stops": [(0.0, 3), (1.0, 4)], "extend": "repeat"},
                "p0": (100, 200),
                "p1": (150, 250),
            },
        ),
        (
            "d",
            {
                "format": 3,
                "colorLine": {
                    "stops": [
                        {"offset": 0.0, "paletteIndex": 5},
                        {"offset": 0.5, "paletteIndex": 6, "alpha": 0.8},
                        {"offset": 1.0, "paletteIndex": 7},
                    ]
                },
                "c0": (50, 50),
                "c1": (75, 75),
                "r0": 30,
                "r1": 10,
            },
        ),
        builder.buildLayerV1Record("e", builder.buildSolidColorPaint(8)),
    ]
    layers = builder.buildLayerV1List(layers)

    assert layers.LayerCount == len(layers.LayerV1Record)
    assert all(isinstance(l, ot.LayerV1Record) for l in layers.LayerV1Record)


def test_buildBaseGlyphV1Record():
    baseGlyphRec = builder.buildBaseGlyphV1Record("a", [("b", 0), ("c", 1)])
    assert baseGlyphRec.BaseGlyph == "a"
    assert isinstance(baseGlyphRec.LayerV1List, ot.LayerV1List)

    layers = builder.buildLayerV1List([("b", 0), ("c", 1)])
    baseGlyphRec = builder.buildBaseGlyphV1Record("a", layers)
    assert baseGlyphRec.BaseGlyph == "a"
    assert baseGlyphRec.LayerV1List == layers


def test_buildBaseGlyphV1List():
    colorGlyphs = {
        "a": [("b", 0), ("c", 1)],
        "d": [
            ("e", {"format": 1, "paletteIndex": 2, "alpha": 0.8}),
            (
                "f",
                {
                    "format": 3,
                    "colorLine": {"stops": [(0.0, 3), (1.0, 4)], "extend": "reflect"},
                    "c0": (0, 0),
                    "c1": (0, 0),
                    "r0": 10,
                    "r1": 0,
                },
            ),
        ],
        "g": builder.buildLayerV1List([("h", 5)]),
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

    baseGlyphs = builder.buildBaseGlyphV1List(colorGlyphs, glyphMap)
    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphV1Record[0].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphV1Record[1].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphV1Record[2].BaseGlyph == "g"

    baseGlyphs = builder.buildBaseGlyphV1List(colorGlyphs)
    assert baseGlyphs.BaseGlyphCount == len(colorGlyphs)
    assert baseGlyphs.BaseGlyphV1Record[0].BaseGlyph == "a"
    assert baseGlyphs.BaseGlyphV1Record[1].BaseGlyph == "d"
    assert baseGlyphs.BaseGlyphV1Record[2].BaseGlyph == "g"


def test_splitSolidAndGradientGlyphs():
    colorGlyphs = {
        "a": [
            ("b", 0),
            ("c", 1),
            ("d", {"format": 1, "paletteIndex": 2}),
            ("e", builder.buildSolidColorPaint(paletteIndex=3)),
        ]
    }

    colorGlyphsV0, colorGlyphsV1 = builder._splitSolidAndGradientGlyphs(colorGlyphs)

    assert colorGlyphsV0 == {"a": [("b", 0), ("c", 1), ("d", 2), ("e", 3)]}
    assert not colorGlyphsV1

    colorGlyphs = {
        "a": [("b", builder.buildSolidColorPaint(paletteIndex=0, alpha=0.0))]
    }

    colorGlyphsV0, colorGlyphsV1 = builder._splitSolidAndGradientGlyphs(colorGlyphs)

    assert not colorGlyphsV0
    assert colorGlyphsV1 == colorGlyphs

    colorGlyphs = {
        "a": [("b", 0)],
        "c": [
            ("d", 1),
            (
                "e",
                {
                    "format": 2,
                    "colorLine": {"stops": [(0.0, 2), (1.0, 3)]},
                    "p0": (0, 0),
                    "p1": (10, 10),
                },
            ),
        ],
    }

    colorGlyphsV0, colorGlyphsV1 = builder._splitSolidAndGradientGlyphs(colorGlyphs)

    assert colorGlyphsV0 == {"a": [("b", 0)]}
    assert "a" not in colorGlyphsV1
    assert "c" in colorGlyphsV1
    assert len(colorGlyphsV1["c"]) == 2

    layer_d = colorGlyphsV1["c"][0]
    assert layer_d[0] == "d"
    assert isinstance(layer_d[1], ot.Paint)
    assert layer_d[1].Format == 1

    layer_e = colorGlyphsV1["c"][1]
    assert layer_e[0] == "e"
    assert isinstance(layer_e[1], ot.Paint)
    assert layer_e[1].Format == 2


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
                            "format": 3,
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
                    ("c", {"format": 1, "paletteIndex": 2, "alpha": 0.8}),
                ],
                "d": [
                    (
                        "e",
                        {
                            "format": 2,
                            "colorLine": {
                                "stops": [(0.0, 2), (1.0, 3)],
                                "extend": "reflect",
                            },
                            "p0": (1, 2),
                            "p1": (3, 4),
                            "p2": (2, 2),
                        },
                    )
                ],
            }
        )
        assert colr.version == 1
        assert not hasattr(colr, "ColorLayers")
        assert hasattr(colr, "table")
        assert isinstance(colr.table, ot.COLR)
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
                            "format": 2,
                            "colorLine": {"stops": [(0.0, 2), (1.0, 3)]},
                            "p0": (1, 2),
                            "p1": (3, 4),
                            "p2": (2, 2),
                        },
                    )
                ],
            }
        )
        assert colr.version == 1
        assert not hasattr(colr, "ColorLayers")
        assert hasattr(colr, "table")
        assert isinstance(colr.table, ot.COLR)
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
        assert isinstance(
            colr.table.BaseGlyphV1List.BaseGlyphV1Record[0].LayerV1List, ot.LayerV1List
        )
        assert (
            colr.table.BaseGlyphV1List.BaseGlyphV1Record[0]
            .LayerV1List.LayerV1Record[0]
            .LayerGlyph
            == "e"
        )

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
