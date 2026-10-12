from io import BytesIO

import pytest

from fontTools.fontBuilder import FontBuilder
from fontTools.otlLib.builder import buildMathTable, buildDevice
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.builder import (
    buildVarDevTable,
    buildVarData,
    buildVarRegionList,
    buildVarStore,
)
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.misc.roundTools import otRound

BASES = {
    "leading": (100, 10, 20),
    "axis": (200, -20, 30),
    "italic_a": (10, 30, -10),
    "italic_b": (20, 40, -20),
    "accent_a": (300, 50, 5),
    "accent_b": (400, 60, -5),
    "height": (50, 70, 7),
    "kern_0": (70, 80, 8),
    "kern_1": (80, 90, 9),
    "assembly": (40, 100, 10),
}


def values(font):
    math = font["MATH"].table
    result = {
        "leading": math.MathConstants.MathLeading,
        "axis": math.MathConstants.AxisHeight,
    }
    glyphs = math.MathGlyphInfo
    info = glyphs.MathItalicsCorrectionInfo
    result.update(
        ("italic_" + name, value)
        for name, value in zip(info.Coverage.glyphs, info.ItalicsCorrection)
    )
    info = glyphs.MathTopAccentAttachment
    result.update(
        ("accent_" + name, value)
        for name, value in zip(info.TopAccentCoverage.glyphs, info.TopAccentAttachment)
    )
    kern = glyphs.MathKernInfo.MathKernInfoRecords[0].TopRightMathKern
    result["height"] = kern.CorrectionHeight[0]
    result.update(("kern_" + str(i), value) for i, value in enumerate(kern.KernValue))
    result["assembly"] = math.MathVariants.VertGlyphConstruction[
        0
    ].GlyphAssembly.ItalicsCorrection
    return result


def roundtrip(font):
    stream = BytesIO()
    font.save(stream)
    stream.seek(0)
    return TTFont(stream)


@pytest.fixture
def font():
    fb = FontBuilder(1000, isTTF=True)
    names = [".notdef", "a", "b"]
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({0x61: "a", 0x62: "b"})
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0))
    pen.lineTo((500, 0))
    pen.lineTo((500, 500))
    pen.closePath()
    fb.setupGlyf({name: pen.glyph() for name in names})
    fb.setupHorizontalMetrics({name: (600, 0) for name in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Math Variations", "styleName": "Regular"})
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200
    )
    fb.setupPost()
    fb.setupFvar([("wght", 0, 0, 1, "Weight"), ("wdth", 0, 0, 1, "Width")], [])
    font = fb.font
    buildMathTable(
        font,
        constants={
            "MathLeading": 100,
            "AxisHeight": 200,
            "AccentBaseHeight": 500,
            "FlattenedAccentBaseHeight": 600,
        },
        italicsCorrections={"a": 10, "b": 20},
        topAccentAttachments={"a": 300, "b": 400},
        mathKerns={"a": {"TopRight": ([50], [70, 80])}},
        vertGlyphAssembly={"a": ([("a", 0, 0, 0, 500)], 40)},
    )
    rows = [[999, -999], [0, 0]]
    for name, record in values(font).items():
        record.DeviceTable = buildVarDevTable(len(rows))
        rows.append(list(BASES[name][1:]))
    constants = font["MATH"].table.MathConstants
    constants.AccentBaseHeight.DeviceTable = buildVarDevTable(ot.NO_VARIATION_INDEX)
    constants.FlattenedAccentBaseHeight.DeviceTable = buildDevice({10: 1})
    font["GDEF"] = newTable("GDEF")
    gdef = font["GDEF"].table = ot.GDEF()
    gdef.Version = 0x00010003
    gdef.populateDefaults()
    gdef.VarStore = buildVarStore(
        buildVarRegionList(
            [{"wght": (0, 1, 1)}, {"wdth": (0, 1, 1)}], ["wght", "wdth"]
        ),
        [buildVarData([0, 1], rows)],
    )
    return roundtrip(font)


def check_values(font, weight, width):
    store = None
    if "GDEF" in font and getattr(font["GDEF"].table, "VarStore", None) is not None:
        store = VarStoreInstancer(
            font["GDEF"].table.VarStore, font["fvar"].axes, {"wdth": width}
        )
    for name, record in values(font).items():
        base, dw, dd = BASES[name]
        value = record.Value
        if record.DeviceTable is not None:
            dev = record.DeviceTable
            assert dev.DeltaFormat == 0x8000
            assert store is not None
            value += store[(dev.StartSize << 16) | dev.EndSize]
        assert value == base + otRound(weight * dw) + width * dd, name
    constants = font["MATH"].table.MathConstants
    assert constants.AccentBaseHeight.Value == 500
    assert constants.FlattenedAccentBaseHeight.DeviceTable.DeltaFormat == 1
    assert constants.FlattenedAccentBaseHeight.DeviceTable.DeltaValue == [1]


@pytest.mark.parametrize("weight", [0, 0.5, 1])
def test_full_math_instance_folds_all_record_types(font, weight):
    result = roundtrip(instantiateVariableFont(font, {"wght": weight, "wdth": 0}))
    assert "fvar" not in result and "GDEF" not in result
    assert all(value.DeviceTable is None for value in values(result).values())
    assert result["MATH"].table.MathConstants.AccentBaseHeight.DeviceTable is None
    check_values(result, weight, 0)


@pytest.mark.parametrize("weight", [0, 0.5, 1])
def test_partial_math_instance_remaps_indices_and_composes(font, weight):
    result = roundtrip(instantiateVariableFont(font, {"wght": weight}))
    assert [axis.axisTag for axis in result["fvar"].axes] == ["wdth"]
    for width in (0, 0.5, 1):
        check_values(result, weight, width)
        full = roundtrip(instantiateVariableFont(result, {"wdth": width}))
        direct = roundtrip(
            instantiateVariableFont(font, {"wght": weight, "wdth": width})
        )
        assert full.getTableData("MATH") == direct.getTableData("MATH")


def test_subset_retains_math_only_variation_rows(font):
    from fontTools import subset

    options = subset.Options()
    options.glyph_names = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(glyphs=["a"])
    subsetter.subset(font)
    font = roundtrip(font)
    assert "b" not in font.getGlyphOrder()
    result = roundtrip(instantiateVariableFont(font, {"wght": 1}))
    check_values(result, 1, 1)


def test_varstore_cli_remaps_math_indices(font, tmp_path):
    from fontTools.varLib.varStore import main

    source, output = tmp_path / "source.ttf", tmp_path / "optimized.ttf"
    font.save(source)
    main([str(source), str(output)])
    result = roundtrip(instantiateVariableFont(TTFont(output), {"wght": 1}))
    check_values(result, 1, 1)


def test_in_memory_records_without_device_attribute(font):
    del font["MATH"].table.MathConstants.FractionRuleThickness.DeviceTable
    result = roundtrip(instantiateVariableFont(font, {"wght": 1, "wdth": 0}))
    check_values(result, 1, 0)
