from __future__ import print_function, division, absolute_import
from fontTools.cffLib import TopDict, PrivateDict, CharStrings
from fontTools.misc.testTools import parseXML
import unittest


class TopDictTest(unittest.TestCase):

    def test_recalcFontBBox(self):
        topDict = TopDict()
        topDict.CharStrings = CharStrings(None, None, None, PrivateDict(), None, None)
        topDict.CharStrings.fromXML(None, None, parseXML("""
            <CharString name=".notdef">
              endchar
            </CharString>
            <CharString name="foo"><!-- [100, -100, 300, 100] -->
              100 -100 rmoveto 200 hlineto 200 vlineto -200 hlineto endchar
            </CharString>
            <CharString name="bar"><!-- [0, 0, 200, 200] -->
              0 0 rmoveto 200 hlineto 200 vlineto -200 hlineto endchar
            </CharString>
            <CharString name="baz"><!-- [-55.1, -55.1, 55.1, 55.1] -->
              -55.1 -55.1 rmoveto 110.2 hlineto 110.2 vlineto -110.2 hlineto endchar
            </CharString>
        """))

        topDict.recalcFontBBox()
        self.assertEqual(topDict.FontBBox, [-56, -100, 300, 200])

    def test_recalcFontBBox_empty(self):
        topDict = TopDict()
        topDict.CharStrings = CharStrings(None, None, None, PrivateDict(), None, None)
        topDict.CharStrings.fromXML(None, None, parseXML("""
            <CharString name=".notdef">
              endchar
            </CharString>
            <CharString name="space">
              123 endchar
            </CharString>
        """))

        topDict.recalcFontBBox()
        self.assertEqual(topDict.FontBBox, [0, 0, 0, 0])


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
