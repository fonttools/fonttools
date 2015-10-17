from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont
from fontTools.misc.textTools import deHexStr
import fontTools.ttLib.tables.otConverters as otConverters
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
import unittest


class GlyphIDTest(unittest.TestCase):
    font = FakeFont(".notdef A B C".split())
    converter = otConverters.GlyphID('GlyphID', 0, None, None)

    def test_readArray(self):
        reader = OTTableReader(deHexStr("0002 0001 DEAD 0002"))
        self.assertEqual(self.converter.readArray(reader, self.font, {}, 4),
                         ["B", "A", "glyph57005", "B"])
        self.assertEqual(reader.pos, 8)

    def test_read(self):
        reader = OTTableReader(deHexStr("0003"))
        self.assertEqual(self.converter.read(reader, self.font, {}), "C")
        self.assertEqual(reader.pos, 2)

    def test_write(self):
        writer = OTTableWriter(globalState={})
        self.converter.write(writer, self.font, {}, "B")
        self.assertEqual(writer.getData(), deHexStr("0002"))


if __name__ == "__main__":
    unittest.main()
