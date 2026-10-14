from copy import deepcopy
from io import BytesIO

import pytest

from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.builder import (
    buildVarDevTable,
    buildVarData,
    buildVarStore,
    buildVarRegionList,
)
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.misc.roundTools import otRound


def roundtrip(font):
    stream = BytesIO()
    font.save(stream)
    stream.seek(0)
    return TTFont(stream)


def table(typ, **fields):
    obj = getattr(ot, typ)()
    obj.populateDefaults()
    obj.__dict__.update(fields)
    return obj


@pytest.fixture
def font():
    fb = FontBuilder(1000, isTTF=True)
    names = [".notdef", "a", "b"]
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({0x61: "a", 0x62: "b"})
    pen = TTGlyphPen(None)
    fb.setupGlyf({name: pen.glyph() for name in names})
    fb.setupHorizontalMetrics({name: (600, 0) for name in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "JSTF Variations", "styleName": "Regular"})
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200
    )
    fb.setupPost()
    fb.setupFvar([("wght", 0, 0, 1, "Weight"), ("wdth", 0, 0, 1, "Width")], [])
    f = fb.font
    addOpenTypeFeaturesFromString(
        f,
        "feature kern { pos a <10 20 30 0>; } kern; feature curs { pos cursive a <anchor 100 200> <anchor 300 400>; } curs;",
    )
    lookups = f["GPOS"].table.LookupList.Lookup
    single = lookups[0].SubTable[0]
    single.Value.XPlaDevice = buildVarDevTable(2)
    single.Value.YPlaDevice = buildVarDevTable(3)
    single.ValueFormat |= 0x30
    anchor = lookups[1].SubTable[0].EntryExitRecord[0].EntryAnchor
    anchor.Format = 3
    anchor.XDeviceTable = buildVarDevTable(4)
    anchor.YDeviceTable = buildVarDevTable(5)
    priority = table(
        "JstfPriority",
        ShrinkageJstfMax=table("JstfMax", Lookup=deepcopy(lookups)),
        ExtensionJstfMax=table("JstfMax", Lookup=deepcopy(lookups)),
    )
    lang = table("JstfLangSys", JstfPriority=[priority])
    script = table(
        "JstfScript",
        DefJstfLangSys=lang,
        JstfLangSysRecord=[
            table(
                "JstfLangSysRecord", JstfLangSysTag="ENG ", JstfLangSys=deepcopy(lang)
            )
        ],
    )
    f["JSTF"] = newTable("JSTF")
    f["JSTF"].table = table(
        "JSTF",
        Version=0x00010000,
        JstfScriptRecord=[
            table("JstfScriptRecord", JstfScriptTag="latn", JstfScript=script)
        ],
    )
    del f["GPOS"]
    if "GDEF" not in f:
        f["GDEF"] = newTable("GDEF")
    gdef = getattr(f["GDEF"], "table", None)
    if gdef is None:
        gdef = f["GDEF"].table = ot.GDEF()
    gdef.Version = 0x00010003
    gdef.populateDefaults()
    gdef.VarStore = buildVarStore(
        buildVarRegionList(
            [{"wght": (0, 1, 1)}, {"wdth": (0, 1, 1)}], ["wght", "wdth"]
        ),
        [
            buildVarData(
                [0, 1], [[999, -999], [0, 0], [10, 20], [-20, 30], [30, -10], [40, -20]]
            )
        ],
    )
    return roundtrip(f)


def values(f):
    script = f["JSTF"].table.JstfScriptRecord[0].JstfScript
    for lang in [script.DefJstfLangSys, script.JstfLangSysRecord[0].JstfLangSys]:
        p = lang.JstfPriority[0]
        for maxval in [p.ShrinkageJstfMax, p.ExtensionJstfMax]:
            yield maxval.Lookup[0].SubTable[0].Value
            yield maxval.Lookup[1].SubTable[0].EntryExitRecord[0].EntryAnchor


def check_values(font, weight, width):
    store = None
    if "GDEF" in font and getattr(font["GDEF"].table, "VarStore", None) is not None:
        store = VarStoreInstancer(
            font["GDEF"].table.VarStore, font["fvar"].axes, {"wdth": width}
        )
    for record in values(font):
        if hasattr(record, "XPlacement"):
            fields = [
                ("XPlacement", "XPlaDevice", 10, 10, 20),
                ("YPlacement", "YPlaDevice", 20, -20, 30),
            ]
            assert record.XAdvance == 30
        else:
            fields = [
                ("XCoordinate", "XDeviceTable", 100, 30, -10),
                ("YCoordinate", "YDeviceTable", 200, 40, -20),
            ]
        for name, device_name, base, dw, dd in fields:
            value = getattr(record, name)
            device = getattr(record, device_name, None)
            if device is not None:
                assert store is not None
                value += store[(device.StartSize << 16) | device.EndSize]
            assert value == base + otRound(weight * dw) + width * dd


@pytest.mark.parametrize("weight", [0, 0.5, 1])
def test_full_jstf_instance(font, weight):
    result = roundtrip(instantiateVariableFont(font, {"wght": weight, "wdth": 0}))
    assert "fvar" not in result and "GDEF" not in result
    check_values(result, weight, 0)
    for value in values(result):
        assert not any("Device" in name for name in value.__dict__)


@pytest.mark.parametrize("weight", [0, 0.5, 1])
def test_partial_jstf_instance_remaps_and_composes(font, weight):
    result = roundtrip(instantiateVariableFont(font, {"wght": weight}))
    for width in (0, 0.5, 1):
        check_values(result, weight, width)
        composed = roundtrip(instantiateVariableFont(result, {"wdth": width}))
        direct = roundtrip(
            instantiateVariableFont(font, {"wght": weight, "wdth": width})
        )
        assert composed["JSTF"].compile(composed) == direct["JSTF"].compile(direct)


def test_optimizer_remaps_jstf_devices(font, tmp_path):
    from fontTools.varLib.varStore import main

    source = tmp_path / "source.ttf"
    dest = tmp_path / "optimized.ttf"
    font.save(source)
    main([str(source), str(dest)])
    result = instantiateVariableFont(TTFont(dest), {"wght": 1})
    check_values(result, 1, 0.5)


def test_subset_preserves_passthrough_jstf_variation_rows(font):
    from fontTools import subset

    options = subset.Options()
    options.drop_tables.remove("JSTF")
    options.passthrough_tables = True
    options.retain_gids = True
    options.glyph_names = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=font.getGlyphOrder())
    subsetter.subset(font)
    result = instantiateVariableFont(roundtrip(font), {"wght": 1})
    check_values(result, 1, 0.5)


@pytest.mark.parametrize("full", [False, True])
@pytest.mark.parametrize("delta", [1, 3, 7])
def test_jstf_preserves_ppem_devices(font, full, delta):
    from fontTools.otlLib.builder import buildDevice

    for value in values(font):
        if hasattr(value, "XPlacement"):
            value.YPlaDevice = buildDevice({10: delta})
        else:
            value.YDeviceTable = buildDevice({10: delta})
    limits = {"wght": 1}
    if full:
        limits["wdth"] = 0
    result = roundtrip(instantiateVariableFont(font, limits))
    for value in values(result):
        if hasattr(value, "XPlacement"):
            assert value.XPlacement == 20
            assert value.YPlacement == 20
            assert value.YPlaDevice.DeltaValue == [delta]
        else:
            assert value.Format == 3
            assert value.XCoordinate == 130
            assert value.YCoordinate == 200
            assert value.YDeviceTable.DeltaValue == [delta]
