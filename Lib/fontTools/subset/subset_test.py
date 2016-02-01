from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import subset
from fontTools.ttLib import TTFont
import difflib
import os
import shutil
import sys
import tempfile
import unittest


class SubsetTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", testfile)

    def temp_path(self, suffix):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir,
                            "tmp%d%s" % (self.num_tempfiles, suffix))

    def read_ttx(self, path):
        lines = []
        with open(path, "r", encoding="utf-8") as ttx:
            for line in ttx.readlines():
                # Elide ttFont attributes because ttLibVersion may change,
                # and use os-native line separators so we can run difflib.
                if line.startswith("<ttFont "):
                    lines.append("<ttFont>" + os.linesep)
                else:
                    lines.append(line.rstrip() + os.linesep)
        return lines

    def expect_ttx(self, font, expected_ttx, tables):
        path = self.temp_path(suffix=".ttx")
        font.saveXML(path, tables=tables)
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                    expected, actual, fromfile=path, tofile=expected_ttx):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def compile_font(self, path, suffix):
        savepath = self.temp_path(suffix=suffix)
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

# -----
# Tests
# -----

    def test_no_notdef_outline_otf(self):
        _, fontpath = self.compile_font(self.getpath("TestOTF-Regular.ttx"), ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--no-notdef-outline", "--gids=0", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_no_notdef_outline_otf.ttx"), ["CFF "])

    def test_no_notdef_outline_cid(self):
        _, fontpath = self.compile_font(self.getpath("TestCID-Regular.ttx"), ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--no-notdef-outline", "--gids=0", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_no_notdef_outline_cid.ttx"), ["CFF "])

    def test_no_notdef_outline_ttf(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--no-notdef-outline", "--gids=0", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_no_notdef_outline_ttf.ttx"), ["glyf", "hmtx"])

    def test_subset_clr(self):
        _, fontpath = self.compile_font(self.getpath("TestCLR-Regular.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=smileface", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_keep_colr.ttx"), ["GlyphOrder", "hmtx", "glyf", "COLR", "CPAL"])

    def test_subset_math(self):
        _, fontpath = self.compile_font(self.getpath("TestMATH-Regular.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0041,U+0028,U+0302,U+1D400,U+1D435", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_keep_math.ttx"), ["GlyphOrder", "CFF ", "MATH", "hmtx"])

    def test_options(self):
        # https://github.com/behdad/fonttools/issues/413
        opt1 = subset.Options()
        self.assertTrue('Xyz-' not in opt1.layout_features)
        opt2 = subset.Options()
        opt2.layout_features.append('Xyz-')
        self.assertTrue('Xyz-' in opt2.layout_features)
        self.assertTrue('Xyz-' not in opt1.layout_features)

    def test_google_color(self):
        _, fontpath = self.compile_font(self.getpath("google_color.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--gids=0,1", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.assertTrue("CBDT" in subsetfont)
        self.assertTrue("CBLC" in subsetfont)
        self.assertTrue("x" in subsetfont['CBDT'].strikeData[0])
        self.assertFalse("y" in subsetfont['CBDT'].strikeData[0])

    def test_google_color_all(self):
        _, fontpath = self.compile_font(self.getpath("google_color.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=*", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.assertTrue("x" in subsetfont['CBDT'].strikeData[0])
        self.assertTrue("y" in subsetfont['CBDT'].strikeData[0])

if __name__ == "__main__":
    unittest.main()
