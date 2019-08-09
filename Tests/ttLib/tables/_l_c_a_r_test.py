from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# Example: Format 0 Ligature Caret Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6lcar.html
LCAR_FORMAT_0_DATA = deHexStr(
    '0001 0000 0000 '  #  0: Version=1.0, Format=0
    '0006 0004 0002 '  #  6: LookupFormat=6, UnitSize=4, NUnits=2
    '0008 0001 0000 '  # 12: SearchRange=8, EntrySelector=1, RangeShift=0
    '0001 001E '       # 18: Glyph=1 (f_r), OffsetOfLigCaretEntry=30
    '0003 0022 '       # 22: Glyph=3 (f_f_l), OffsetOfLigCaretEntry=34
    'FFFF 0000 '       # 26: Glyph=<end>, OffsetOfLigCaretEntry=0
    '0001 00DC '       # 30: DivisionPointCount=1, DivisionPoint=[220]
    '0002 00EF 01D8 '  # 34: DivisionPointCount=2, DivisionPoint=[239, 475]
)                      # 40: <end>
assert(len(LCAR_FORMAT_0_DATA) == 40)


LCAR_FORMAT_0_XML = [
    '<Version value="0x00010000"/>',
    '<LigatureCarets Format="0">',
    '  <Carets>',
    '    <Lookup glyph="f_f_l">',
    '      <!-- DivsionPointCount=2 -->',
    '      <DivisionPoint index="0" value="239"/>',
    '      <DivisionPoint index="1" value="472"/>',
    '    </Lookup>',
    '    <Lookup glyph="f_r">',
    '      <!-- DivsionPointCount=1 -->',
    '      <DivisionPoint index="0" value="220"/>',
    '    </Lookup>',
    '  </Carets>',
    '</LigatureCarets>',
]


# Example: Format 1 Ligature Caret Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6lcar.html
LCAR_FORMAT_1_DATA = deHexStr(
    '0001 0000 0001 '  #  0: Version=1.0, Format=1
    '0006 0004 0002 '  #  6: LookupFormat=6, UnitSize=4, NUnits=2
    '0008 0001 0000 '  # 12: SearchRange=8, EntrySelector=1, RangeShift=0
    '0001 001E '       # 18: Glyph=1 (f_r), OffsetOfLigCaretEntry=30
    '0003 0022 '       # 22: Glyph=3 (f_f_l), OffsetOfLigCaretEntry=34
    'FFFF 0000 '       # 26: Glyph=<end>, OffsetOfLigCaretEntry=0
    '0001 0032 '       # 30: DivisionPointCount=1, DivisionPoint=[50]
    '0002 0037 004B '  # 34: DivisionPointCount=2, DivisionPoint=[55, 75]
)                      # 40: <end>
assert(len(LCAR_FORMAT_1_DATA) == 40)


LCAR_FORMAT_1_XML = [
    '<Version value="0x00010000"/>',
    '<LigatureCarets Format="1">',
    '  <Carets>',
    '    <Lookup glyph="f_f_l">',
    '      <!-- DivsionPointCount=2 -->',
    '      <DivisionPoint index="0" value="55"/>',
    '      <DivisionPoint index="1" value="75"/>',
    '    </Lookup>',
    '    <Lookup glyph="f_r">',
    '      <!-- DivsionPointCount=1 -->',
    '      <DivisionPoint index="0" value="50"/>',
    '    </Lookup>',
    '  </Carets>',
    '</LigatureCarets>',
]


class LCARTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(['.notdef', 'f_r', 'X', 'f_f_l'])

    def test_decompile_toXML_format0(self):
        table = newTable('lcar')
        table.decompile(LCAR_FORMAT_0_DATA, self.font)
        self.assertEqual(getXML(table.toXML), LCAR_FORMAT_0_XML)

    def test_compile_fromXML_format0(self):
        table = newTable('lcar')
        for name, attrs, content in parseXML(LCAR_FORMAT_0_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(LCAR_FORMAT_0_DATA))

    def test_decompile_toXML_format1(self):
        table = newTable('lcar')
        table.decompile(LCAR_FORMAT_1_DATA, self.font)
        self.assertEqual(getXML(table.toXML), LCAR_FORMAT_1_XML)

    def test_compile_fromXML_format1(self):
        table = newTable('lcar')
        for name, attrs, content in parseXML(LCAR_FORMAT_1_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(LCAR_FORMAT_1_DATA))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
