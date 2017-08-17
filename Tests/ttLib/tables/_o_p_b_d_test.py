from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# Example: Format 0 Optical Bounds Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6opbd.html
OPBD_FORMAT_0_DATA = deHexStr(
    '0001 0000 0000 '       #  0: Version=1.0, Format=0
    '0006 0004 0002 '       #  6: LookupFormat=6, UnitSize=4, NUnits=2
    '0008 0001 0000 '       # 12: SearchRange=8, EntrySelector=1, RangeShift=0
    '000A 001E '            # 18: Glyph=10(=C), OffsetOfOpticalBoundsDeltas=30
    '002B 0026 '            # 22: Glyph=43(=A), OffsetOfOpticalBoundsDeltas=38
    'FFFF 0000 '            # 26: Glyph=<end>, OffsetOfOpticalBoundsDeltas=0
    'FFCE 0005 0037 FFFB '  # 30: Bounds[C].Left=-50 .Top=5 .Right=55 .Bottom=-5
    'FFF6 000F 0000 0000 '  # 38: Bounds[A].Left=-10 .Top=15 .Right=0 .Bottom=0
)                           # 46: <end>
assert(len(OPBD_FORMAT_0_DATA) == 46)


OPBD_FORMAT_0_XML = [
    '<Version value="0x00010000"/>',
    '<OpticalBounds Format="0">',
    '  <OpticalBoundsDeltas>',
    '    <Lookup glyph="A">',
    '      <Left value="-10"/>',
    '      <Top value="15"/>',
    '      <Right value="0"/>',
    '      <Bottom value="0"/>',
    '    </Lookup>',
    '    <Lookup glyph="C">',
    '      <Left value="-50"/>',
    '      <Top value="5"/>',
    '      <Right value="55"/>',
    '      <Bottom value="-5"/>',
    '    </Lookup>',
    '  </OpticalBoundsDeltas>',
    '</OpticalBounds>',
]


# Example: Format 1 Optical Bounds Table
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6opbd.html
OPBD_FORMAT_1_DATA = deHexStr(
    '0001 0000 0001 '       #  0: Version=1.0, Format=1
    '0006 0004 0002 '       #  6: LookupFormat=6, UnitSize=4, NUnits=2
    '0008 0001 0000 '       # 12: SearchRange=8, EntrySelector=1, RangeShift=0
    '000A 001E '            # 18: Glyph=10(=C), OffsetOfOpticalBoundsPoints=30
    '002B 0026 '            # 22: Glyph=43(=A), OffsetOfOpticalBoundsPoints=38
    'FFFF 0000 '            # 26: Glyph=<end>, OffsetOfOpticalBoundsPoints=0
    '0024 0025 0026 0027 '  # 30: Bounds[C].Left=36 .Top=37 .Right=38 .Bottom=39
    '0020 0029 FFFF FFFF '  # 38: Bounds[A].Left=32 .Top=41 .Right=-1 .Bottom=-1
)                           # 46: <end>
assert(len(OPBD_FORMAT_1_DATA) == 46)


OPBD_FORMAT_1_XML = [
    '<Version value="0x00010000"/>',
    '<OpticalBounds Format="1">',
    '  <OpticalBoundsPoints>',
    '    <Lookup glyph="A">',
    '      <Left value="32"/>',
    '      <Top value="41"/>',
    '      <Right value="-1"/>',
    '      <Bottom value="-1"/>',
    '    </Lookup>',
    '    <Lookup glyph="C">',
    '      <Left value="36"/>',
    '      <Top value="37"/>',
    '      <Right value="38"/>',
    '      <Bottom value="39"/>',
    '    </Lookup>',
    '  </OpticalBoundsPoints>',
    '</OpticalBounds>',
]


class OPBDTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        glyphs = ['.notdef'] + ['X.alt%d' for g in range(1, 50)]
        glyphs[10] = 'C'
        glyphs[43] = 'A'
        cls.font = FakeFont(glyphs)

    def test_decompile_toXML_format0(self):
        table = newTable('opbd')
        table.decompile(OPBD_FORMAT_0_DATA, self.font)
        self.assertEqual(getXML(table.toXML), OPBD_FORMAT_0_XML)

    def test_compile_fromXML_format0(self):
        table = newTable('opbd')
        for name, attrs, content in parseXML(OPBD_FORMAT_0_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(OPBD_FORMAT_0_DATA))

    def test_decompile_toXML_format1(self):
        table = newTable('opbd')
        table.decompile(OPBD_FORMAT_1_DATA, self.font)
        self.assertEqual(getXML(table.toXML), OPBD_FORMAT_1_XML)

    def test_compile_fromXML_format1(self):
        table = newTable('opbd')
        for name, attrs, content in parseXML(OPBD_FORMAT_1_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(OPBD_FORMAT_1_DATA))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
