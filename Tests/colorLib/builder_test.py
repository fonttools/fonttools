from fontTools.ttLib import newTable
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
