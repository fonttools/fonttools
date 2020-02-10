from fontTools import ttLib
from fontTools.misc.testTools import getXML, parseXML
from fontTools.ttLib.tables.C_O_L_R_ import table_C_O_L_R_

import pytest


COLR_DATA = (
    b"\x00\x00"  # Version
    b"\x00\x01"  # BaseGlyphRecordCount
    b"\x00\x00\x00\x0e"  # Offset to BaseGlyphRecordArray
    b"\x00\x00\x00\x14"  # Offset to LayerRecordArray
    b"\x00\x03"  # LayerRecordCount
    b"\x00\x06"  # BaseGlyphRecord[0].BaseGlyph
    b"\x00\x00"  # BaseGlyphRecord[0].FirstLayerIndex
    b"\x00\x03"  # BaseGlyphRecord[0].NumLayers
    b"\x00\x07"  # LayerRecord[0].LayerGlyph
    b"\x00\x00"  # LayerRecord[0].PaletteIndex
    b"\x00\x08"  # LayerRecord[1].LayerGlyph
    b"\x00\x01"  # LayerRecord[1].PaletteIndex
    b"\x00\t"  # LayerRecord[2].LayerGlyph
    b"\x00\x02"  # LayerRecord[3].PaletteIndex
)


COLR_XML = [
    '<version value="0"/>',
    '<ColorGlyph name="glyph00006">',
    '  <layer colorID="0" name="glyph00007"/>',
    '  <layer colorID="1" name="glyph00008"/>',
    '  <layer colorID="2" name="glyph00009"/>',
    '</ColorGlyph>',
]


def dump(table, ttFont=None):
    print("\n".join(getXML(table.toXML, ttFont)))


@pytest.fixture
def font():
    font = ttLib.TTFont()
    font.setGlyphOrder(["glyph%05d" % i for i in range(10)])
    return font


def test_decompile_and_compile(font):
    colr = table_C_O_L_R_()
    colr.decompile(COLR_DATA, font)
    assert colr.compile(font) == COLR_DATA


def test_decompile_and_dump_xml(font):
    colr = table_C_O_L_R_()
    colr.decompile(COLR_DATA, font)

    dump(colr, font)
    assert getXML(colr.toXML, font) == COLR_XML
