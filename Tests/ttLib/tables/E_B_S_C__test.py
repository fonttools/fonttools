import io

import pytest

from fontTools.misc.testTools import getXML, parseXmlInto
from fontTools.ttLib import TTFont, TTLibError, newTable
from fontTools.ttLib.tables.E_B_S_C_ import BitmapScaleTable, table_E_B_S_C_

EBSC_XML = """\
<header version="2.0" numSizes="1"/>
<bitmapScaleTable index="0">
  <sbitLineMetrics direction="hori">
    <ascender value="1"/>
    <descender value="-1"/>
    <widthMax value="3"/>
    <caretSlopeNumerator value="4"/>
    <caretSlopeDenominator value="5"/>
    <caretOffset value="6"/>
    <minOriginSB value="7"/>
    <minAdvanceSB value="8"/>
    <maxBeforeBL value="9"/>
    <minAfterBL value="10"/>
    <pad1 value="0"/>
    <pad2 value="0"/>
  </sbitLineMetrics>
  <sbitLineMetrics direction="vert">
    <ascender value="11"/>
    <descender value="-2"/>
    <widthMax value="13"/>
    <caretSlopeNumerator value="14"/>
    <caretSlopeDenominator value="15"/>
    <caretOffset value="16"/>
    <minOriginSB value="17"/>
    <minAdvanceSB value="18"/>
    <maxBeforeBL value="19"/>
    <minAfterBL value="20"/>
    <pad1 value="0"/>
    <pad2 value="0"/>
  </sbitLineMetrics>
  <ppemX value="21"/>
  <ppemY value="22"/>
  <substitutePpemX value="23"/>
  <substitutePpemY value="24"/>
</bitmapScaleTable>
"""


def makeBitmapScaleTable():
    table = BitmapScaleTable()
    table.hori.ascender = 1
    table.hori.descender = -1
    table.hori.widthMax = 3
    table.hori.caretSlopeNumerator = 4
    table.hori.caretSlopeDenominator = 5
    table.hori.caretOffset = 6
    table.hori.minOriginSB = 7
    table.hori.minAdvanceSB = 8
    table.hori.maxBeforeBL = 9
    table.hori.minAfterBL = 10
    table.hori.pad1 = 0
    table.hori.pad2 = 0
    table.vert.ascender = 11
    table.vert.descender = -2
    table.vert.widthMax = 13
    table.vert.caretSlopeNumerator = 14
    table.vert.caretSlopeDenominator = 15
    table.vert.caretOffset = 16
    table.vert.minOriginSB = 17
    table.vert.minAdvanceSB = 18
    table.vert.maxBeforeBL = 19
    table.vert.minAfterBL = 20
    table.vert.pad1 = 0
    table.vert.pad2 = 0
    table.ppemX = 21
    table.ppemY = 22
    table.substitutePpemX = 23
    table.substitutePpemY = 24
    return table


def assertBitmapScaleTableEqual(table, expected):
    assert table.hori.__dict__ == expected.hori.__dict__
    assert table.vert.__dict__ == expected.vert.__dict__
    assert table.ppemX == expected.ppemX
    assert table.ppemY == expected.ppemY
    assert table.substitutePpemX == expected.substitutePpemX
    assert table.substitutePpemY == expected.substitutePpemY


def test_compile_decompile_and_roundtrip_ttx():
    ttFont = TTFont()
    table = table_E_B_S_C_()
    assert table.tableTag == "EBSC"
    table.version = 2.0
    table.bitmapScaleTables = [makeBitmapScaleTable()]

    data = table.compile(ttFont)

    table2 = table_E_B_S_C_()
    table2.decompile(data, ttFont)

    assert table.version == table2.version
    assert len(table2.bitmapScaleTables) == 1
    assertBitmapScaleTableEqual(table2.bitmapScaleTables[0], makeBitmapScaleTable())
    assert getXML(table2.toXML, ttFont) == EBSC_XML.splitlines()

    table3 = table_E_B_S_C_()
    parseXmlInto(ttFont, table3, EBSC_XML)

    assert table3.version == 2.0
    assert table3.numSizes == 1
    assert len(table3.bitmapScaleTables) == 1
    assertBitmapScaleTableEqual(table3.bitmapScaleTables[0], makeBitmapScaleTable())


def test_fromxml_accepts_bitmap_scale_table_before_header():
    ttFont = TTFont()
    table = table_E_B_S_C_()
    parseXmlInto(
        ttFont,
        table,
        """\
<bitmapScaleTable index="0">
  <sbitLineMetrics direction="hori">
    <ascender value="1"/>
    <descender value="-1"/>
    <widthMax value="3"/>
    <caretSlopeNumerator value="4"/>
    <caretSlopeDenominator value="5"/>
    <caretOffset value="6"/>
    <minOriginSB value="7"/>
    <minAdvanceSB value="8"/>
    <maxBeforeBL value="9"/>
    <minAfterBL value="10"/>
    <pad1 value="0"/>
    <pad2 value="0"/>
  </sbitLineMetrics>
  <sbitLineMetrics direction="vert">
    <ascender value="11"/>
    <descender value="-2"/>
    <widthMax value="13"/>
    <caretSlopeNumerator value="14"/>
    <caretSlopeDenominator value="15"/>
    <caretOffset value="16"/>
    <minOriginSB value="17"/>
    <minAdvanceSB value="18"/>
    <maxBeforeBL value="19"/>
    <minAfterBL value="20"/>
    <pad1 value="0"/>
    <pad2 value="0"/>
  </sbitLineMetrics>
  <ppemX value="21"/>
  <ppemY value="22"/>
  <substitutePpemX value="23"/>
  <substitutePpemY value="24"/>
</bitmapScaleTable>
<header version="2.0" numSizes="1"/>
""",
    )

    assert table.version == 2.0
    assert table.numSizes == 1
    assert len(table.bitmapScaleTables) == 1
    assertBitmapScaleTableEqual(table.bitmapScaleTables[0], makeBitmapScaleTable())


def test_fromxml_rejects_invalid_sbit_line_metrics_direction():
    table = table_E_B_S_C_()
    with pytest.raises(TTLibError, match="invalid sbitLineMetrics direction"):
        parseXmlInto(
            TTFont(),
            table,
            """\
<bitmapScaleTable index="0">
  <sbitLineMetrics direction="diagonal"/>
</bitmapScaleTable>
""",
        )


def test_save_writes_ebsc_after_ebdt_and_eblc():
    font = TTFont()
    font.setGlyphOrder([".notdef"])
    ebdt = newTable("EBDT")
    ebdt.version = 2.0
    ebdt.strikeData = []
    font["EBDT"] = ebdt
    eblc = newTable("EBLC")
    eblc.version = 2.0
    eblc.strikes = []
    font["EBLC"] = eblc
    ebsc = newTable("EBSC")
    ebsc.version = 2.0
    ebsc.bitmapScaleTables = [makeBitmapScaleTable()]
    font["EBSC"] = ebsc

    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    font = TTFont(buf)

    assert list(font.reader.keys()) == ["EBDT", "EBLC", "EBSC"]
