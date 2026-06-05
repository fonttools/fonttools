from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.otData import otData


TABLES = dict(otData)


def field(table, name):
    return next(field for field in TABLES[table] if field.name == name)


def test_extended_layout_formats():
    assert set(otTables.Coverage.convertersByName) == {1, 2, 3, 4}
    assert set(otTables.ClassDef.convertersByName) == {1, 2, 3, 4}
    assert set(otTables.ContextSubst.convertersByName) == {1, 2, 3, 4, 5, 6}
    assert set(otTables.ContextPos.convertersByName) == {1, 2, 3, 4, 5, 6}
    assert set(otTables.ChainContextSubst.convertersByName) == {1, 2, 3, 4, 5}
    assert set(otTables.ChainContextPos.convertersByName) == {1, 2, 3, 4, 5}


def test_extended_layout_header_fields():
    for table in ("GSUB", "GPOS"):
        assert field(table, "ScriptList2").type == "LOffsetTo(ScriptList)"
        assert field(table, "FeatureList2").type == "LOffsetTo(FeatureList)"
        assert field(table, "LookupList2").type == "LOffsetTo(LookupList)"

    assert field("GDEF", "GlyphClassDef2").type == "LOffsetTo(ClassDef)"
    assert field("GDEF", "LigCaretList2").type == "LOffsetTo(LigCaretList2)"
    assert field("JSTF", "JstfScriptRecord2").condition == "Version >= 0x00010001"


def test_extended_context_count_exceptions():
    # These counts remain 16-bit despite the surrounding extended offsets and
    # glyph IDs. This matches the corrected model implemented by HarfBuzz.
    for name in (
        "BacktrackGlyphCount",
        "InputGlyphCount",
        "LookAheadGlyphCount",
    ):
        assert field("ChainedSeqRule2", name).type == "uint16"

    assert field("ReverseChainSingleSubstFormat2", "BacktrackGlyphCount").type == (
        "uint16"
    )
    assert field("ReverseChainSingleSubstFormat2", "LookAheadGlyphCount").type == (
        "uint16"
    )
