# coding: utf-8
from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# On macOS X 10.12.3, the font /Library/Fonts/AppleGothic.ttf has a ‘gcid’
# table with a similar structure as this test data, just more CIDs.
GCID_DATA = deHexStr(
    "0000 0000 "          #   0: Format=0, Flags=0
    "0000 0098 "          #   4: Size=152
    "0000 "               #   8: Registry=0
    "41 64 6F 62 65 "     #  10: RegistryName="Adobe"
    + ("00" * 59) +       #  15: <padding>
    "0003 "               #  74: Order=3
    "4B 6F 72 65 61 31 "  #  76: Order="Korea1"
    + ("00" * 58) +       #  82: <padding>
    "0001 "               # 140: SupplementVersion
    "0004 "               # 142: Count
    "1234 "               # 144: CIDs[0/.notdef]=4660
    "FFFF "               # 146: CIDs[1/A]=None
    "0007 "               # 148: CIDs[2/B]=7
    "DEF0 "               # 150: CIDs[3/C]=57072
)                         # 152: <end>
assert len(GCID_DATA) == 152, len(GCID_DATA)


GCID_XML = [
   '<GlyphCIDMapping Format="0">',
   '  <DataFormat value="0"/>',
   '  <!-- StructLength=152 -->',
   '  <Registry value="0"/>',
   '  <RegistryName value="Adobe"/>',
   '  <Order value="3"/>',
   '  <OrderName value="Korea1"/>',
   '  <SupplementVersion value="1"/>',
   '  <Mapping>',
   '    <CID glyph=".notdef" value="4660"/>',
   '    <CID glyph="B" value="7"/>',
   '    <CID glyph="C" value="57072"/>',
   '  </Mapping>',
   '</GlyphCIDMapping>',
]


class GCIDTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(['.notdef', 'A', 'B', 'C', 'D'])

    def testDecompileToXML(self):
        table = newTable('gcid')
        table.decompile(GCID_DATA, self.font)
        self.assertEqual(getXML(table.toXML, self.font), GCID_XML)

    def testCompileFromXML(self):
        table = newTable('gcid')
        for name, attrs, content in parseXML(GCID_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(GCID_DATA))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
