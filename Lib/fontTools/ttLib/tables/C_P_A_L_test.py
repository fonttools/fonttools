from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import newTable
import unittest


CPAL_DATA_V0 = deHexStr(
    '00 00 00 02 00 02 00 04 00 00 00 10 00 00 00 02 '
    '00 00 00 FF FF CC 66 FF 00 00 00 FF 00 00 80 FF')


def xml_lines(writer):
    content = writer.file.getvalue().decode("utf-8")
    return [line.strip() for line in content.splitlines()][1:]


class CPALTest(unittest.TestCase):
    def test_decompile_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(cpal.version, 0)
        self.assertEqual(cpal.numPaletteEntries, 2)
        self.assertEqual(repr(cpal.palettes),
                         '[[#000000FF, #66CCFFFF], [#000000FF, #800000FF]]')

    def test_compile_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(cpal.compile(ttFont=None), CPAL_DATA_V0)

    def test_toXML_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(getXML(cpal.toXML),
                         '<version value="0"/>'
                         '<numPaletteEntries value="2"/>'
                         '<palette index="0">'
                         '  <color index="0" value="#000000FF"/>'
                         '  <color index="1" value="#66CCFFFF"/>'
                         '</palette>'
                         '<palette index="1">'
                         '  <color index="0" value="#000000FF"/>'
                         '  <color index="1" value="#800000FF"/>'
                         '</palette>')

    def test_fromXML_v0(self):
        cpal = newTable('CPAL')
        for name, attrs, content in parseXML(
                '<version value="0"/>'
                '<numPaletteEntries value="1"/>'
                '<palette index="0">'
                '  <color index="0" value="#12345678"/>'
                '  <color index="1" value="#FEDCBA98"/>'
                '</palette>'):
            cpal.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual(cpal.version, 0)
        self.assertEqual(cpal.numPaletteEntries, 1)
        self.assertEqual(repr(cpal.palettes), '[[#12345678, #FEDCBA98]]')


if __name__ == "__main__":
    unittest.main()
