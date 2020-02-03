import base64
import io
import os

from fontTools.misc.testTools import getXML
from fontTools.ttLib import TTFont


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")

# This is a subset from NotoColorEmoji.ttf which contains an IndexTable format=3
INDEX_FORMAT_3_TTX = os.path.join(DATA_DIR, "NotoColorEmoji.subset.index_format_3.ttx")
# The CLBC table was compiled with Harfbuzz' hb-subset and contains the correct padding
CBLC_INDEX_FORMAT_3 = base64.b64decode(
    "AAMAAAAAAAEAAAA4AAAALAAAAAIAAAAAZeWIAAAAAAAAAAAAZeWIAAAAAAAAAAAAAAEAA"
    "21tIAEAAQACAAAAEAADAAMAAAAgAAMAEQAAAAQAAAOmEQ0AAAADABEAABERAAAIUg=="
)


def test_compile_decompile_index_table_format_3():
    font = TTFont()
    font.importXML(INDEX_FORMAT_3_TTX)
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    font = TTFont(buf)

    assert font.reader["CBLC"] == CBLC_INDEX_FORMAT_3

    assert getXML(font["CBLC"].toXML, font) == [
        '<header version="3.0"/>',
        '<strike index="0">',
        "  <bitmapSizeTable>",
        '    <sbitLineMetrics direction="hori">',
        '      <ascender value="101"/>',
        '      <descender value="-27"/>',
        '      <widthMax value="136"/>',
        '      <caretSlopeNumerator value="0"/>',
        '      <caretSlopeDenominator value="0"/>',
        '      <caretOffset value="0"/>',
        '      <minOriginSB value="0"/>',
        '      <minAdvanceSB value="0"/>',
        '      <maxBeforeBL value="0"/>',
        '      <minAfterBL value="0"/>',
        '      <pad1 value="0"/>',
        '      <pad2 value="0"/>',
        "    </sbitLineMetrics>",
        '    <sbitLineMetrics direction="vert">',
        '      <ascender value="101"/>',
        '      <descender value="-27"/>',
        '      <widthMax value="136"/>',
        '      <caretSlopeNumerator value="0"/>',
        '      <caretSlopeDenominator value="0"/>',
        '      <caretOffset value="0"/>',
        '      <minOriginSB value="0"/>',
        '      <minAdvanceSB value="0"/>',
        '      <maxBeforeBL value="0"/>',
        '      <minAfterBL value="0"/>',
        '      <pad1 value="0"/>',
        '      <pad2 value="0"/>',
        "    </sbitLineMetrics>",
        '    <colorRef value="0"/>',
        '    <startGlyphIndex value="1"/>',
        '    <endGlyphIndex value="3"/>',
        '    <ppemX value="109"/>',
        '    <ppemY value="109"/>',
        '    <bitDepth value="32"/>',
        '    <flags value="1"/>',
        "  </bitmapSizeTable>",
        "  <!-- GlyphIds are written but not read. The firstGlyphIndex and",
        "       lastGlyphIndex values will be recalculated by the compiler. -->",
        '  <eblc_index_sub_table_3 imageFormat="17" firstGlyphIndex="1" lastGlyphIndex="2">',
        '    <glyphLoc id="1" name="eight"/>',
        '    <glyphLoc id="2" name="registered"/>',
        "  </eblc_index_sub_table_3>",
        '  <eblc_index_sub_table_3 imageFormat="17" firstGlyphIndex="3" lastGlyphIndex="3">',
        '    <glyphLoc id="3" name="uni2049"/>',
        "  </eblc_index_sub_table_3>",
        "</strike>",
    ]
