from fontTools import ttLib
from fontTools.misc.testTools import getXML, parseXML
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter

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
    "<COLR>",
    '  <Version value="0"/>',
    "  <!-- BaseGlyphRecordCount=1 -->",
    "  <BaseGlyphRecordArray>",
    '    <BaseGlyphRecord index="0">',
    '      <BaseGlyph value="glyph00006"/>',
    '      <FirstLayerIndex value="0"/>',
    '      <NumLayers value="3"/>',
    "    </BaseGlyphRecord>",
    "  </BaseGlyphRecordArray>",
    "  <LayerRecordArray>",
    '    <LayerRecord index="0">',
    '      <LayerGlyph value="glyph00007"/>',
    '      <PaletteIndex value="0"/>',
    "    </LayerRecord>",
    '    <LayerRecord index="1">',
    '      <LayerGlyph value="glyph00008"/>',
    '      <PaletteIndex value="1"/>',
    "    </LayerRecord>",
    '    <LayerRecord index="2">',
    '      <LayerGlyph value="glyph00009"/>',
    '      <PaletteIndex value="2"/>',
    "    </LayerRecord>",
    "  </LayerRecordArray>",
    "  <!-- LayerRecordCount=3 -->",
    "</COLR>",
]


def dump(table, ttFont=None):
    print("\n".join(getXML(table.toXML, ttFont)))


@pytest.fixture
def font():
    font = ttLib.TTFont()
    font.setGlyphOrder(["glyph%05d" % i for i in range(10)])
    return font


def test_decompile_and_compile(font):
    colr = ot.COLR()
    reader = OTTableReader(COLR_DATA)
    colr.decompile(reader, font)

    writer = OTTableWriter()
    colr.compile(writer, font)
    data = writer.getAllData()

    assert data == COLR_DATA


def test_decompile_and_dump_xml(font):
    colr = ot.COLR()
    reader = OTTableReader(COLR_DATA)
    colr.decompile(reader, font)

    dump(colr, font)
    assert getXML(colr.toXML, font) == COLR_XML
