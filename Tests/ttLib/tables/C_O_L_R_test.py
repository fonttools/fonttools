from fontTools import ttLib
from fontTools.misc.testTools import getXML, parseXML
from fontTools.ttLib.tables.C_O_L_R_ import table_C_O_L_R_

import pytest


COLR_V0_DATA = (
    b"\x00\x00"  # Version (0)
    b"\x00\x01"  # BaseGlyphRecordCount (1)
    b"\x00\x00\x00\x0e"  # Offset to BaseGlyphRecordArray
    b"\x00\x00\x00\x14"  # Offset to LayerRecordArray
    b"\x00\x03"  # LayerRecordCount (3)
    b"\x00\x06"  # BaseGlyphRecord[0].BaseGlyph (6)
    b"\x00\x00"  # BaseGlyphRecord[0].FirstLayerIndex (0)
    b"\x00\x03"  # BaseGlyphRecord[0].NumLayers (3)
    b"\x00\x07"  # LayerRecord[0].LayerGlyph (7)
    b"\x00\x00"  # LayerRecord[0].PaletteIndex (0)
    b"\x00\x08"  # LayerRecord[1].LayerGlyph (8)
    b"\x00\x01"  # LayerRecord[1].PaletteIndex (1)
    b"\x00\t"  # LayerRecord[2].LayerGlyph (9)
    b"\x00\x02"  # LayerRecord[3].PaletteIndex (2)
)


COLR_V0_XML = [
    '<version value="0"/>',
    '<ColorGlyph name="glyph00006">',
    '  <layer colorID="0" name="glyph00007"/>',
    '  <layer colorID="1" name="glyph00008"/>',
    '  <layer colorID="2" name="glyph00009"/>',
    "</ColorGlyph>",
]


def dump(table, ttFont=None):
    print("\n".join(getXML(table.toXML, ttFont)))


@pytest.fixture
def font():
    font = ttLib.TTFont()
    font.setGlyphOrder(["glyph%05d" % i for i in range(30)])
    return font


class COLR_V0_Test(object):
    def test_decompile_and_compile(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V0_DATA, font)
        assert colr.compile(font) == COLR_V0_DATA

    def test_decompile_and_dump_xml(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V0_DATA, font)

        dump(colr, font)
        assert getXML(colr.toXML, font) == COLR_V0_XML

    def test_load_from_xml_and_compile(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V0_XML):
            colr.fromXML(name, attrs, content, font)

        assert colr.compile(font) == COLR_V0_DATA


COLR_V1_DATA = (
    b"\x00\x01"  # Version (1)
    b"\x00\x01"  # BaseGlyphRecordCount (1)
    b"\x00\x00\x00\x16"  # Offset to BaseGlyphRecordArray
    b"\x00\x00\x00\x1c"  # Offset to LayerRecordArray
    b"\x00\x03"  # LayerRecordCount (3)
    b"\x00\x00\x00("  # Offset to BaseGlyphV1Array
    b"\x00\x00\x00\x00"  # Offset to VarStore (NULL)
    b"\x00\x06"  # BaseGlyphRecord[0].BaseGlyph (6)
    b"\x00\x00"  # BaseGlyphRecord[0].FirstLayerIndex (0)
    b"\x00\x03"  # BaseGlyphRecord[0].NumLayers (3)
    b"\x00\x07"  # LayerRecord[0].LayerGlyph (7)
    b"\x00\x00"  # LayerRecord[0].PaletteIndex (0)
    b"\x00\x08"  # LayerRecord[1].LayerGlyph (8)
    b"\x00\x01"  # LayerRecord[1].PaletteIndex (1)
    b"\x00\t"  # LayerRecord[2].LayerGlyph (9)
    b"\x00\x02"  # LayerRecord[3].PaletteIndex (2)
    b"\x00\x00\x00\x01"  # BaseGlyphV1Array.BaseGlyphCount (1)
    b"\x00\n"  # BaseGlyphV1Array.BaseGlyphV1Record[0].BaseGlyph (10)
    b"\x00\x00\x00\n"  # Offset to LayerV1Array
    b"\x00\x00\x00\x03"  # LayerV1Array.LayerCount (3)
    b"\x00\x0b"  # LayerV1Array.LayerV1Record[0].LayerGlyph (11)
    b"\x00\x00\x00\x16"  # Offset to Paint
    b"\x00\x0c"  # LayerV1Array.LayerV1Record[1].LayerGlyph (12)
    b"\x00\x00\x00 "  # Offset to Paint
    b"\x00\r"  # LayerV1Array.LayerV1Record[2].LayerGlyph (13)
    b"\x00\x00\x00x"  # Offset to Paint
    b"\x00\x01"  # Paint.Format (1)
    b"\x00\x02"  # Paint.Color.PaletteIndex (2)
    b" \x00"  # Paint.Color.Transparency.value (0.5)
    b"\x00\x00\x00\x00"  # Paint.Color.Transparency.varIdx (0)
    b"\x00\x02"  # Paint.Format (2)
    b"\x00\x00\x00*"  # Offset to ColorLine
    b"\x00\x01"  # Paint.p0.x.value (1)
    b"\x00\x00\x00\x00"  # Paint.p0.x.varIdx (0)
    b"\x00\x02"  # Paint.p0.y.value (2)
    b"\x00\x00\x00\x00"  # Paint.p0.y.varIdx (0)
    b"\xff\xfd"  # Paint.p1.x.value (-3)
    b"\x00\x00\x00\x00"  # Paint.p1.x.varIdx (0)
    b"\xff\xfc"  # Paint.p1.y.value (-4)
    b"\x00\x00\x00\x00"  # Paint.p1.y.varIdx (0)
    b"\x00\x05"  # Paint.p2.x.value (5)
    b"\x00\x00\x00\x00"  # Paint.p2.y.varIdx (0)
    b"\x00\x06"  # Paint.p2.y.value (5)
    b"\x00\x00\x00\x00"  # Paint.p2.y.varIdx (0)
    b"\x00\x01"  # ColorLine.Extend (1 or "repeat")
    b"\x00\x03"  # ColorLine.StopCount (3)
    b"\x00\x00"  # ColorLine.ColorStop[0].StopOffset.value (0.0)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[0].StopOffset.varIdx (0)
    b"\x00\x03"  # ColorLine.ColorStop[0].Color.PaletteIndex (3)
    b"\x00\x00"  # ColorLine.ColorStop[0].Color.Transparency.value (0.0)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[0].Color.Transparency.varIdx (0)
    b" \x00"  # ColorLine.ColorStop[1].StopOffset.value (0.5)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[1].StopOffset.varIdx (0)
    b"\x00\x04"  # ColorLine.ColorStop[1].Color.PaletteIndex (4)
    b"\x00\x00"  # ColorLine.ColorStop[1].Color.Transparency.value (0.0)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[1].Color.Transparency.varIdx (0)
    b"@\x00"  # ColorLine.ColorStop[2].StopOffset.value (1.0)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[2].StopOffset.varIdx (0)
    b"\x00\x05"  # ColorLine.ColorStop[2].Color.PaletteIndex (5)
    b"\x00\x00"  # ColorLine.ColorStop[2].Color.Transparency.value (0.0)
    b"\x00\x00\x00\x00"  # ColorLine.ColorStop[2].Color.Transparency.varIdx (0)
    b"\x00\x03"  # Paint.Format (3)
    b"\x00\x00\x00."  # Offset to ColorLine
    b"\x00\x07"  # Paint.c0.x.value (7)
    b"\x00\x00\x00\x00"
    b"\x00\x08"  # Paint.c0.y.value (8)
    b"\x00\x00\x00\x00"
    b"\x00\t"  # Paint.c1.x.value (9)
    b"\x00\x00\x00\x00"
    b"\x00\n"  # Paint.c1.y.value (10)
    b"\x00\x00\x00\x00"
    b"\x00\x0b"  # Paint.r0.value (11)
    b"\x00\x00\x00\x00"
    b"\x00\x0c"  # Paint.r1.value (12)
    b"\x00\x00\x00\x00"
    b"\x00\x00\x00N"  # Offset to Affine2x2
    b"\x00\x00"  # ColorLine.Extend (0 or "pad")
    b"\x00\x02"  # ColorLine.StopCount (2)
    b"\x00\x00"  # ColorLine.ColorStop[0].StopOffset.value (0.0)
    b"\x00\x00\x00\x00"
    b"\x00\x06"  # ColorLine.ColorStop[0].Color.PaletteIndex (6)
    b"\x00\x00"
    b"\x00\x00\x00\x00"
    b"@\x00"  # ColorLine.ColorStop[1].StopOffset.value (1.0)
    b"\x00\x00\x00\x00"
    b"\x00\x07"  # ColorLine.ColorStop[1].Color.PaletteIndex (7)
    b"\x19\x9a"  # ColorLine.ColorStop[1].Color.Transparency.value (0.4)
    b"\x00\x00\x00\x00"
    b"\xff\xf3\x00\x00"  # Affine2x2.xx.value (-13)
    b"\x00\x00\x00\x00"
    b"\x00\x0e\x00\x00"  # Affine2x2.xy.value (14)
    b"\x00\x00\x00\x00"
    b"\x00\x0f\x00\x00"  # Affine2x2.yx.value (15)
    b"\x00\x00\x00\x00"
    b"\xff\xef\x00\x00"  # Affine2x2.yy.value (-17)
    b"\x00\x00\x00\x00"
)


COLR_V1_XML = [
    '<Version value="1"/>',
    "<!-- BaseGlyphRecordCount=1 -->",
    "<BaseGlyphRecordArray>",
    '  <BaseGlyphRecord index="0">',
    '    <BaseGlyph value="glyph00006"/>',
    '    <FirstLayerIndex value="0"/>',
    '    <NumLayers value="3"/>',
    "  </BaseGlyphRecord>",
    "</BaseGlyphRecordArray>",
    "<LayerRecordArray>",
    '  <LayerRecord index="0">',
    '    <LayerGlyph value="glyph00007"/>',
    '    <PaletteIndex value="0"/>',
    "  </LayerRecord>",
    '  <LayerRecord index="1">',
    '    <LayerGlyph value="glyph00008"/>',
    '    <PaletteIndex value="1"/>',
    "  </LayerRecord>",
    '  <LayerRecord index="2">',
    '    <LayerGlyph value="glyph00009"/>',
    '    <PaletteIndex value="2"/>',
    "  </LayerRecord>",
    "</LayerRecordArray>",
    "<!-- LayerRecordCount=3 -->",
    "<BaseGlyphV1Array>",
    "  <!-- BaseGlyphCount=1 -->",
    '  <BaseGlyphV1Record index="0">',
    '    <BaseGlyph value="glyph00010"/>',
    "    <LayerV1Array>",
    "      <!-- LayerCount=3 -->",
    '      <LayerV1Record index="0">',
    '        <LayerGlyph value="glyph00011"/>',
    '        <Paint Format="1">',
    "          <Color>",
    '            <PaletteIndex value="2"/>',
    '            <Transparency value="0.5"/>',
    "          </Color>",
    "        </Paint>",
    "      </LayerV1Record>",
    '      <LayerV1Record index="1">',
    '        <LayerGlyph value="glyph00012"/>',
    '        <Paint Format="2">',
    "          <ColorLine>",
    '            <Extend value="repeat"/>',
    "            <!-- StopCount=3 -->",
    '            <ColorStop index="0">',
    '              <StopOffset value="0.0"/>',
    "              <Color>",
    '                <PaletteIndex value="3"/>',
    '                <Transparency value="0.0"/>',
    "              </Color>",
    "            </ColorStop>",
    '            <ColorStop index="1">',
    '              <StopOffset value="0.5"/>',
    "              <Color>",
    '                <PaletteIndex value="4"/>',
    '                <Transparency value="0.0"/>',
    "              </Color>",
    "            </ColorStop>",
    '            <ColorStop index="2">',
    '              <StopOffset value="1.0"/>',
    "              <Color>",
    '                <PaletteIndex value="5"/>',
    '                <Transparency value="0.0"/>',
    "              </Color>",
    "            </ColorStop>",
    "          </ColorLine>",
    "          <p0>",
    '            <x value="1"/>',
    '            <y value="2"/>',
    "          </p0>",
    "          <p1>",
    '            <x value="-3"/>',
    '            <y value="-4"/>',
    "          </p1>",
    "          <p2>",
    '            <x value="5"/>',
    '            <y value="6"/>',
    "          </p2>",
    "        </Paint>",
    "      </LayerV1Record>",
    '      <LayerV1Record index="2">',
    '        <LayerGlyph value="glyph00013"/>',
    '        <Paint Format="3">',
    "          <ColorLine>",
    '            <Extend value="pad"/>',
    "            <!-- StopCount=2 -->",
    '            <ColorStop index="0">',
    '              <StopOffset value="0.0"/>',
    "              <Color>",
    '                <PaletteIndex value="6"/>',
    '                <Transparency value="0.0"/>',
    "              </Color>",
    "            </ColorStop>",
    '            <ColorStop index="1">',
    '              <StopOffset value="1.0"/>',
    "              <Color>",
    '                <PaletteIndex value="7"/>',
    '                <Transparency value="0.4"/>',
    "              </Color>",
    "            </ColorStop>",
    "          </ColorLine>",
    "          <c0>",
    '            <x value="7"/>',
    '            <y value="8"/>',
    "          </c0>",
    "          <c1>",
    '            <x value="9"/>',
    '            <y value="10"/>',
    "          </c1>",
    '          <r0 value="11"/>',
    '          <r1 value="12"/>',
    "          <Affine>",
    '            <xx value="-13.0"/>',
    '            <xy value="14.0"/>',
    '            <yx value="15.0"/>',
    '            <yy value="-17.0"/>',
    "          </Affine>",
    "        </Paint>",
    "      </LayerV1Record>",
    "    </LayerV1Array>",
    "  </BaseGlyphV1Record>",
    "</BaseGlyphV1Array>",
]


class COLR_V1_Test(object):
    def test_decompile_and_compile(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V1_DATA, font)
        assert colr.compile(font) == COLR_V1_DATA

    def test_decompile_and_dump_xml(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V1_DATA, font)

        dump(colr, font)
        assert getXML(colr.toXML, font) == COLR_V1_XML

    def test_load_from_xml_and_compile(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V1_XML):
            colr.fromXML(name, attrs, content, font)

        assert colr.compile(font) == COLR_V1_DATA
