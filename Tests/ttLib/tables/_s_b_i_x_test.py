from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.sbixGlyph import Glyph


@pytest.fixture
def sbix_font():
    font = TTFont()
    font.importXML(Path(__file__).resolve().parents[2] / "subset" / "data" / "sbix.ttx")
    return font


def test_external_images_round_trip_without_overwriting_other_strikes_or_tables(
    sbix_font, tmp_path
):
    expected = sbix_font.getTableData("sbix")
    other_bitmap = tmp_path / "bitmaps" / "strike20" / "X.png"
    other_bitmap.parent.mkdir(parents=True)
    other_data = sbix_font["sbix"].strikes[20].glyphs["Y"].imageData
    other_bitmap.write_bytes(other_data)

    path = tmp_path / "font.ttx"
    sbix_font.saveXML(path, bitmapGlyphDataFormat="extfile")
    for strike_xml in ET.parse(path).findall("./sbix/strike"):
        ppem = int(strike_xml.find("ppem").attrib["value"])
        for glyph_xml in strike_xml.findall("glyph"):
            image = glyph_xml.find("extfileimagedata")
            assert image is not None
            assert glyph_xml.find("hexdata") is None
            glyph = sbix_font["sbix"].strikes[ppem].glyphs[glyph_xml.attrib["name"]]
            assert Path(image.attrib["value"]).read_bytes() == glyph.imageData
    assert other_bitmap.read_bytes() == other_data

    restored = TTFont()
    restored.importXML(path)
    assert restored.getTableData("sbix") == expected


@pytest.mark.parametrize("data_format", ["raw", "extfile"])
def test_empty_and_reference_glyphs_keep_their_records(
    sbix_font, tmp_path, data_format
):
    sbix_font.setGlyphOrder([".notdef", "X", "Y", "Z"])
    strike = sbix_font["sbix"].strikes[20]
    sbix_font["sbix"].strikes = {20: strike}
    strike.glyphs[".notdef"] = Glyph(glyphName=".notdef")
    strike.glyphs["Y"] = Glyph(
        glyphName="Y", graphicType="dupe", referenceGlyphName="X", originOffsetX=-4
    )
    strike.glyphs["Z"] = Glyph(
        glyphName="Z", graphicType="flip", referenceGlyphName="X", originOffsetY=8
    )
    expected = sbix_font.getTableData("sbix")
    path = tmp_path / "font.ttx"
    sbix_font.saveXML(
        path, tables=["GlyphOrder", "sbix"], bitmapGlyphDataFormat=data_format
    )
    root = ET.parse(path)
    data_tag = "hexdata" if data_format == "raw" else "extfileimagedata"
    assert root.find(f"./sbix/strike/glyph[@name='X']/{data_tag}") is not None
    for name in ["Y", "Z"]:
        glyph_xml = root.find(f"./sbix/strike/glyph[@name='{name}']")
        assert glyph_xml.find("ref").attrib["glyphname"] == "X"
        assert glyph_xml.find("hexdata") is None
        assert glyph_xml.find("extfileimagedata") is None
    assert list(root.find("./sbix/strike/glyph[@name='.notdef']")) == []

    restored = TTFont()
    restored.importXML(path)
    assert restored.getTableData("sbix") == expected


def test_external_paths_contain_glyph_names_and_graphic_types(sbix_font, tmp_path):
    sbix_font.setGlyphOrder([".notdef", "../X", "%..%2FX"])
    strike = sbix_font["sbix"].strikes[20]
    sbix_font["sbix"].strikes = {20: strike}
    for old_name, new_name in [("X", "../X"), ("Y", "%..%2FX")]:
        glyph = strike.glyphs.pop(old_name)
        glyph.glyphName = new_name
        strike.glyphs[new_name] = glyph
    strike.glyphs["../X"].graphicType = "../x"
    expected = sbix_font.getTableData("sbix")
    path = tmp_path / "font.ttx"
    sbix_font.saveXML(
        path, tables=["GlyphOrder", "sbix"], bitmapGlyphDataFormat="extfile"
    )
    for glyph_xml in ET.parse(path).findall("./sbix/strike/glyph"):
        image = glyph_xml.find("extfileimagedata")
        assert image is not None
        image_path = Path(image.attrib["value"]).resolve()
        assert image_path.is_relative_to(tmp_path.resolve())
        assert (
            image_path.read_bytes() == strike.glyphs[glyph_xml.attrib["name"]].imageData
        )

    restored = TTFont()
    restored.importXML(path)
    assert restored.getTableData("sbix") == expected
