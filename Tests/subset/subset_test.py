from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import subset
from fontTools.ttLib import TTFont, newTable
from fontTools.misc.loggingTools import CapturingLogHandler
import difflib
import logging
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
        return os.path.join(path, "data", testfile)

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
                    expected, actual, fromfile=expected_ttx, tofile=path):
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

    def test_subset_gvar(self):
        _, fontpath = self.compile_font(self.getpath("TestGVAR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+002B,U+2212", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_keep_gvar.ttx"), ["GlyphOrder", "avar", "fvar", "gvar", "name"])

    def test_subset_gvar_notdef_outline(self):
        _, fontpath = self.compile_font(self.getpath("TestGVAR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030", "--notdef_outline", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_keep_gvar_notdef_outline.ttx"), ["GlyphOrder", "avar", "fvar", "gvar", "name"])

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

    def test_timing_publishes_parts(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")

        options = subset.Options()
        options.timing = True
        subsetter = subset.Subsetter(options)
        subsetter.populate(text='ABC')
        font = TTFont(fontpath)
        with CapturingLogHandler('fontTools.subset.timer', logging.DEBUG) as captor:
            captor.logger.propagate = False
            subsetter.subset(font)
            logs = captor.records
        captor.logger.propagate = True

        self.assertTrue(len(logs) > 5)
        self.assertEqual(len(logs), len([l for l in logs if 'msg' in l.args and 'time' in l.args]))
        # Look for a few things we know should happen
        self.assertTrue(filter(lambda l: l.args['msg'] == "load 'cmap'", logs))
        self.assertTrue(filter(lambda l: l.args['msg'] == "subset 'cmap'", logs))
        self.assertTrue(filter(lambda l: l.args['msg'] == "subset 'glyf'", logs))

    def test_passthrough_tables(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")
        font = TTFont(fontpath)
        unknown_tag = 'ZZZZ'
        unknown_table = newTable(unknown_tag)
        unknown_table.data = b'\0'*10
        font[unknown_tag] = unknown_table
        font.save(fontpath)

        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)

        # tables we can't subset are dropped by default
        self.assertFalse(unknown_tag in subsetfont)

        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--passthrough-tables", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)

        # unknown tables are kept if --passthrough-tables option is passed
        self.assertTrue(unknown_tag in subsetfont)

    def test_non_BMP_text_arg_input(self):
        _, fontpath = self.compile_font(
            self.getpath("TestTTF-Regular_non_BMP_char.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        text = tostr(u"A\U0001F6D2", encoding='utf-8')

        subset.main([fontpath, "--text=%s" % text, "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)

        self.assertEqual(subsetfont['maxp'].numGlyphs, 3)
        self.assertEqual(subsetfont.getGlyphOrder(), ['.notdef', 'A', 'u1F6D2'])

    def test_non_BMP_text_file_input(self):
        _, fontpath = self.compile_font(
            self.getpath("TestTTF-Regular_non_BMP_char.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        text = tobytes(u"A\U0001F6D2", encoding='utf-8')
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(text)

        try:
            subset.main([fontpath, "--text-file=%s" % tmp.name,
                         "--output-file=%s" % subsetpath])
            subsetfont = TTFont(subsetpath)
        finally:
            os.remove(tmp.name)

        self.assertEqual(subsetfont['maxp'].numGlyphs, 3)
        self.assertEqual(subsetfont.getGlyphOrder(), ['.notdef', 'A', 'u1F6D2'])

    def test_no_hinting_CFF(self):
        ttxpath = self.getpath("Lobster.subset.ttx")
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--no-hinting", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "expect_no_hinting_CFF.ttx"), ["CFF "])

    def test_desubroutinize_CFF(self):
        ttxpath = self.getpath("Lobster.subset.ttx")
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--desubroutinize", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "expect_desubroutinize_CFF.ttx"), ["CFF "])

    def test_no_hinting_desubroutinize_CFF(self):
        ttxpath = self.getpath("Lobster.subset.ttx")
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--no-hinting", "--desubroutinize", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "expect_no_hinting_desubroutinize_CFF.ttx"), ["CFF "])

    def test_no_hinting_TTF(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--no-hinting", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "expect_no_hinting_TTF.ttx"), ["glyf", "maxp"])
        for tag in subset.Options().hinting_tables:
            self.assertTrue(tag not in subsetfont)

    def test_notdef_width_cid(self):
        # https://github.com/fonttools/fonttools/pull/845
        _, fontpath = self.compile_font(self.getpath("NotdefWidthCID-Regular.ttx"), ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--no-notdef-outline", "--gids=0,1", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_notdef_width_cid.ttx"), ["CFF "])

    def test_recalc_timestamp_ttf(self):
        ttxpath = self.getpath("TestTTF-Regular.ttx")
        font = TTFont()
        font.importXML(ttxpath)
        modified = font['head'].modified
        _, fontpath = self.compile_font(ttxpath, ".ttf")
        subsetpath = self.temp_path(".ttf")

        # by default, the subsetter does not recalculate the modified timestamp
        subset.main([fontpath, "--output-file=%s" % subsetpath, "*"])
        self.assertEqual(modified, TTFont(subsetpath)['head'].modified)

        subset.main([fontpath, "--recalc-timestamp", "--output-file=%s" % subsetpath, "*"])
        self.assertLess(modified, TTFont(subsetpath)['head'].modified)

    def test_recalc_timestamp_otf(self):
        ttxpath = self.getpath("TestOTF-Regular.ttx")
        font = TTFont()
        font.importXML(ttxpath)
        modified = font['head'].modified
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")

        # by default, the subsetter does not recalculate the modified timestamp
        subset.main([fontpath, "--output-file=%s" % subsetpath, "*"])
        self.assertEqual(modified, TTFont(subsetpath)['head'].modified)

        subset.main([fontpath, "--recalc-timestamp", "--output-file=%s" % subsetpath, "*"])
        self.assertLess(modified, TTFont(subsetpath)['head'].modified)


if __name__ == "__main__":
    sys.exit(unittest.main())
