from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# Apple's spec of the baseline table gives no example for 'bsln' format 0,
# but the Apple Chancery font contains the following data.
BSLN_FORMAT_0_DATA = deHexStr(
    "0001 0000 0000 "  #  0: Version=1.0, Format=0
    "0000 "  #  6: DefaultBaseline=0 (Roman baseline)
    "0000 01D1 0000 0541 "  #  8: Delta[0..3]=0, 465, 0, 1345
    "01FB 0000 0000 0000 "  # 16: Delta[4..7]=507, 0, 0, 0
    "0000 0000 0000 0000 "  # 24: Delta[8..11]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 32: Delta[12..15]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 40: Delta[16..19]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 48: Delta[20..23]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 56: Delta[24..27]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 64: Delta[28..31]=0, 0, 0, 0
)  # 72: <end>
assert len(BSLN_FORMAT_0_DATA) == 72


BSLN_FORMAT_0_XML = [
    '<Version value="0x00010000"/>',
    '<Baseline Format="0">',
    '  <DefaultBaseline value="0"/>',
    '  <Delta index="0" value="0"/>',
    '  <Delta index="1" value="465"/>',
    '  <Delta index="2" value="0"/>',
    '  <Delta index="3" value="1345"/>',
    '  <Delta index="4" value="507"/>',
    '  <Delta index="5" value="0"/>',
    '  <Delta index="6" value="0"/>',
    '  <Delta index="7" value="0"/>',
    '  <Delta index="8" value="0"/>',
    '  <Delta index="9" value="0"/>',
    '  <Delta index="10" value="0"/>',
    '  <Delta index="11" value="0"/>',
    '  <Delta index="12" value="0"/>',
    '  <Delta index="13" value="0"/>',
    '  <Delta index="14" value="0"/>',
    '  <Delta index="15" value="0"/>',
    '  <Delta index="16" value="0"/>',
    '  <Delta index="17" value="0"/>',
    '  <Delta index="18" value="0"/>',
    '  <Delta index="19" value="0"/>',
    '  <Delta index="20" value="0"/>',
    '  <Delta index="21" value="0"/>',
    '  <Delta index="22" value="0"/>',
    '  <Delta index="23" value="0"/>',
    '  <Delta index="24" value="0"/>',
    '  <Delta index="25" value="0"/>',
    '  <Delta index="26" value="0"/>',
    '  <Delta index="27" value="0"/>',
    '  <Delta index="28" value="0"/>',
    '  <Delta index="29" value="0"/>',
    '  <Delta index="30" value="0"/>',
    '  <Delta index="31" value="0"/>',
    "</Baseline>",
]


# Example: Format 1 Baseline Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6bsln.html
# The example in the AAT specification uses the value 270 for Seg[0].LastGlyph,
# whereas we use the value 10 for testng to shorten the XML dump.
BSLN_FORMAT_1_DATA = deHexStr(
    "0001 0000 0001 "  #  0: Version=1.0, Format=1
    "0001 "  #  6: DefaultBaseline=1 (Ideographic baseline)
    "0000 0357 0000 05F0 "  #  8: Delta[0..3]=0, 855, 0, 1520
    "0000 0000 0000 0000 "  # 16: Delta[4..7]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 24: Delta[8..11]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 32: Delta[12..15]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 40: Delta[16..19]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 48: Delta[20..23]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 56: Delta[24..27]=0, 0, 0, 0
    "0000 0000 0000 0000 "  # 64: Delta[28..31]=0, 0, 0, 0
    "0002 0006 0001 "  # 72: LookupFormat=2, UnitSize=6, NUnits=1
    "0006 0000 0000 "  # 78: SearchRange=6, EntrySelector=0, RangeShift=0
    "000A 0002 0000 "  # 84: Seg[0].LastGlyph=10 FirstGl=2 Value=0/Roman
    "FFFF FFFF 0000 "  # 90: Seg[1]=<end>
)  # 96: <end>
assert len(BSLN_FORMAT_1_DATA) == 96


BSLN_FORMAT_1_XML = [
    '<Version value="0x00010000"/>',
    '<Baseline Format="1">',
    '  <DefaultBaseline value="1"/>',
    '  <Delta index="0" value="0"/>',
    '  <Delta index="1" value="855"/>',
    '  <Delta index="2" value="0"/>',
    '  <Delta index="3" value="1520"/>',
    '  <Delta index="4" value="0"/>',
    '  <Delta index="5" value="0"/>',
    '  <Delta index="6" value="0"/>',
    '  <Delta index="7" value="0"/>',
    '  <Delta index="8" value="0"/>',
    '  <Delta index="9" value="0"/>',
    '  <Delta index="10" value="0"/>',
    '  <Delta index="11" value="0"/>',
    '  <Delta index="12" value="0"/>',
    '  <Delta index="13" value="0"/>',
    '  <Delta index="14" value="0"/>',
    '  <Delta index="15" value="0"/>',
    '  <Delta index="16" value="0"/>',
    '  <Delta index="17" value="0"/>',
    '  <Delta index="18" value="0"/>',
    '  <Delta index="19" value="0"/>',
    '  <Delta index="20" value="0"/>',
    '  <Delta index="21" value="0"/>',
    '  <Delta index="22" value="0"/>',
    '  <Delta index="23" value="0"/>',
    '  <Delta index="24" value="0"/>',
    '  <Delta index="25" value="0"/>',
    '  <Delta index="26" value="0"/>',
    '  <Delta index="27" value="0"/>',
    '  <Delta index="28" value="0"/>',
    '  <Delta index="29" value="0"/>',
    '  <Delta index="30" value="0"/>',
    '  <Delta index="31" value="0"/>',
    "  <BaselineValues>",
    '    <Lookup glyph="B" value="0"/>',
    '    <Lookup glyph="C" value="0"/>',
    '    <Lookup glyph="D" value="0"/>',
    '    <Lookup glyph="E" value="0"/>',
    '    <Lookup glyph="F" value="0"/>',
    '    <Lookup glyph="G" value="0"/>',
    '    <Lookup glyph="H" value="0"/>',
    '    <Lookup glyph="I" value="0"/>',
    '    <Lookup glyph="J" value="0"/>',
    "  </BaselineValues>",
    "</Baseline>",
]


BSLN_FORMAT_2_DATA = deHexStr(
    "0001 0000 0002 "  #  0: Version=1.0, Format=2
    "0004 "  #  6: DefaultBaseline=4 (Math)
    "0016 "  #  8: StandardGlyph=22
    "0050 0051 FFFF 0052 "  # 10: ControlPoint[0..3]=80, 81, <none>, 82
    "FFFF FFFF FFFF FFFF "  # 18: ControlPoint[4..7]=<none>
    "FFFF FFFF FFFF FFFF "  # 26: ControlPoint[8..11]=<none>
    "FFFF FFFF FFFF FFFF "  # 34: ControlPoint[12..15]=<none>
    "FFFF FFFF FFFF FFFF "  # 42: ControlPoint[16..19]=<none>
    "FFFF FFFF FFFF FFFF "  # 50: ControlPoint[20..23]=<none>
    "FFFF FFFF FFFF FFFF "  # 58: ControlPoint[24..27]=<none>
    "FFFF FFFF FFFF FFFF "  # 66: ControlPoint[28..31]=<none>
)  # 74: <end>
assert len(BSLN_FORMAT_2_DATA) == 74


BSLN_FORMAT_2_XML = [
    '<Version value="0x00010000"/>',
    '<Baseline Format="2">',
    '  <DefaultBaseline value="4"/>',
    '  <StandardGlyph value="V"/>',
    '  <ControlPoint index="0" value="80"/>',
    '  <ControlPoint index="1" value="81"/>',
    '  <ControlPoint index="2" value="65535"/>',
    '  <ControlPoint index="3" value="82"/>',
    '  <ControlPoint index="4" value="65535"/>',
    '  <ControlPoint index="5" value="65535"/>',
    '  <ControlPoint index="6" value="65535"/>',
    '  <ControlPoint index="7" value="65535"/>',
    '  <ControlPoint index="8" value="65535"/>',
    '  <ControlPoint index="9" value="65535"/>',
    '  <ControlPoint index="10" value="65535"/>',
    '  <ControlPoint index="11" value="65535"/>',
    '  <ControlPoint index="12" value="65535"/>',
    '  <ControlPoint index="13" value="65535"/>',
    '  <ControlPoint index="14" value="65535"/>',
    '  <ControlPoint index="15" value="65535"/>',
    '  <ControlPoint index="16" value="65535"/>',
    '  <ControlPoint index="17" value="65535"/>',
    '  <ControlPoint index="18" value="65535"/>',
    '  <ControlPoint index="19" value="65535"/>',
    '  <ControlPoint index="20" value="65535"/>',
    '  <ControlPoint index="21" value="65535"/>',
    '  <ControlPoint index="22" value="65535"/>',
    '  <ControlPoint index="23" value="65535"/>',
    '  <ControlPoint index="24" value="65535"/>',
    '  <ControlPoint index="25" value="65535"/>',
    '  <ControlPoint index="26" value="65535"/>',
    '  <ControlPoint index="27" value="65535"/>',
    '  <ControlPoint index="28" value="65535"/>',
    '  <ControlPoint index="29" value="65535"/>',
    '  <ControlPoint index="30" value="65535"/>',
    '  <ControlPoint index="31" value="65535"/>',
    "</Baseline>",
]


# Example: Format 3 Baseline Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6bsln.html
# The example in the AAT specification uses the value 270 for Seg[0].LastGlyph,
# whereas we use the value 10 for testng to shorten the XML dump.
BSLN_FORMAT_3_DATA = deHexStr(
    "0001 0000 0003 "  #  0: Version=1.0, Format=3
    "0001 "  #  6: DefaultBaseline=1 (Ideographic)
    "0016 "  #  8: StandardGlyph=22
    "0050 0051 FFFF 0052 "  # 10: ControlPoint[0..3]=80, 81, <none>, 82
    "FFFF FFFF FFFF FFFF "  # 18: ControlPoint[4..7]=<none>
    "FFFF FFFF FFFF FFFF "  # 26: ControlPoint[8..11]=<none>
    "FFFF FFFF FFFF FFFF "  # 34: ControlPoint[12..15]=<none>
    "FFFF FFFF FFFF FFFF "  # 42: ControlPoint[16..19]=<none>
    "FFFF FFFF FFFF FFFF "  # 50: ControlPoint[20..23]=<none>
    "FFFF FFFF FFFF FFFF "  # 58: ControlPoint[24..27]=<none>
    "FFFF FFFF FFFF FFFF "  # 66: ControlPoint[28..31]=<none>
    "0002 0006 0001 "  # 74: LookupFormat=2, UnitSize=6, NUnits=1
    "0006 0000 0000 "  # 80: SearchRange=6, EntrySelector=0, RangeShift=0
    "000A 0002 0000 "  # 86: Seg[0].LastGlyph=10 FirstGl=2 Value=0/Roman
    "FFFF FFFF 0000 "  # 92: Seg[1]=<end>
)  # 98: <end>
assert len(BSLN_FORMAT_3_DATA) == 98


BSLN_FORMAT_3_XML = [
    '<Version value="0x00010000"/>',
    '<Baseline Format="3">',
    '  <DefaultBaseline value="1"/>',
    '  <StandardGlyph value="V"/>',
    '  <ControlPoint index="0" value="80"/>',
    '  <ControlPoint index="1" value="81"/>',
    '  <ControlPoint index="2" value="65535"/>',
    '  <ControlPoint index="3" value="82"/>',
    '  <ControlPoint index="4" value="65535"/>',
    '  <ControlPoint index="5" value="65535"/>',
    '  <ControlPoint index="6" value="65535"/>',
    '  <ControlPoint index="7" value="65535"/>',
    '  <ControlPoint index="8" value="65535"/>',
    '  <ControlPoint index="9" value="65535"/>',
    '  <ControlPoint index="10" value="65535"/>',
    '  <ControlPoint index="11" value="65535"/>',
    '  <ControlPoint index="12" value="65535"/>',
    '  <ControlPoint index="13" value="65535"/>',
    '  <ControlPoint index="14" value="65535"/>',
    '  <ControlPoint index="15" value="65535"/>',
    '  <ControlPoint index="16" value="65535"/>',
    '  <ControlPoint index="17" value="65535"/>',
    '  <ControlPoint index="18" value="65535"/>',
    '  <ControlPoint index="19" value="65535"/>',
    '  <ControlPoint index="20" value="65535"/>',
    '  <ControlPoint index="21" value="65535"/>',
    '  <ControlPoint index="22" value="65535"/>',
    '  <ControlPoint index="23" value="65535"/>',
    '  <ControlPoint index="24" value="65535"/>',
    '  <ControlPoint index="25" value="65535"/>',
    '  <ControlPoint index="26" value="65535"/>',
    '  <ControlPoint index="27" value="65535"/>',
    '  <ControlPoint index="28" value="65535"/>',
    '  <ControlPoint index="29" value="65535"/>',
    '  <ControlPoint index="30" value="65535"/>',
    '  <ControlPoint index="31" value="65535"/>',
    "  <BaselineValues>",
    '    <Lookup glyph="B" value="0"/>',
    '    <Lookup glyph="C" value="0"/>',
    '    <Lookup glyph="D" value="0"/>',
    '    <Lookup glyph="E" value="0"/>',
    '    <Lookup glyph="F" value="0"/>',
    '    <Lookup glyph="G" value="0"/>',
    '    <Lookup glyph="H" value="0"/>',
    '    <Lookup glyph="I" value="0"/>',
    '    <Lookup glyph="J" value="0"/>',
    "  </BaselineValues>",
    "</Baseline>",
]


class BSLNTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont([".notdef"] + [g for g in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])

    def decompileToXML(self, data, xml):
        table = newTable("bsln")
        table.decompile(data, self.font)
        self.assertEqual(getXML(table.toXML), xml)

    def compileFromXML(self, xml, data):
        table = newTable("bsln")
        for name, attrs, content in parseXML(xml):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)), hexStr(data))

    def testFormat0(self):
        self.decompileToXML(BSLN_FORMAT_0_DATA, BSLN_FORMAT_0_XML)
        self.compileFromXML(BSLN_FORMAT_0_XML, BSLN_FORMAT_0_DATA)

    def testFormat1(self):
        self.decompileToXML(BSLN_FORMAT_1_DATA, BSLN_FORMAT_1_XML)
        self.compileFromXML(BSLN_FORMAT_1_XML, BSLN_FORMAT_1_DATA)

    def testFormat2(self):
        self.decompileToXML(BSLN_FORMAT_2_DATA, BSLN_FORMAT_2_XML)
        self.compileFromXML(BSLN_FORMAT_2_XML, BSLN_FORMAT_2_DATA)

    def testFormat3(self):
        self.decompileToXML(BSLN_FORMAT_3_DATA, BSLN_FORMAT_3_XML)
        self.compileFromXML(BSLN_FORMAT_3_XML, BSLN_FORMAT_3_DATA)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
