import os
import sys

libdir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "Lib"
)
sys.path.insert(0, libdir)

from fontTools.cffLib import TopDict, PrivateDict, CharStrings, CFFFontSet
from fontTools.misc.testTools import parseXML, DataFilesHandler
from fontTools.ttLib import TTFont
import copy
import unittest
from io import BytesIO
import pytest


class CffLibTest(DataFilesHandler):
    def test_VARC_short_CharStrings_roundtrip(self):
        for format in (3, 4):
            for retainGids in (False, True):
                with self.subTest(format=format, retainGids=retainGids):
                    self._check_VARC_short_CharStrings_roundtrip(format, retainGids)

    def _check_VARC_short_CharStrings_roundtrip(self, format, retainGids):
        from fontTools.pens.boundsPen import BoundsPen
        from fontTools import subset

        font = TTFont(self.getpath("varc-short-cff2.otf"))
        top = font["CFF2"].cff.topDictIndex[0]
        top.FDSelect.format = format

        def check(font):
            order = font.getGlyphOrder()
            top = font["CFF2"].cff.topDictIndex[0]
            assert len(top.CharStrings) < len(order)
            assert top.charset == order[: len(top.CharStrings)]
            assert len(top.FDSelect) == len(order)
            glyphSet = font.getGlyphSet()
            assert list(glyphSet) == order
            composite = font["VARC"].table.Coverage.glyphs[0]
            assert composite in glyphSet
            pen = BoundsPen(glyphSet)
            glyphSet[composite].draw(pen)
            assert pen.bounds == (600, 0, 800, 200)
            assert glyphSet[composite].width == 500
            assert font["head"].xMax == 800
            assert font["head"].yMax == 200
            assert font["hhea"].xMaxExtent == 200
            assert font["vhea"].yMaxExtent == 200
            assert top.FDSelect.gidArray[-1] == 1

        for _ in range(2):
            check(font)
            data = BytesIO()
            font.save(data)
            font = TTFont(BytesIO(data.getvalue()))
        xml = BytesIO()
        font.saveXML(xml)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        data = BytesIO()
        font.save(data)
        font = TTFont(BytesIO(data.getvalue()))
        check(font)

        options = subset.Options()
        options.retain_gids = retainGids
        # Preserve both FDs: one is used only by the VARC-only glyph.
        options.hinting = True
        sub = subset.Subsetter(options=options)
        sub.populate(glyphs=["composite"])
        sub.subset(font)
        data = BytesIO()
        font.save(data)
        font = TTFont(BytesIO(data.getvalue()))
        check(font)

    def test_CFF2_count_mismatch_without_VARC(self):
        font = TTFont(self.getpath("varc-short-cff2.otf"))
        font["CFF2"].cff.topDictIndex[0].CharStrings
        del font["VARC"]
        with pytest.raises(ValueError, match="CharStrings count"):
            font.save(BytesIO())

    def test_CFF2_CharStrings_must_be_prefix(self):
        font = TTFont(self.getpath("varc-short-cff2.otf"))
        strings = font["CFF2"].cff.topDictIndex[0].CharStrings
        strings.charStrings["composite"] = strings.charStrings.pop("unused")
        with pytest.raises(ValueError, match="glyph-order prefix"):
            font.save(BytesIO())

    def test_FDSelect_VARC_sentinel_bounds(self):
        from fontTools.cffLib import FDSelect, packFDSelect3, packFDSelect4

        for pack in (packFDSelect3, packFDSelect4):
            for sentinel in (2, 3, 4, 5):
                data = BytesIO(pack([0] * sentinel))
                if sentinel in (3, 4):
                    select = FDSelect(data, 3, maxGlyphs=4)
                    assert len(select) == sentinel
                else:
                    with pytest.raises(ValueError, match="sentinel"):
                        FDSelect(data, 3, maxGlyphs=4)

    def test_topDict_recalcFontBBox(self):
        topDict = TopDict()
        topDict.CharStrings = CharStrings(None, None, None, PrivateDict(), None, None)
        topDict.CharStrings.fromXML(
            None,
            None,
            parseXML("""
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
        """),
        )

        topDict.recalcFontBBox()
        self.assertEqual(topDict.FontBBox, [-56, -100, 300, 200])

    def test_topDict_recalcFontBBox_empty(self):
        topDict = TopDict()
        topDict.CharStrings = CharStrings(None, None, None, PrivateDict(), None, None)
        topDict.CharStrings.fromXML(
            None,
            None,
            parseXML("""
            <CharString name=".notdef">
              endchar
            </CharString>
            <CharString name="space">
              123 endchar
            </CharString>
        """),
        )

        topDict.recalcFontBBox()
        self.assertEqual(topDict.FontBBox, [0, 0, 0, 0])

    def test_topDict_set_Encoding(self):
        ttx_path = self.getpath("TestOTF.ttx")
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(ttx_path)

        topDict = font["CFF "].cff.topDictIndex[0]
        encoding = [".notdef"] * 256
        encoding[0x20] = "space"
        topDict.Encoding = encoding

        self.temp_dir()
        save_path = os.path.join(self.tempdir, "TestOTF.otf")
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

    def test_CFF2_VarStore_recompiled_after_mutation(self):
        """A VarStore changed after a save must be written out as changed."""
        ttx_path = self.getpath("TestSparseCFF2VF.ttx")
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(ttx_path)
        font.save(BytesIO())

        varStore = font["CFF2"].cff.topDictIndex[0].VarStore.otVarStore
        varStore.VarRegionList.Region[0].VarRegionAxis[0].PeakCoord = 0.5

        buf = BytesIO()
        font.save(buf)
        buf.seek(0)
        font2 = TTFont(buf)

        varStore2 = font2["CFF2"].cff.topDictIndex[0].VarStore.otVarStore
        self.assertEqual(
            varStore2.VarRegionList.Region[0].VarRegionAxis[0].PeakCoord, 0.5
        )

    def test_FDSelect_format_4(self):
        ttx_path = self.getpath("TestFDSelect4.ttx")
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(ttx_path)

        self.temp_dir()
        save_path = os.path.join(self.tempdir, "TestOTF.otf")
        font.save(save_path)

        font2 = TTFont(save_path)
        topDict2 = font2["CFF2"].cff.topDictIndex[0]
        self.assertEqual(topDict2.FDSelect.format, 4)
        self.assertEqual(topDict2.FDSelect.gidArray, [0, 0, 1])

    def test_unique_glyph_names(self):
        font_path = self.getpath("LinLibertine_RBI.otf")
        font = TTFont(font_path, recalcBBoxes=False, recalcTimestamp=False)

        glyphOrder = font.getGlyphOrder()
        self.assertEqual(len(glyphOrder), len(set(glyphOrder)))

        self.temp_dir()
        save_path = os.path.join(self.tempdir, "TestOTF.otf")
        font.save(save_path)

        font2 = TTFont(save_path)
        glyphOrder = font2.getGlyphOrder()
        self.assertEqual(len(glyphOrder), len(set(glyphOrder)))

    def test_reading_supplement_encoding(self):
        cff_path = self.getpath("TestSupplementEncoding.cff")
        topDict = None
        with open(cff_path, "rb") as fontfile:
            cff = CFFFontSet()
            cff.decompile(fontfile, None)
            topDict = cff[0]
            self.assertEqual(topDict.Encoding[9], "space")
            self.assertEqual(topDict.Encoding[32], "space")


class CFFToCFF2Test(DataFilesHandler):
    def test_conversion(self):
        font_path = self.getpath("CFFToCFF2-1.otf")
        font = TTFont(font_path)
        from fontTools.cffLib.CFFToCFF2 import convertCFFToCFF2

        convertCFFToCFF2(font)
        f = BytesIO()
        font.save(f)


if __name__ == "__main__":
    sys.exit(unittest.main())
