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


# This is the content of the Optical Bounds table in AppleChancery.ttf,
# font version 8.0d1e1 of 2013-02-06. An early version of fontTools
# was crashing when trying to decompile this table.
# https://github.com/fonttools/fonttools/issues/1031
OPBD_APPLE_CHANCERY_DATA = deHexStr(
    '0001 0000 0000 '  #   0: Version=1.0, Format=0
    '0004 0006 0011 '  #   6: LookupFormat=4, UnitSize=6, NUnits=17
    '0060 0004 0006 '  #  12: SearchRange=96, EntrySelector=4, RangeShift=6
    '017d 017d 0072 '  #  18: Seg[0].LastGlyph=381, FirstGlyph=381, Off=114(+6)
    '0183 0180 0074 '  #  24: Seg[1].LastGlyph=387, FirstGlyph=384, Off=116(+6)
    '0186 0185 007c '  #  30: Seg[2].LastGlyph=390, FirstGlyph=389, Off=124(+6)
    '018f 018b 0080 '  #  36: Seg[3].LastGlyph=399, FirstGlyph=395, Off=128(+6)
    '01a0 0196 008a '  #  42: Seg[4].LastGlyph=416, FirstGlyph=406, Off=138(+6)
    '01a5 01a3 00a0 '  #  48: Seg[5].LastGlyph=421, FirstGlyph=419, Off=160(+6)
    '01aa 01aa 00a6 '  #  54: Seg[6].LastGlyph=426, FirstGlyph=426, Off=166(+6)
    '01ac 01ac 00a8 '  #  60: Seg[7].LastGlyph=428, FirstGlyph=428, Off=168(+6)
    '01fb 01f1 00aa '  #  66: Seg[8].LastGlyph=507, FirstGlyph=497, Off=170(+6)
    '0214 0209 00c0 '  #  72: Seg[9].LastGlyph=532, FirstGlyph=521, Off=192(+6)
    '021d 0216 00d8 '  #  78: Seg[10].LastGlyph=541, FirstGlyph=534, Off=216(+6)
    '0222 0220 00e8 '  #  84: Seg[11].LastGlyph=546, FirstGlyph=544, Off=232(+6)
    '0227 0225 00ee '  #  90: Seg[12].LastGlyph=551, FirstGlyph=549, Off=238(+6)
    '0229 0229 00f4 '  #  96: Seg[13].LastGlyph=553, FirstGlyph=553, Off=244(+6)
    '023b 023b 00f6 '  # 102: Seg[14].LastGlyph=571, FirstGlyph=571, Off=246(+6)
    '023e 023e 00f8 '  # 108: Seg[15].LastGlyph=574, FirstGlyph=574, Off=248(+6)
    'ffff ffff 00fa '  # 114: Seg[16]=<end>
    '0100 0108 0110 0118 0120 0128 0130 0138 0140 0148 0150 0158 '
    '0160 0168 0170 0178 0180 0188 0190 0198 01a0 01a8 01b0 01b8 '
    '01c0 01c8 01d0 01d8 01e0 01e8 01f0 01f8 0200 0208 0210 0218 '
    '0220 0228 0230 0238 0240 0248 0250 0258 0260 0268 0270 0278 '
    '0280 0288 0290 0298 02a0 02a8 02b0 02b8 02c0 02c8 02d0 02d8 '
    '02e0 02e8 02f0 02f8 0300 0308 0310 0318 fd98 0000 0000 0000 '
    'fdbc 0000 0000 0000 fdbc 0000 0000 0000 fdbf 0000 0000 0000 '
    'fdbc 0000 0000 0000 fd98 0000 0000 0000 fda9 0000 0000 0000 '
    'fd98 0000 0000 0000 fd98 0000 0000 0000 fd98 0000 0000 0000 '
    '0000 0000 0205 0000 0000 0000 0205 0000 0000 0000 02a4 0000 '
    '0000 0000 027e 0000 0000 0000 02f4 0000 0000 0000 02a4 0000 '
    '0000 0000 0365 0000 0000 0000 0291 0000 0000 0000 0291 0000 '
    '0000 0000 026a 0000 0000 0000 02b8 0000 0000 0000 02cb 0000 '
    '0000 0000 02a4 0000 0000 0000 01a9 0000 0000 0000 0244 0000 '
    '0000 0000 02a4 0000 0000 0000 02cb 0000 0000 0000 0244 0000 '
    '0000 0000 0307 0000 0000 0000 0307 0000 0000 0000 037f 0000 '
    '0000 0000 0307 0000 0000 0000 0307 0000 0000 0000 0307 0000 '
    '0000 0000 0307 0000 0000 0000 0307 0000 0000 0000 03e3 0000 '
    '0000 0000 030c 0000 0000 0000 0307 0000 fe30 0000 0000 0000 '
    'fe7e 0000 0000 0000 fe91 0000 0000 0000 fe6a 0000 0000 0000 '
    'fe6a 0000 0000 0000 fecb 0000 0000 0000 fe6a 0000 0000 0000 '
    'fe7e 0000 0000 0000 fea4 0000 0000 0000 fe7e 0000 0000 0000 '
    'fe44 0000 0000 0000 fea4 0000 0000 0000 feb8 0000 0000 0000 '
    'fe7e 0000 0000 0000 fe5e 0000 0000 0000 fe37 0000 0000 0000 '
    'fe37 0000 0000 0000 fcbd 0000 0000 0000 fd84 0000 0000 0000 '
    'fd98 0000 0000 0000 fd82 0000 0000 0000 fcbd 0000 0000 0000 '
    'fd84 0000 0000 0000 fcbd 0000 0000 0000 fcbd 0000 0000 0000 '
    'fe72 0000 0000 0000 ff9d 0000 0000 0000 0000 0000 032f 0000 '
    '0000 0000 03ba 0000 '
)
assert len(OPBD_APPLE_CHANCERY_DATA) == 800


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

    def test_decompile_AppleChancery(self):
        # Make sure we do not crash when decompiling the 'opbd' table of
        # AppleChancery.ttf. https://github.com/fonttools/fonttools/issues/1031
        table = newTable('opbd')
        table.decompile(OPBD_APPLE_CHANCERY_DATA, self.font)
        self.assertIn('<OpticalBounds Format="0">', getXML(table.toXML))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
