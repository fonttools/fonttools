from __future__ import print_function, division, absolute_import
from fontTools.cffLib import TopDict, PrivateDict, CharStrings
from fontTools.misc.testTools import parseXML, DataFilesHandler
from fontTools.ttLib import TTFont
import sys
import unittest


class CffLibTest(DataFilesHandler):

    def test_topDict_recalcFontBBox(self):
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

    def test_topDict_recalcFontBBox_empty(self):
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

    def test_topDict_set_Encoding(self):
        file_name = 'TestOTF.otf'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        save_path = temp_path[:-4] + '2.otf'
        font = TTFont(temp_path)
        topDict = font["CFF "].cff.topDictIndex[0]
        encoding = [".notdef"] * 256
        encoding[0x20] = "space"
        topDict.Encoding = encoding
        font.save(save_path)
        font2 = TTFont(save_path)
        topDict2 = font2["CFF "].cff.topDictIndex[0]
        self.assertEqual(topDict2.Encoding[32], "space")


if __name__ == "__main__":
    sys.exit(unittest.main())
