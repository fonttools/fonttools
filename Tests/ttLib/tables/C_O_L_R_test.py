from fontTools import ttLib
from fontTools.misc.testTools import getXML, parseXML
from fontTools.ttLib.tables.C_O_L_R_ import table_C_O_L_R_

import binascii
import pytest


COLR_V0_SAMPLE = (
    (b"\x00\x00", "Version (0)"),
    (b"\x00\x01", "BaseGlyphRecordCount (1)"),
    (
        b"\x00\x00\x00\x0e",
        "Offset to BaseGlyphRecordArray from beginning of table (14)",
    ),
    (b"\x00\x00\x00\x14", "Offset to LayerRecordArray from beginning of table (20)"),
    (b"\x00\x03", "LayerRecordCount (3)"),
    (b"\x00\x06", "BaseGlyphRecord[0].BaseGlyph (6)"),
    (b"\x00\x00", "BaseGlyphRecord[0].FirstLayerIndex (0)"),
    (b"\x00\x03", "BaseGlyphRecord[0].NumLayers (3)"),
    (b"\x00\x07", "LayerRecord[0].LayerGlyph (7)"),
    (b"\x00\x00", "LayerRecord[0].PaletteIndex (0)"),
    (b"\x00\x08", "LayerRecord[1].LayerGlyph (8)"),
    (b"\x00\x01", "LayerRecord[1].PaletteIndex (1)"),
    (b"\x00\t", "LayerRecord[2].LayerGlyph (9)"),
    (b"\x00\x02", "LayerRecord[3].PaletteIndex (2)"),
)

COLR_V0_DATA = b"".join(t[0] for t in COLR_V0_SAMPLE)


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


def diff_binary_fragments(font_bytes, expected_fragments):
    pos = 0
    prev_desc = ""
    errors = 0
    for expected_bytes, description in expected_fragments:
        actual_bytes = font_bytes[pos : pos + len(expected_bytes)]
        if actual_bytes != expected_bytes:
            print(f'{description} (previous "{prev_desc}", actual_bytes: {"".join("%02x" % v for v in actual_bytes)} bytes: {str(font_bytes[pos:pos+16])}')
            errors += 1
        pos += len(expected_bytes)
        prev_desc = description
    assert errors == 0
    assert pos == len(
        font_bytes
    ), f"Leftover font bytes, used {pos} of {len(font_bytes)}"


@pytest.fixture
def font():
    font = ttLib.TTFont()
    font.setGlyphOrder(["glyph%05d" % i for i in range(30)])
    return font


class COLR_V0_Test(object):
    def test_decompile_and_compile(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V0_DATA, font)
        diff_binary_fragments(colr.compile(font), COLR_V0_SAMPLE)

    def test_decompile_and_dump_xml(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V0_DATA, font)

        dump(colr, font)
        assert getXML(colr.toXML, font) == COLR_V0_XML

    def test_load_from_xml_and_compile(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V0_XML):
            colr.fromXML(name, attrs, content, font)

        diff_binary_fragments(colr.compile(font), COLR_V0_SAMPLE)

    def test_round_trip_xml(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V0_XML):
            colr.fromXML(name, attrs, content, font)
        compiled = colr.compile(font)

        colr = table_C_O_L_R_()
        colr.decompile(compiled, font)
        assert getXML(colr.toXML, font) == COLR_V0_XML


COLR_V1_SAMPLE = (
    (b"\x00\x01", "Version (1)"),
    (b"\x00\x01", "BaseGlyphRecordCount (1)"),
    (
        b"\x00\x00\x00\x1a",
        "Offset to BaseGlyphRecordArray from beginning of table (26)",
    ),
    (b"\x00\x00\x00 ", "Offset to LayerRecordArray from beginning of table (32)"),
    (b"\x00\x03", "LayerRecordCount (3)"),
    (b"\x00\x00\x00,", "Offset to BaseGlyphV1List from beginning of table (44)"),
    (b"\x00\x00\x00\xac", "Offset to LayerV1List from beginning of table (172)"),
    (b"\x00\x00\x00\x00", "Offset to VarStore (NULL)"),
    (b"\x00\x06", "BaseGlyphRecord[0].BaseGlyph (6)"),
    (b"\x00\x00", "BaseGlyphRecord[0].FirstLayerIndex (0)"),
    (b"\x00\x03", "BaseGlyphRecord[0].NumLayers (3)"),
    (b"\x00\x07", "LayerRecord[0].LayerGlyph (7)"),
    (b"\x00\x00", "LayerRecord[0].PaletteIndex (0)"),
    (b"\x00\x08", "LayerRecord[1].LayerGlyph (8)"),
    (b"\x00\x01", "LayerRecord[1].PaletteIndex (1)"),
    (b"\x00\t", "LayerRecord[2].LayerGlyph (9)"),
    (b"\x00\x02", "LayerRecord[2].PaletteIndex (2)"),
    # BaseGlyphV1List
    (b"\x00\x00\x00\x03", "BaseGlyphV1List.BaseGlyphCount (3)"),
    (b"\x00\n", "BaseGlyphV1List.BaseGlyphV1Record[0].BaseGlyph (10)"),
    (
        b"\x00\x00\x00\x16",
        "Offset to Paint table from beginning of BaseGlyphV1List (22)",
    ),
    (b"\x00\x0e", "BaseGlyphV1List.BaseGlyphV1Record[1].BaseGlyph (14)"),
    (
        b"\x00\x00\x00\x1c",
        "Offset to Paint table from beginning of BaseGlyphV1List (28)",
    ),
    (b"\x00\x0f", "BaseGlyphV1List.BaseGlyphV1Record[2].BaseGlyph (15)"),
    (
        b"\x00\x00\x00\x5b",
        "Offset to Paint table from beginning of BaseGlyphV1List (91)",
    ),
    # BaseGlyphV1Record[0]
    (b"\x01", "BaseGlyphV1Record[0].Paint.Format (1)"),
    (b"\x04", "BaseGlyphV1Record[0].Paint.NumLayers (4)"),
    (b"\x00\x00\x00\x00", "BaseGlyphV1Record[0].Paint.FirstLayerIndex (0)"),
    # BaseGlyphV1Record[1]
    (b"\x14", "BaseGlyphV1Record[1].Paint.Format (20)"),
    (b"\x00\x00<", "Offset to SourcePaint from beginning of PaintComposite (60)"),
    (b"\x03", "BaseGlyphV1Record[1].Paint.CompositeMode [SRC_OVER] (3)"),
    (b"\x00\x00\x08", "Offset to BackdropPaint from beginning of PaintComposite (8)"),
    (b"\x0d", "BaseGlyphV1Record[1].Paint.BackdropPaint.Format (13)"),
    (b"\x00\x00\x34", "Offset to Paint from beginning of PaintVarTransform (52)"),
    (b"\x00\x01\x00\x00\xff\xff\xff\xff", "Affine2x3.xx.value (1.0)"),
    (b"\x00\x00\x00\x00\xff\xff\xff\xff", "Affine2x3.xy.value (0.0)"),
    (b"\x00\x00\x00\x00\xff\xff\xff\xff", "Affine2x3.yx.value (0.0)"),
    (b"\x00\x01\x00\x00\xff\xff\xff\xff", "Affine2x3.yy.value (1.0)"),
    (b"\x01\x2c\x00\x00\xff\xff\xff\xff", "Affine2x3.dx.value (300.0)"),
    (b"\x00\x00\x00\x00\xff\xff\xff\xff", "Affine2x3.dy.value (0.0)"),
    (b"\x0b", "BaseGlyphV1Record[1].Paint.SourcePaint.Format (11)"),
    (b"\x00\n", "BaseGlyphV1Record[1].Paint.SourcePaint.Glyph (10)"),
    # BaseGlyphV1Record[2]
    (b"\x0a", "BaseGlyphV1Record[2].Paint.Format (10)"),
    (b"\x00\x00\x06", "Offset to Paint subtable from beginning of PaintGlyph (6)"),
    (b"\x00\x0b", "BaseGlyphV1Record[2].Paint.Glyph (11)"),
    (b"\x08", "BaseGlyphV1Record[2].Paint.Paint.Format (8)"),
    (b"\x00\x00\x10", "Offset to ColorLine from beginning of PaintSweepGradient (16)"),
    (b"\x01\x03", "centerX (259)"),
    (b"\x01\x2c", "centerY (300)"),
    (b"\x00\x2d\x00\x00", "startAngle (45.0)"),
    (b"\x00\x87\x00\x00", "endAngle (135.0)"),
    (b"\x00", "ColorLine.Extend (0; pad)"),
    (b"\x00\x02", "ColorLine.StopCount (2)"),
    (b"\x00\x00", "ColorLine.ColorStop[0].StopOffset (0.0)"),
    (b"\x00\x03", "ColorLine.ColorStop[0].Color.PaletteIndex (3)"),
    (b"@\x00", "ColorLine.ColorStop[0].Color.Alpha (1.0)"),
    (b"@\x00", "ColorLine.ColorStop[1].StopOffset (1.0)"),
    (b"\x00\x05", "ColorLine.ColorStop[1].Color.PaletteIndex (5)"),
    (b"@\x00", "ColorLine.ColorStop[1].Color.Alpha (1.0)"),
    # LayerV1List
    (b"\x00\x00\x00\x04", "LayerV1List.LayerCount (4)"),
    (
        b"\x00\x00\x00\x14",
        "First Offset to Paint table from beginning of LayerV1List (20)",
    ),
    (
        b"\x00\x00\x00\x23",
        "Second Offset to Paint table from beginning of LayerV1List (35)",
    ),
    (
        b"\x00\x00\x00\x4e",
        "Third Offset to Paint table from beginning of LayerV1List (78)",
    ),
    (
        b"\x00\x00\x00\xb7",
        "Fourth Offset to Paint table from beginning of LayerV1List (183)",
    ),
    # PaintGlyph glyph00011
    (b"\x0a", "LayerV1List.Paint[0].Format (10)"),
    (b"\x00\x00\x06", "Offset24 to Paint subtable from beginning of PaintGlyph (6)"),
    (b"\x00\x0b", "LayerV1List.Paint[0].Glyph (glyph00011)"),
    # PaintVarSolid
    (b"\x03", "LayerV1List.Paint[0].Paint.Format (3)"),
    (b"\x00\x02", "Paint.Color.PaletteIndex (2)"),
    (b" \x00", "Paint.Color.Alpha.value (0.5)"),
    (b"\xff\xff\xff\xff", "Paint.Color.Alpha.varIdx (0xFFFFFFFF)"),
    # PaintGlyph glyph00012
    (b"\x0a", "LayerV1List.Paint[1].Format (10)"),
    (b"\x00\x00\x06", "Offset to Paint subtable from beginning of PaintGlyph (6)"),
    (b"\x00\x0c", "LayerV1List.Paint[1].Glyph (glyph00012)"),
    (b"\x04", "LayerV1List.Paint[1].Paint.Format (4)"),
    (b"\x00\x00\x10", "Offset to ColorLine from beginning of PaintLinearGradient (16)"),
    (b"\x00\x01", "Paint.x0 (1)"),
    (b"\x00\x02", "Paint.y0 (2)"),
    (b"\xff\xfd", "Paint.x1 (-3)"),
    (b"\xff\xfc", "Paint.y1 (-4)"),
    (b"\x00\x05", "Paint.x2 (5)"),
    (b"\x00\x06", "Paint.y2 (6)"),
    (b"\x01", "ColorLine.Extend (1; repeat)"),
    (b"\x00\x03", "ColorLine.StopCount (3)"),
    (b"\x00\x00", "ColorLine.ColorStop[0].StopOffset (0.0)"),
    (b"\x00\x03", "ColorLine.ColorStop[0].Color.PaletteIndex (3)"),
    (b"@\x00", "ColorLine.ColorStop[0].Color.Alpha (1.0)"),
    (b" \x00", "ColorLine.ColorStop[1].StopOffset (0.5)"),
    (b"\x00\x04", "ColorLine.ColorStop[1].Color.PaletteIndex (4)"),
    (b"@\x00", "ColorLine.ColorStop[1].Color.Alpha (1.0)"),
    (b"@\x00", "ColorLine.ColorStop[2].StopOffset (1.0)"),
    (b"\x00\x05", "ColorLine.ColorStop[2].Color.PaletteIndex (5)"),
    (b"@\x00", "ColorLine.ColorStop[2].Color.Alpha (1.0)"),
    # PaintGlyph glyph00013
    (b"\x0a", "LayerV1List.Paint[2].Format (10)"),
    (b"\x00\x00\x06", "Offset to Paint subtable from beginning of PaintGlyph (6)"),
    (b"\x00\r", "LayerV1List.Paint[2].Glyph (13)"),
    (b"\x0c", "LayerV1List.Paint[2].Paint.Format (12)"),
    (b"\x00\x00\x1c", "Offset to Paint subtable from beginning of PaintTransform (28)"),
    (b"\xff\xf3\x00\x00", "Affine2x3.xx (-13)"),
    (b"\x00\x0e\x00\x00", "Affine2x3.xy (14)"),
    (b"\x00\x0f\x00\x00", "Affine2x3.yx (15)"),
    (b"\xff\xef\x00\x00", "Affine2x3.yy (-17)"),
    (b"\x00\x12\x00\x00", "Affine2x3.yy (18)"),
    (b"\x00\x13\x00\x00", "Affine2x3.yy (19)"),
    (b"\x07", "LayerV1List.Paint[2].Paint.Paint.Format (7)"),
    (b"\x00\x00(", "Offset to ColorLine from beginning of PaintVarRadialGradient (40)"),
    (b"\x00\x07\xff\xff\xff\xff", "Paint.x0.value (7)"),
    (b"\x00\x08\xff\xff\xff\xff", "Paint.y0.value (8)"),
    (b"\x00\t\xff\xff\xff\xff", "Paint.r0.value (9)"),
    (b"\x00\n\xff\xff\xff\xff", "Paint.x1.value (10)"),
    (b"\x00\x0b\xff\xff\xff\xff", "Paint.y1.value (11)"),
    (b"\x00\x0c\xff\xff\xff\xff", "Paint.r1.value (12)"),
    (b"\x00", "ColorLine.Extend (0; pad)"),
    (b"\x00\x02", "ColorLine.StopCount (2)"),
    (b"\x00\x00\xff\xff\xff\xff", "ColorLine.ColorStop[0].StopOffset.value (0.0)"),
    (b"\x00\x06", "ColorLine.ColorStop[0].Color.PaletteIndex (6)"),
    (b"@\x00\xff\xff\xff\xff", "ColorLine.ColorStop[0].Color.Alpha.value (1.0)"),
    (b"@\x00\xff\xff\xff\xff", "ColorLine.ColorStop[1].StopOffset.value (1.0)"),
    (b"\x00\x07", "ColorLine.ColorStop[1].Color.PaletteIndex (7)"),
    (b"\x19\x9a\xff\xff\xff\xff", "ColorLine.ColorStop[1].Color.Alpha.value (0.4)"),
    # PaintTranslate
    (b"\x0e", "LayerV1List.Paint[3].Format (14)"),
    (b"\x00\x00\x0c", "Offset to Paint subtable from beginning of PaintTranslate (12)"),
    (b"\x01\x01\x00\x00", "dx (257)"),
    (b"\x01\x02\x00\x00", "dy (258)"),
    # PaintRotate
    (b"\x10", "LayerV1List.Paint[3].Paint.Format (16)"),
    (b"\x00\x00\x10", "Offset to Paint subtable from beginning of PaintRotate (16)"),
    (b"\x00\x2d\x00\x00", "angle (45)"),
    (b"\x00\xff\x00\x00", "centerX (255)"),
    (b"\x01\x00\x00\x00", "centerY (256)"),
    # PaintSkew
    (b"\x12", "LayerV1List.Paint[3].Paint.Paint.Format (18)"),
    (b"\x00\x00\x14", "Offset to Paint subtable from beginning of PaintSkew (20)"),
    (b"\xff\xf5\x00\x00", "xSkewAngle (-11)"),
    (b"\x00\x05\x00\x00", "ySkewAngle (5)"),
    (b"\x00\xfd\x00\x00", "centerX.value (253)"),
    (b"\x00\xfe\x00\x00", "centerY.value (254)"),
    # PaintGlyph
    (b"\x0a", "LayerV1List.Paint[3].Paint.Paint.Paint.Format (10)"),
    (b"\x00\x00\x06", "Offset to Paint subtable from beginning of PaintGlyph (6)"),
    (b"\x00\x0b", "LayerV1List.Paint[2].Glyph (11)"),
    # PaintSolid
    (b"\x02", "LayerV1List.Paint[0].Paint.Paint.Paint.Paint.Format (2)"),
    (b"\x00\x02", "Paint.Color.PaletteIndex (2)"),
    (b" \x00", "Paint.Color.Alpha (0.5)"),
)

COLR_V1_DATA = b"".join(t[0] for t in COLR_V1_SAMPLE)

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
    "<BaseGlyphV1List>",
    "  <!-- BaseGlyphCount=3 -->",
    '  <BaseGlyphV1Record index="0">',
    '    <BaseGlyph value="glyph00010"/>',
    '    <Paint Format="1"><!-- PaintColrLayers -->',
    '      <NumLayers value="4"/>',
    '      <FirstLayerIndex value="0"/>',
    "    </Paint>",
    "  </BaseGlyphV1Record>",
    '  <BaseGlyphV1Record index="1">',
    '    <BaseGlyph value="glyph00014"/>',
    '    <Paint Format="20"><!-- PaintComposite -->',
    '      <SourcePaint Format="11"><!-- PaintColrGlyph -->',
    '        <Glyph value="glyph00010"/>',
    "      </SourcePaint>",
    '      <CompositeMode value="src_over"/>',
    '      <BackdropPaint Format="13"><!-- PaintVarTransform -->',
    '        <Paint Format="11"><!-- PaintColrGlyph -->',
    '          <Glyph value="glyph00010"/>',
    "        </Paint>",
    "        <Transform>",
    '          <xx value="1.0"/>',
    '          <yx value="0.0"/>',
    '          <xy value="0.0"/>',
    '          <yy value="1.0"/>',
    '          <dx value="300.0"/>',
    '          <dy value="0.0"/>',
    "        </Transform>",
    "      </BackdropPaint>",
    "    </Paint>",
    "  </BaseGlyphV1Record>",
    '  <BaseGlyphV1Record index="2">',
    '    <BaseGlyph value="glyph00015"/>',
    '    <Paint Format="10"><!-- PaintGlyph -->',
    '      <Paint Format="8"><!-- PaintSweepGradient -->',
    "        <ColorLine>",
    '          <Extend value="pad"/>',
    "          <!-- StopCount=2 -->",
    '          <ColorStop index="0">',
    '            <StopOffset value="0.0"/>',
    "            <Color>",
    '              <PaletteIndex value="3"/>',
    '              <Alpha value="1.0"/>',
    "            </Color>",
    "          </ColorStop>",
    '          <ColorStop index="1">',
    '            <StopOffset value="1.0"/>',
    "            <Color>",
    '              <PaletteIndex value="5"/>',
    '              <Alpha value="1.0"/>',
    "            </Color>",
    "          </ColorStop>",
    "        </ColorLine>",
    '        <centerX value="259"/>',
    '        <centerY value="300"/>',
    '        <startAngle value="45.0"/>',
    '        <endAngle value="135.0"/>',
    "      </Paint>",
    '      <Glyph value="glyph00011"/>',
    "    </Paint>",
    "  </BaseGlyphV1Record>",
    "</BaseGlyphV1List>",
    "<LayerV1List>",
    "  <!-- LayerCount=4 -->",
    '  <Paint index="0" Format="10"><!-- PaintGlyph -->',
    '    <Paint Format="3"><!-- PaintVarSolid -->',
    "      <Color>",
    '        <PaletteIndex value="2"/>',
    '        <Alpha value="0.5"/>',
    "      </Color>",
    "    </Paint>",
    '    <Glyph value="glyph00011"/>',
    "  </Paint>",
    '  <Paint index="1" Format="10"><!-- PaintGlyph -->',
    '    <Paint Format="4"><!-- PaintLinearGradient -->',
    "      <ColorLine>",
    '        <Extend value="repeat"/>',
    "        <!-- StopCount=3 -->",
    '        <ColorStop index="0">',
    '          <StopOffset value="0.0"/>',
    "          <Color>",
    '            <PaletteIndex value="3"/>',
    '            <Alpha value="1.0"/>',
    "          </Color>",
    "        </ColorStop>",
    '        <ColorStop index="1">',
    '          <StopOffset value="0.5"/>',
    "          <Color>",
    '            <PaletteIndex value="4"/>',
    '            <Alpha value="1.0"/>',
    "          </Color>",
    "        </ColorStop>",
    '        <ColorStop index="2">',
    '          <StopOffset value="1.0"/>',
    "          <Color>",
    '            <PaletteIndex value="5"/>',
    '            <Alpha value="1.0"/>',
    "          </Color>",
    "        </ColorStop>",
    "      </ColorLine>",
    '      <x0 value="1"/>',
    '      <y0 value="2"/>',
    '      <x1 value="-3"/>',
    '      <y1 value="-4"/>',
    '      <x2 value="5"/>',
    '      <y2 value="6"/>',
    "    </Paint>",
    '    <Glyph value="glyph00012"/>',
    "  </Paint>",
    '  <Paint index="2" Format="10"><!-- PaintGlyph -->',
    '    <Paint Format="12"><!-- PaintTransform -->',
    '      <Paint Format="7"><!-- PaintVarRadialGradient -->',
    "        <ColorLine>",
    '          <Extend value="pad"/>',
    "          <!-- StopCount=2 -->",
    '          <ColorStop index="0">',
    '            <StopOffset value="0.0"/>',
    "            <Color>",
    '              <PaletteIndex value="6"/>',
    '              <Alpha value="1.0"/>',
    "            </Color>",
    "          </ColorStop>",
    '          <ColorStop index="1">',
    '            <StopOffset value="1.0"/>',
    "            <Color>",
    '              <PaletteIndex value="7"/>',
    '              <Alpha value="0.4"/>',
    "            </Color>",
    "          </ColorStop>",
    "        </ColorLine>",
    '        <x0 value="7"/>',
    '        <y0 value="8"/>',
    '        <r0 value="9"/>',
    '        <x1 value="10"/>',
    '        <y1 value="11"/>',
    '        <r1 value="12"/>',
    "      </Paint>",
    "      <Transform>",
    '        <xx value="-13.0"/>',
    '        <yx value="14.0"/>',
    '        <xy value="15.0"/>',
    '        <yy value="-17.0"/>',
    '        <dx value="18.0"/>',
    '        <dy value="19.0"/>',
    "      </Transform>",
    "    </Paint>",
    '    <Glyph value="glyph00013"/>',
    "  </Paint>",
    '  <Paint index="3" Format="14"><!-- PaintTranslate -->',
    '    <Paint Format="16"><!-- PaintRotate -->',
    '      <Paint Format="18"><!-- PaintSkew -->',
    '        <Paint Format="10"><!-- PaintGlyph -->',
    '          <Paint Format="2"><!-- PaintSolid -->',
    "            <Color>",
    '              <PaletteIndex value="2"/>',
    '              <Alpha value="0.5"/>',
    "            </Color>",
    "          </Paint>",
    '          <Glyph value="glyph00011"/>',
    "        </Paint>",
    '        <xSkewAngle value="-11.0"/>',
    '        <ySkewAngle value="5.0"/>',
    '        <centerX value="253.0"/>',
    '        <centerY value="254.0"/>',
    "      </Paint>",
    '      <angle value="45.0"/>',
    '      <centerX value="255.0"/>',
    '      <centerY value="256.0"/>',
    "    </Paint>",
    '    <dx value="257.0"/>',
    '    <dy value="258.0"/>',
    "  </Paint>",
    "</LayerV1List>",
]


class COLR_V1_Test(object):
    def test_decompile_and_compile(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V1_DATA, font)
        diff_binary_fragments(colr.compile(font), COLR_V1_SAMPLE)

    def test_decompile_and_dump_xml(self, font):
        colr = table_C_O_L_R_()
        colr.decompile(COLR_V1_DATA, font)

        dump(colr, font)
        assert getXML(colr.toXML, font) == COLR_V1_XML

    def test_load_from_xml_and_compile(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V1_XML):
            colr.fromXML(name, attrs, content, font)
        diff_binary_fragments(colr.compile(font), COLR_V1_SAMPLE)

    def test_round_trip_xml(self, font):
        colr = table_C_O_L_R_()
        for name, attrs, content in parseXML(COLR_V1_XML):
            colr.fromXML(name, attrs, content, font)
        compiled = colr.compile(font)

        colr = table_C_O_L_R_()
        colr.decompile(compiled, font)
        assert getXML(colr.toXML, font) == COLR_V1_XML
