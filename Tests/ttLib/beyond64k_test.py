from io import BytesIO
from pathlib import Path

import pytest

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.otlLib import builder
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.beyond64k import (
    _convert_contextual_layout_formats,
    _convert_explicit_layout_formats,
    lower_tables,
    main,
    upper_tables,
)
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent, flagCubic
from fontTools.ttLib.tables.otBase import CountReference, OTTableWriter
from fontTools.ttLib.tables.otTraverse import dfs_base_table


DATA_DIR = Path(__file__).parent / "data"


def layout_subtables(font, tag, table_type):
    return [
        path[-1].value
        for path in dfs_base_table(font[tag].table)
        if isinstance(path[-1].value, table_type)
    ]


def glyph_paths(font):
    glyph_set = font.getGlyphSet()
    paths = {}
    for name in font.getGlyphOrder():
        pen = SVGPathPen(glyph_set)
        glyph_set[name].draw(pen)
        paths[name] = pen.getCommands()
    return paths


def normalized_uvs_dict(uvs_dict):
    return {
        selector: sorted(entries, key=lambda item: (item[1] is not None, item[0]))
        for selector, entries in uvs_dict.items()
    }


def assert_layout_formats(font, extended):
    coverage_formats = (3, 4) if extended else (1, 2)
    ligature_format = 2 if extended else 1
    for tag in ("GSUB", "GPOS"):
        for coverage in layout_subtables(font, tag, otTables.Coverage):
            coverage.preWrite(font)
            assert coverage.Format in coverage_formats
    for ligature in layout_subtables(font, "GSUB", otTables.LigatureSubst):
        raw_table = ligature.preWrite(font)
        assert ligature.Format == ligature_format
        raw_table["Coverage"].preWrite(font)
        assert raw_table["Coverage"].Format in coverage_formats


@pytest.mark.parametrize(
    "table_type,compact_format,extended_format,compact_nested,extended_nested",
    [
        (otTables.SinglePos, 1, 3, (), ()),
        (otTables.SinglePos, 2, 4, (), ()),
        (
            otTables.PairPos,
            1,
            3,
            (otTables.PairSet, otTables.PairValueRecord),
            (otTables.PairSet2, otTables.PairValue2),
        ),
        (otTables.PairPos, 2, 4, (), ()),
        (
            otTables.CursivePos,
            1,
            2,
            (otTables.EntryExitRecord,),
            (otTables.EntryExit2,),
        ),
        (
            otTables.MarkBasePos,
            1,
            2,
            (
                otTables.MarkArray,
                otTables.MarkRecord,
                otTables.BaseArray,
                otTables.BaseRecord,
            ),
            (
                otTables.MarkArray2,
                otTables.MarkRecord2,
                otTables.BaseArray2,
                otTables.BaseRecord2,
            ),
        ),
        (
            otTables.MarkLigPos,
            1,
            2,
            (
                otTables.MarkArray,
                otTables.MarkRecord,
                otTables.LigatureArray,
                otTables.LigatureAttach,
                otTables.ComponentRecord,
            ),
            (
                otTables.MarkArray2,
                otTables.MarkRecord2,
                otTables.LigatureArray2,
                otTables.LigatureAttach2,
                otTables.ComponentRecord2,
            ),
        ),
        (
            otTables.MarkMarkPos,
            1,
            2,
            (
                otTables.MarkArray,
                otTables.MarkRecord,
                otTables.Mark2Array,
                otTables.Mark2Record,
            ),
            (
                otTables.MarkArray2,
                otTables.MarkRecord2,
                otTables.Mark2Array2,
                otTables.Mark2Record2,
            ),
        ),
        (otTables.ReverseChainSingleSubst, 1, 2, (), ()),
    ],
)
def test_convert_explicit_layout_format(
    table_type,
    compact_format,
    extended_format,
    compact_nested,
    extended_nested,
):
    table = table_type()
    table.Format = compact_format
    populate_explicit_layout_table(table)

    _convert_explicit_layout_formats(table, True)

    assert table.Format == extended_format
    assert nested_types(table, compact_nested + extended_nested) == extended_nested

    _convert_explicit_layout_formats(table, False)

    assert table.Format == compact_format
    assert nested_types(table, compact_nested + extended_nested) == compact_nested


def populate_explicit_layout_table(table):
    if isinstance(table, otTables.PairPos) and table.Format == 1:
        pair_set = otTables.PairSet()
        pair_set.PairValueRecord = [otTables.PairValueRecord()]
        table.PairSet = [pair_set]
    elif isinstance(table, otTables.CursivePos):
        table.EntryExitRecord = [otTables.EntryExitRecord()]
    elif isinstance(table, otTables.MarkBasePos):
        table.MarkArray = otTables.MarkArray()
        table.MarkArray.MarkRecord = [otTables.MarkRecord()]
        table.BaseArray = otTables.BaseArray()
        table.BaseArray.BaseRecord = [otTables.BaseRecord()]
    elif isinstance(table, otTables.MarkLigPos):
        table.MarkArray = otTables.MarkArray()
        table.MarkArray.MarkRecord = [otTables.MarkRecord()]
        table.LigatureArray = otTables.LigatureArray()
        ligature_attach = otTables.LigatureAttach()
        ligature_attach.ComponentRecord = [otTables.ComponentRecord()]
        table.LigatureArray.LigatureAttach = [ligature_attach]
    elif isinstance(table, otTables.MarkMarkPos):
        table.Mark1Array = otTables.MarkArray()
        table.Mark1Array.MarkRecord = [otTables.MarkRecord()]
        table.Mark2Array = otTables.Mark2Array()
        table.Mark2Array.Mark2Record = [otTables.Mark2Record()]


def nested_types(table, types):
    return tuple(
        type(path[-1].value)
        for path in dfs_base_table(table, skip_root=True)
        if isinstance(path[-1].value, types)
    )


@pytest.mark.parametrize(
    "builder_type,lookup_prefix",
    [
        (builder.ChainContextSubstBuilder, "Subst"),
        (builder.ChainContextPosBuilder, "Pos"),
    ],
)
@pytest.mark.parametrize("chaining", [False, True])
def test_convert_contextual_layout_formats(builder_type, lookup_prefix, chaining):
    font = TTFont()
    font.setGlyphOrder([".notdef", "a", "b", "c", "d"])
    lookup_builder = builder_type(font, None)
    lookup = builder.SingleSubstBuilder(font, None)
    lookup.lookup_index = 3
    rule = builder.ChainContextualRule(
        [["a"]] if chaining else [],
        [["b"], ["c"]],
        [["d"]] if chaining else [],
        [[lookup], None],
    )
    ruleset = builder.ChainContextualRuleset()
    ruleset.addRule(rule)

    subtables = [
        lookup_builder.buildFormat1Subtable(ruleset, chaining),
        lookup_builder.buildFormat2Subtable(
            ruleset, ruleset.format2ClassDefs(), chaining
        ),
    ]
    if not chaining:
        subtables.append(lookup_builder.buildFormat3Subtable(rule, chaining))

    for compact_format, subtable in enumerate(subtables, 1):
        _convert_contextual_layout_formats(subtable, True)
        assert subtable.Format == compact_format + 3
        assert_contextual_layout_attributes(
            subtable, lookup_prefix, compact_format, chaining, extended=True
        )
        compile_layout_subtable(subtable, font)

        _convert_contextual_layout_formats(subtable, False)
        assert subtable.Format == compact_format
        assert_contextual_layout_attributes(
            subtable, lookup_prefix, compact_format, chaining, extended=False
        )
        compile_layout_subtable(subtable, font)


def assert_contextual_layout_attributes(
    table, lookup_prefix, format, chaining, extended
):
    compact_prefix = ("Chain" if chaining else "") + lookup_prefix[:3]
    compact_rule = compact_prefix + ("ClassRule" if format == 2 else "Rule")
    compact_rule_set = compact_prefix + ("ClassSet" if format == 2 else "RuleSet")
    extended_rule = ("Chained" if chaining else "") + (
        "ClassSeqRule" if format == 2 else "SeqRule"
    )
    extended_rule_set = extended_rule + "Set"

    if format in (1, 2):
        rule_set_name = extended_rule_set if extended else compact_rule_set
        rule_name = extended_rule if extended else compact_rule
        rule_set = next(value for value in getattr(table, rule_set_name) if value)
        rule = getattr(rule_set, rule_name)[0]
    else:
        rule = table

    lookup_count = "SeqLookupCount" if extended else lookup_prefix + "Count"
    lookup_record = "SeqLookupRecord" if extended else lookup_prefix + "LookupRecord"
    assert getattr(rule, lookup_count) == 1
    assert isinstance(
        getattr(rule, lookup_record)[0],
        (
            otTables.SeqLookup
            if extended
            else getattr(otTables, lookup_prefix + "LookupRecord")
        ),
    )

    if format in (1, 2):
        input_name = "InputSequence"
        if not extended:
            input_name = "Class" if format == 2 and not chaining else "Input"
        assert getattr(rule, input_name)
        if chaining:
            backtrack_name = "BacktrackSequence" if extended else "Backtrack"
            lookahead_name = "LookAheadSequence" if extended else "LookAhead"
            assert getattr(rule, backtrack_name)
            assert getattr(rule, lookahead_name)


def compile_layout_subtable(table, font):
    lookup_type = {"LookupType": None}
    writer = OTTableWriter(
        localState={"LookupType": CountReference(lookup_type, "LookupType")}
    )
    table.compile(writer, font)
    writer.getAllData()


def build_contextual_layout_font():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    addOpenTypeFeaturesFromString(
        font,
        """
        feature calt { sub period by ellipsis; } calt;
        feature kern { pos period -20; } kern;
        """,
    )
    lookup = builder.SingleSubstBuilder(font, None)
    lookup.lookup_index = 0
    rule = builder.ChainContextualRule(
        [["space"]], [["period"], ["ellipsis"]], [["space"]], [[lookup], None]
    )
    ruleset = builder.ChainContextualRuleset()
    ruleset.addRule(rule)

    for tag, builder_type in (
        ("GSUB", builder.ChainContextSubstBuilder),
        ("GPOS", builder.ChainContextPosBuilder),
    ):
        lookup_builder = builder_type(font, None)
        subtables = []
        for chaining in (False, True):
            subtables.extend(
                [
                    lookup_builder.buildFormat1Subtable(ruleset, chaining),
                    lookup_builder.buildFormat2Subtable(
                        ruleset, ruleset.format2ClassDefs(), chaining
                    ),
                ]
            )
            if not chaining:
                subtables.append(lookup_builder.buildFormat3Subtable(rule, chaining))
        lookups = [builder.buildLookup([subtable], table=tag) for subtable in subtables]
        font[tag].table.LookupList.Lookup = lookups
        font[tag].table.LookupList.LookupCount = len(lookups)
    return font


def assert_contextual_formats(font, extended):
    expected = {
        otTables.ContextSubst: [4, 5, 6] if extended else [1, 2, 3],
        otTables.ChainContextSubst: [4, 5] if extended else [1, 2],
        otTables.ContextPos: [4, 5, 6] if extended else [1, 2, 3],
        otTables.ChainContextPos: [4, 5] if extended else [1, 2],
    }
    for table_type, formats in expected.items():
        tag = "GSUB" if "Subst" in table_type.__name__ else "GPOS"
        subtables = layout_subtables(font, tag, table_type)
        assert [subtable.Format for subtable in subtables] == formats


def test_contextual_layout_end_to_end_round_trip():
    font = build_contextual_layout_font()

    upper_tables(font, tables={"GSUB", "GPOS"})
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert_contextual_formats(font, True)

    lower_tables(font, tables={"GSUB", "GPOS"})
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert_contextual_formats(font, False)


def test_gdef_end_to_end_round_trip():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    addOpenTypeFeaturesFromString(
        font,
        """
        table GDEF {
            GlyphClassDef [period], [ellipsis], , ;
            LigatureCaretByPos ellipsis 300;
        } GDEF;
        """,
    )

    upper_tables(font, tables={"GDEF"})
    table = font["GDEF"].table
    assert table.Version == 0x00010004
    assert table.GlyphClassDef is None
    assert table.GlyphClassDef2 is not None
    assert table.LigCaretList is None
    assert isinstance(table.LigCaretList2, otTables.LigCaretList2)

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    table = font["GDEF"].table
    assert table.Version == 0x00010004
    assert table.GlyphClassDef2 is not None
    assert isinstance(table.LigCaretList2, otTables.LigCaretList2)

    lower_tables(font, tables={"GDEF"})
    table = font["GDEF"].table
    assert table.Version == 0x00010000
    assert table.GlyphClassDef is not None
    assert table.GlyphClassDef2 is None
    assert isinstance(table.LigCaretList, otTables.LigCaretList)
    assert table.LigCaretList2 is None

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    table = font["GDEF"].table
    assert table.Version == 0x00010000
    assert table.GlyphClassDef is not None
    assert isinstance(table.LigCaretList, otTables.LigCaretList)


def test_base_end_to_end_round_trip():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    addOpenTypeFeaturesFromString(
        font,
        """
        table BASE {
            HorizAxis.BaseTagList romn;
            HorizAxis.BaseScriptList latn romn 0;
        } BASE;
        """,
    )
    coord = (
        font["BASE"]
        .table.HorizAxis.BaseScriptList.BaseScriptRecord[0]
        .BaseScript.BaseValues.BaseCoord[0]
    )
    coord.Format = 2
    coord.ReferenceGlyph = "period"
    coord.BaseCoordPoint = 0

    upper_tables(font, tables={"BASE"})
    assert coord.Format == 4
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    coord = (
        font["BASE"]
        .table.HorizAxis.BaseScriptList.BaseScriptRecord[0]
        .BaseScript.BaseValues.BaseCoord[0]
    )
    assert coord.Format == 4

    lower_tables(font, tables={"BASE"})
    assert coord.Format == 2
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    coord = (
        font["BASE"]
        .table.HorizAxis.BaseScriptList.BaseScriptRecord[0]
        .BaseScript.BaseValues.BaseCoord[0]
    )
    assert coord.Format == 2


def test_jstf_end_to_end_round_trip():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    font["JSTF"] = newTable("JSTF")
    table = font["JSTF"].table = otTables.JSTF()
    table.Version = 0x00010000
    table.JstfScriptCount = 1
    record = otTables.JstfScriptRecord()
    record.JstfScriptTag = "latn"
    record.JstfScript = otTables.JstfScript()
    record.JstfScript.ExtenderGlyph = otTables.ExtenderGlyph()
    record.JstfScript.ExtenderGlyph.GlyphCount = 1
    record.JstfScript.ExtenderGlyph.ExtenderGlyph = ["period"]
    record.JstfScript.DefJstfLangSys = None
    record.JstfScript.JstfLangSysCount = 0
    record.JstfScript.JstfLangSysRecord = []
    table.JstfScriptRecord = [record]

    upper_tables(font, tables={"JSTF"})
    table = font["JSTF"].table
    assert table.Version == 0x00010001
    assert getattr(table, "JstfScriptRecord", None) is None
    assert isinstance(table.JstfScriptRecord2[0], otTables.JstfScriptRecord2)
    assert isinstance(table.JstfScriptRecord2[0].JstfScript, otTables.JstfScript2)
    assert isinstance(
        table.JstfScriptRecord2[0].JstfScript.ExtenderGlyph, otTables.ExtenderGlyph2
    )
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert isinstance(
        font["JSTF"].table.JstfScriptRecord2[0].JstfScript.ExtenderGlyph,
        otTables.ExtenderGlyph2,
    )

    lower_tables(font, tables={"JSTF"})
    table = font["JSTF"].table
    assert table.Version == 0x00010000
    assert isinstance(table.JstfScriptRecord[0], otTables.JstfScriptRecord)
    assert isinstance(table.JstfScriptRecord[0].JstfScript, otTables.JstfScript)
    assert isinstance(
        table.JstfScriptRecord[0].JstfScript.ExtenderGlyph, otTables.ExtenderGlyph
    )
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert isinstance(
        font["JSTF"].table.JstfScriptRecord[0].JstfScript.ExtenderGlyph,
        otTables.ExtenderGlyph,
    )


def test_round_trip_companion_tables():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    expected_paths = glyph_paths(font)

    upper_tables(font)

    assert {"GLYF", "LOCA", "MAXP", "HHEA", "HMTX"} <= set(font.keys())
    assert not {"glyf", "loca", "maxp", "hhea", "hmtx"} & set(font.keys())

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert glyph_paths(font) == expected_paths

    lower_tables(font)

    assert {"glyf", "loca", "maxp", "hhea", "hmtx"} <= set(font.keys())
    assert not {"GLYF", "LOCA", "MAXP", "HHEA", "HMTX"} & set(font.keys())

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)
    assert font.getGlyphOrder() == list(expected_paths)
    assert glyph_paths(font) == expected_paths


def test_upper_tables_replaces_bmp_format4_cmap_with_format12():
    font = TTFont()
    font.setGlyphOrder(
        [".notdef"] + [f"glyph{i}" for i in range(1, 0x10000)] + ["highGlyph"]
    )

    cmap4 = CmapSubtable.newSubtable(4)
    cmap4.platformID = 3
    cmap4.platEncID = 1
    cmap4.language = 0
    cmap4.cmap = {0x41: "highGlyph"}

    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = [cmap4]

    upper_tables(font)

    assert [subtable.format for subtable in font["cmap"].tables] == [12]
    assert font["cmap"].tables[0].platformID == 3
    assert font["cmap"].tables[0].platEncID == 10
    assert font["cmap"].tables[0].cmap == {0x41: "highGlyph"}
    font["cmap"].compile(font)


def test_upper_tables_converts_high_uvs_format14_to_format15():
    font = TTFont()
    font.setGlyphOrder(
        [".notdef", "lowGlyph"]
        + [f"glyph{i}" for i in range(2, 0x10000)]
        + ["highGlyph"]
    )

    cmap14 = CmapSubtable.newSubtable(14)
    cmap14.platformID = 0
    cmap14.platEncID = 5
    cmap14.language = 0xFF
    cmap14.cmap = {}
    cmap14.uvsDict = {0xFE00: [(0x41, "highGlyph"), (0x42, None)]}

    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = [cmap14]

    upper_tables(font)

    assert [subtable.format for subtable in font["cmap"].tables] == [15]
    assert font["cmap"].tables[0].uvsDict == {
        0xFE00: [(0x41, "highGlyph"), (0x42, None)]
    }
    data = font["cmap"].tables[0].compile(font)
    cmap15 = CmapSubtable.newSubtable(15)
    cmap15.decompile(data, font)
    assert normalized_uvs_dict(cmap15.uvsDict) == normalized_uvs_dict(
        font["cmap"].tables[0].uvsDict
    )


def test_upper_tables_keeps_low_uvs_format14():
    font = TTFont()
    font.setGlyphOrder(
        [".notdef", "lowGlyph"]
        + [f"glyph{i}" for i in range(2, 0x10000)]
        + ["highGlyph"]
    )

    cmap14 = CmapSubtable.newSubtable(14)
    cmap14.platformID = 0
    cmap14.platEncID = 5
    cmap14.language = 0xFF
    cmap14.cmap = {}
    cmap14.uvsDict = {0xFE00: [(0x41, "lowGlyph"), (0x42, None)]}

    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = [cmap14]

    upper_tables(font)

    assert [subtable.format for subtable in font["cmap"].tables] == [14]
    font["cmap"].tables[0].compile(font)


def test_lower_tables_converts_format15_to_format14_when_safe():
    font = TTFont()
    font.setGlyphOrder([".notdef", "lowGlyph"])

    cmap15 = CmapSubtable.newSubtable(15)
    cmap15.platformID = 0
    cmap15.platEncID = 5
    cmap15.language = 0xFF
    cmap15.cmap = {}
    cmap15.uvsDict = {0xFE00: [(0x41, "lowGlyph"), (0x42, None)]}

    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = [cmap15]

    lower_tables(font, validate=False)

    assert [subtable.format for subtable in font["cmap"].tables] == [14]
    assert font["cmap"].tables[0].uvsDict == {
        0xFE00: [(0x41, "lowGlyph"), (0x42, None)]
    }
    font["cmap"].tables[0].compile(font)


def test_lower_tables_rejects_high_format15_uvs():
    font = TTFont()
    font.setGlyphOrder(
        [".notdef"] + [f"glyph{i}" for i in range(1, 0x10000)] + ["highGlyph"]
    )

    cmap15 = CmapSubtable.newSubtable(15)
    cmap15.platformID = 0
    cmap15.platEncID = 5
    cmap15.language = 0xFF
    cmap15.cmap = {}
    cmap15.uvsDict = {0xFE00: [(0x41, "highGlyph")]}

    font["cmap"] = newTable("cmap")
    font["cmap"].tableVersion = 0
    font["cmap"].tables = [cmap15]

    with pytest.raises(ValueError, match="format 15 glyph IDs"):
        lower_tables(font, validate=False)


def test_upper_tables_drops_beyond64k_post_glyph_names():
    font = TTFont()
    font.setGlyphOrder(
        [".notdef"] + [f"glyph{i}" for i in range(1, 0x10000)] + ["highGlyph"]
    )
    post = font["post"] = newTable("post")
    post.formatType = 2.0
    post.italicAngle = 0
    post.underlinePosition = 0
    post.underlineThickness = 0
    post.isFixedPitch = 0
    post.minMemType42 = 0
    post.maxMemType42 = 0
    post.minMemType1 = 0
    post.maxMemType1 = 0
    post.extraNames = ["highGlyph"]
    post.mapping = {"highGlyph": "highGlyph"}

    upper_tables(font)

    assert post.formatType == 3.0
    assert post.extraNames == []
    assert post.mapping == {}
    post.compile(font)


@pytest.mark.parametrize("tag", ["glyf", "GLYF"])
def test_accepts_either_table_spelling(tag):
    font = TTFont()
    font["glyf"] = newTable("glyf")

    upper_tables(font, tables={tag}, validate=False)

    assert "GLYF" in font
    assert "glyf" not in font


def test_validate_rejects_mixed_family_before_mutation():
    font = TTFont()
    font["glyf"] = newTable("glyf")
    font["loca"] = newTable("loca")

    with pytest.raises(ValueError, match="mixed beyond-64k table family"):
        upper_tables(font, tables={"glyf"})

    assert "glyf" in font
    assert "loca" in font
    assert "GLYF" not in font


def test_overwrite_replaces_existing_destination():
    font = TTFont()
    font["glyf"] = newTable("glyf")
    font["glyf"].marker = "source"
    font["GLYF"] = newTable("GLYF")
    font["GLYF"].marker = "destination"

    upper_tables(font, tables={"glyf"}, validate=False, overwrite=True)

    assert font["GLYF"].marker == "source"
    assert "glyf" not in font


def test_duplicate_destination_requires_overwrite():
    font = TTFont()
    font["glyf"] = newTable("glyf")
    font["GLYF"] = newTable("GLYF")

    with pytest.raises(ValueError, match="overwrite=True"):
        upper_tables(font, tables={"glyf"}, validate=False)


def test_missing_tables_are_ignored_by_default():
    upper_tables(TTFont(), tables={"glyf"})


def test_missing_tables_can_be_rejected():
    with pytest.raises(KeyError):
        upper_tables(TTFont(), tables={"glyf"}, ignore_missing=False)


def test_cli_help_documents_usage(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "fonttools ttLib.beyond64k upper input.ttf -o upper.ttf" in help_text
    assert "fonttools ttLib.beyond64k lower upper.ttf -o lower.ttf" in help_text
    assert "--no-validate" in help_text
    assert "--overwrite" in help_text


def test_lower_rejects_large_glyph_count():
    font = TTFont()
    font["MAXP"] = newTable("MAXP")
    font["MAXP"].numGlyphs = 0x10000

    with pytest.raises(ValueError, match="does not fit"):
        lower_tables(font, tables={"maxp"}, validate=False)


def test_lower_rejects_cubic_glyph():
    font = TTFont()
    font.setGlyphOrder([".notdef"])
    font["GLYF"] = newTable("GLYF")
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.flags = [flagCubic]
    font["GLYF"].glyphs = {".notdef": glyph}

    with pytest.raises(ValueError, match="cubic outlines"):
        lower_tables(font, tables={"glyf"}, validate=False)


def test_lower_rejects_large_component_glyph_id():
    font = TTFont()
    font.setGlyphOrder([".notdef"] + [f"glyph{i}" for i in range(0x10000)])
    font["GLYF"] = newTable("GLYF")
    glyph = Glyph()
    glyph.numberOfContours = -1
    component = GlyphComponent()
    component.glyphName = "glyph65535"
    glyph.components = [component]
    font["GLYF"].glyphs = {".notdef": glyph}

    with pytest.raises(ValueError, match="does not fit"):
        lower_tables(font, tables={"glyf"}, validate=False)


def test_layout_header_round_trip():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    addOpenTypeFeaturesFromString(
        font,
        """
        feature kern { pos period period -20; } kern;
        feature liga { sub period period by ellipsis; } liga;
        """,
    )

    upper_tables(font, tables={"GSUB", "GPOS"})

    for tag in ("GSUB", "GPOS"):
        table = font[tag].table
        assert table.Version == 0x00010002
        assert table.ScriptList is None
        assert table.FeatureList is None
        assert table.LookupList is None
        assert table.ScriptList2 is not None
        assert table.FeatureList2 is not None
        assert table.LookupList2 is not None
    assert_layout_formats(font, False)

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)

    lower_tables(font, tables={"GSUB", "GPOS"})

    for tag in ("GSUB", "GPOS"):
        table = font[tag].table
        assert table.Version == 0x00010000
        assert table.ScriptList is not None
        assert table.FeatureList is not None
        assert table.LookupList is not None
        assert table.ScriptList2 is None
        assert table.FeatureList2 is None
        assert table.LookupList2 is None
    assert_layout_formats(font, False)

    data = BytesIO()
    font.save(data)
    data.seek(0)
    TTFont(data)
