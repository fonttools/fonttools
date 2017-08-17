from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


PROP_FORMAT_0_DATA = deHexStr(
    '0001 0000 0000 '  #  0: Version=1.0, Format=0
    '0005 '            #  6: DefaultProperties=European number terminator
)                      #  8: <end>
assert(len(PROP_FORMAT_0_DATA) == 8)


PROP_FORMAT_0_XML = [
    '<Version value="1.0"/>',
    '<GlyphProperties Format="0">',
    '  <DefaultProperties value="5"/>',
    '</GlyphProperties>',
]


PROP_FORMAT_1_DATA = deHexStr(
    '0003 0000 0001 '  #  0: Version=3.0, Format=1
    '0000 '            #  6: DefaultProperties=left-to-right; non-whitespace
    '0008 0003 0004 '  #  8: LookupFormat=8, FirstGlyph=3, GlyphCount=4
    '000B '            # 14: Properties[C]=other neutral
    '000A '            # 16: Properties[D]=whitespace
    '600B '            # 18: Properties[E]=other neutral; hanging punct
    '0005 '            # 20: Properties[F]=European number terminator
)                      # 22: <end>
assert(len(PROP_FORMAT_1_DATA) == 22)


PROP_FORMAT_1_XML = [
    '<Version value="3.0"/>',
    '<GlyphProperties Format="1">',
    '  <DefaultProperties value="0"/>',
    '  <Properties>',
    '    <Lookup glyph="C" value="11"/>',
    '    <Lookup glyph="D" value="10"/>',
    '    <Lookup glyph="E" value="24587"/>',
    '    <Lookup glyph="F" value="5"/>',
    '  </Properties>',
    '</GlyphProperties>',
]


class PROPTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(['.notdef', 'A', 'B', 'C', 'D', 'E', 'F', 'G'])

    def test_decompile_toXML_format0(self):
        table = newTable('prop')
        table.decompile(PROP_FORMAT_0_DATA, self.font)
        self.assertEqual(getXML(table.toXML), PROP_FORMAT_0_XML)

    def test_compile_fromXML_format0(self):
        table = newTable('prop')
        for name, attrs, content in parseXML(PROP_FORMAT_0_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(PROP_FORMAT_0_DATA))

    def test_decompile_toXML_format1(self):
        table = newTable('prop')
        table.decompile(PROP_FORMAT_1_DATA, self.font)
        self.assertEqual(getXML(table.toXML), PROP_FORMAT_1_XML)

    def test_compile_fromXML_format1(self):
        table = newTable('prop')
        for name, attrs, content in parseXML(PROP_FORMAT_1_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(PROP_FORMAT_1_DATA))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
