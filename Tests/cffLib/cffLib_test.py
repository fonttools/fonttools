from __future__ import print_function, division, absolute_import
from fontTools.cffLib import TopDict, PrivateDict, CharStrings
from fontTools.misc.testTools import parseXML, DataFilesHandler
from fontTools.ttLib import TTFont
import copy
import os
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
        ttx_path = self.getpath('TestOTF.ttx')
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(ttx_path)

        topDict = font["CFF "].cff.topDictIndex[0]
        encoding = [".notdef"] * 256
        encoding[0x20] = "space"
        topDict.Encoding = encoding
        
        self.temp_dir()
        save_path = os.path.join(self.tempdir, 'TestOTF.otf')
        font.save(save_path)

        font2 = TTFont(save_path)
        topDict2 = font2["CFF "].cff.topDictIndex[0]
        self.assertEqual(topDict2.Encoding[32], "space")

    def test_CFF_deepcopy(self):
        """Test that deepcopying a TTFont with a CFF table does not recurse
        infinitely."""
        ttx_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "varLib",
            "data",
            "master_ttx_interpolatable_otf",
            "TestFamily2-Master0.ttx",
        )
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(ttx_path)
        copy.deepcopy(font)


if __name__ == "__main__":
    sys.exit(unittest.main())
