from io import BytesIO
from pathlib import Path

import pytest

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.beyond64k import lower_tables, upper_tables


DATA_DIR = Path(__file__).parent / "data"


def test_round_trip_companion_tables():
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)

    upper_tables(font)

    assert {"GLYF", "LOCA", "MAXP", "HHEA", "HMTX"} <= set(font.keys())
    assert not {"glyf", "loca", "maxp", "hhea", "hmtx"} & set(font.keys())

    data = BytesIO()
    font.save(data)
    data.seek(0)
    font = TTFont(data)

    lower_tables(font)

    assert {"glyf", "loca", "maxp", "hhea", "hmtx"} <= set(font.keys())
    assert not {"GLYF", "LOCA", "MAXP", "HHEA", "HMTX"} & set(font.keys())

    data = BytesIO()
    font.save(data)
    data.seek(0)
    assert TTFont(data).getGlyphOrder() == font.getGlyphOrder()


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


def test_lower_rejects_large_glyph_count():
    font = TTFont()
    font["MAXP"] = newTable("MAXP")
    font["MAXP"].numGlyphs = 0x10000

    with pytest.raises(ValueError, match="does not fit"):
        lower_tables(font, tables={"maxp"}, validate=False)


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
