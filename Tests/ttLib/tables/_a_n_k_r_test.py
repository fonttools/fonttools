# coding: utf-8
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# This is the anchor points table of the first font file in
# “/Library/Fonts/Devanagari Sangam MN.ttc” on macOS 10.12.6.
# For testing, we’ve changed the GlyphIDs to smaller values.
# Also, in the AATLookup, we’ve changed GlyphDataOffset value
# for the end-of-table marker from 0xFFFF to 0 since that is
# what our encoder emits. (The value for end-of-table markers
# does not actually matter).
ANKR_FORMAT_0_DATA = deHexStr(
    "0000 0000 "  #  0: Format=0, Flags=0
    "0000 000C "  #  4: LookupTableOffset=12
    "0000 0024 "  #  8: GlyphDataTableOffset=36
    "0006 0004 0002 "  # 12: LookupFormat=6, UnitSize=4, NUnits=2
    "0008 0001 0000 "  # 18: SearchRange=8, EntrySelector=1, RangeShift=0
    "0001 0000 "  # 24: Glyph=A, Offset=0 (+GlyphDataTableOffset=36)
    "0003 0008 "  # 28: Glyph=C, Offset=8 (+GlyphDataTableOffset=44)
    "FFFF 0000 "  # 32: Glyph=<end>, Offset=<n/a>
    "0000 0001 "  # 36: GlyphData[A].NumPoints=1
    "0235 045E "  # 40: GlyphData[A].Points[0].X=565, .Y=1118
    "0000 0001 "  # 44: GlyphData[C].NumPoints=1
    "FED2 045E "  # 48: GlyphData[C].Points[0].X=-302, .Y=1118
)  # 52: <end>
assert len(ANKR_FORMAT_0_DATA) == 52


ANKR_FORMAT_0_XML = [
    '<AnchorPoints Format="0">',
    '  <Flags value="0"/>',
    "  <Anchors>",
    '    <Lookup glyph="A">',
    "      <!-- AnchorPointCount=1 -->",
    '      <AnchorPoint index="0">',
    '        <XCoordinate value="565"/>',
    '        <YCoordinate value="1118"/>',
    "      </AnchorPoint>",
    "    </Lookup>",
    '    <Lookup glyph="C">',
    "      <!-- AnchorPointCount=1 -->",
    '      <AnchorPoint index="0">',
    '        <XCoordinate value="-302"/>',
    '        <YCoordinate value="1118"/>',
    "      </AnchorPoint>",
    "    </Lookup>",
    "  </Anchors>",
    "</AnchorPoints>",
]


# Same data as ANKR_FORMAT_0_DATA, but with chunks of unused data
# whose presence should not stop us from decompiling the table.
ANKR_FORMAT_0_STRAY_DATA = deHexStr(
    "0000 0000 "  #  0: Format=0, Flags=0
    "0000 0018 "  #  4: LookupTableOffset=24
    "0000 0034 "  #  8: GlyphDataTableOffset=52
    "DEAD BEEF CAFE "  # 12: <stray data>
    "DEAD BEEF CAFE "  # 18: <stray data>
    "0006 0004 0002 "  # 24: LookupFormat=6, UnitSize=4, NUnits=2
    "0008 0001 0000 "  # 30: SearchRange=8, EntrySelector=1, RangeShift=0
    "0001 0000 "  # 36: Glyph=A, Offset=0 (+GlyphDataTableOffset=52)
    "0003 0008 "  # 40: Glyph=C, Offset=8 (+GlyphDataTableOffset=60)
    "FFFF 0000 "  # 44: Glyph=<end>, Offset=<n/a>
    "BEEF F00D "  # 48: <stray data>
    "0000 0001 "  # 52: GlyphData[A].NumPoints=1
    "0235 045E "  # 56: GlyphData[A].Points[0].X=565, .Y=1118
    "0000 0001 "  # 60: GlyphData[C].NumPoints=1
    "FED2 045E "  # 64: GlyphData[C].Points[0].X=-302, .Y=1118
)  # 68: <end>
assert len(ANKR_FORMAT_0_STRAY_DATA) == 68


# Constructed test case where glyphs A and D share the same anchor data.
ANKR_FORMAT_0_SHARING_DATA = deHexStr(
    "0000 0000 "  #  0: Format=0, Flags=0
    "0000 000C "  #  4: LookupTableOffset=12
    "0000 0028 "  #  8: GlyphDataTableOffset=40
    "0006 0004 0003 "  # 12: LookupFormat=6, UnitSize=4, NUnits=3
    "0008 0001 0004 "  # 18: SearchRange=8, EntrySelector=1, RangeShift=4
    "0001 0000 "  # 24: Glyph=A, Offset=0 (+GlyphDataTableOffset=36)
    "0003 0008 "  # 28: Glyph=C, Offset=8 (+GlyphDataTableOffset=44)
    "0004 0000 "  # 32: Glyph=D, Offset=0 (+GlyphDataTableOffset=36)
    "FFFF 0000 "  # 36: Glyph=<end>, Offset=<n/a>
    "0000 0001 "  # 40: GlyphData[A].NumPoints=1
    "0235 045E "  # 44: GlyphData[A].Points[0].X=565, .Y=1118
    "0000 0002 "  # 48: GlyphData[C].NumPoints=2
    "000B 000C "  # 52: GlyphData[C].Points[0].X=11, .Y=12
    "001B 001C "  # 56: GlyphData[C].Points[1].X=27, .Y=28
)  # 60: <end>
assert len(ANKR_FORMAT_0_SHARING_DATA) == 60


ANKR_FORMAT_0_SHARING_XML = [
    '<AnchorPoints Format="0">',
    '  <Flags value="0"/>',
    "  <Anchors>",
    '    <Lookup glyph="A">',
    "      <!-- AnchorPointCount=1 -->",
    '      <AnchorPoint index="0">',
    '        <XCoordinate value="565"/>',
    '        <YCoordinate value="1118"/>',
    "      </AnchorPoint>",
    "    </Lookup>",
    '    <Lookup glyph="C">',
    "      <!-- AnchorPointCount=2 -->",
    '      <AnchorPoint index="0">',
    '        <XCoordinate value="11"/>',
    '        <YCoordinate value="12"/>',
    "      </AnchorPoint>",
    '      <AnchorPoint index="1">',
    '        <XCoordinate value="27"/>',
    '        <YCoordinate value="28"/>',
    "      </AnchorPoint>",
    "    </Lookup>",
    '    <Lookup glyph="D">',
    "      <!-- AnchorPointCount=1 -->",
    '      <AnchorPoint index="0">',
    '        <XCoordinate value="565"/>',
    '        <YCoordinate value="1118"/>',
    "      </AnchorPoint>",
    "    </Lookup>",
    "  </Anchors>",
    "</AnchorPoints>",
]


class ANKRTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont([".notdef", "A", "B", "C", "D"])

    def decompileToXML(self, data, xml):
        table = newTable("ankr")
        table.decompile(data, self.font)
        self.assertEqual(getXML(table.toXML), xml)

    def compileFromXML(self, xml, data):
        table = newTable("ankr")
        for name, attrs, content in parseXML(xml):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)), hexStr(data))

    def roundtrip(self, data, xml):
        self.decompileToXML(data, xml)
        self.compileFromXML(xml, data)

    def testFormat0(self):
        self.roundtrip(ANKR_FORMAT_0_DATA, ANKR_FORMAT_0_XML)

    def testFormat0_stray(self):
        self.decompileToXML(ANKR_FORMAT_0_STRAY_DATA, ANKR_FORMAT_0_XML)

    def testFormat0_sharing(self):
        self.roundtrip(ANKR_FORMAT_0_SHARING_DATA, ANKR_FORMAT_0_SHARING_XML)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
