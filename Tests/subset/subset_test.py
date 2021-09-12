import io
from fontTools.misc.py23 import tobytes, tostr
from fontTools.misc.testTools import getXML
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.misc.loggingTools import CapturingLogHandler
import difflib
import logging
import os
import shutil
import sys
import tempfile
import unittest
import pathlib
import pytest


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
                # Elide ttFont attributes because ttLibVersion may change.
                if line.startswith("<ttFont "):
                    lines.append("<ttFont>\n")
                else:
                    lines.append(line.rstrip() + "\n")
        return lines

    def expect_ttx(self, font, expected_ttx, tables=None):
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

    def test_layout_scripts(self):
        _, fontpath = self.compile_font(self.getpath("layout_scripts.ttx"), ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--glyphs=*", "--layout-features=*",
                     "--layout-scripts=latn,arab.URD,arab.dflt",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_layout_scripts.ttx"),
                        ["GPOS", "GSUB"])

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

    def test_subset_ankr(self):
        _, fontpath = self.compile_font(self.getpath("TestANKR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=one", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_ankr.ttx"), ["ankr"])

    def test_subset_ankr_remove(self):
        _, fontpath = self.compile_font(self.getpath("TestANKR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=two", "--output-file=%s" % subsetpath])
        self.assertNotIn("ankr", TTFont(subsetpath))

    def test_subset_bsln_format_0(self):
        _, fontpath = self.compile_font(self.getpath("TestBSLN-0.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=one", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_0.ttx"), ["bsln"])

    def test_subset_bsln_format_0_from_format_1(self):
        # TestBSLN-1 defines the ideographic baseline to be the font's default,
        # and specifies that glyphs {.notdef, zero, one, two} use the roman
        # baseline instead of the default ideographic baseline. As we request
        # a subsetted font with {zero, one} and the implicit .notdef, all
        # glyphs in the resulting font use the Roman baseline. In this case,
        # we expect a format 0 'bsln' table because it is the most compact.
        _, fontpath = self.compile_font(self.getpath("TestBSLN-1.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030-0031",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_0.ttx"), ["bsln"])

    def test_subset_bsln_format_1(self):
        # TestBSLN-1 defines the ideographic baseline to be the font's default,
        # and specifies that glyphs {.notdef, zero, one, two} use the roman
        # baseline instead of the default ideographic baseline. We request
        # a subset where the majority of glyphs use the roman baseline,
        # but one single glyph (uni2EA2) is ideographic. In the resulting
        # subsetted font, we expect a format 1 'bsln' table whose default
        # is Roman, but with an override that uses the ideographic baseline
        # for uni2EA2.
        _, fontpath = self.compile_font(self.getpath("TestBSLN-1.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030-0031,U+2EA2",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_1.ttx"), ["bsln"])

    def test_subset_bsln_format_2(self):
        # The 'bsln' table in TestBSLN-2 refers to control points in glyph 'P'
        # for defining its baselines. Therefore, the subsetted font should
        # include this glyph even though it is not requested explicitly.
        _, fontpath = self.compile_font(self.getpath("TestBSLN-2.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=one", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_2.ttx"), ["bsln"])

    def test_subset_bsln_format_2_from_format_3(self):
        # TestBSLN-3 defines the ideographic baseline to be the font's default,
        # and specifies that glyphs {.notdef, zero, one, two, P} use the roman
        # baseline instead of the default ideographic baseline. As we request
        # a subsetted font with zero and the implicit .notdef and P for
        # baseline measurement, all glyphs in the resulting font use the Roman
        # baseline. In this case, we expect a format 2 'bsln' table because it
        # is the most compact encoding.
        _, fontpath = self.compile_font(self.getpath("TestBSLN-3.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_2.ttx"), ["bsln"])

    def test_subset_bsln_format_3(self):
        # TestBSLN-3 defines the ideographic baseline to be the font's default,
        # and specifies that glyphs {.notdef, zero, one, two} use the roman
        # baseline instead of the default ideographic baseline. We request
        # a subset where the majority of glyphs use the roman baseline,
        # but one single glyph (uni2EA2) is ideographic. In the resulting
        # subsetted font, we expect a format 1 'bsln' table whose default
        # is Roman, but with an override that uses the ideographic baseline
        # for uni2EA2.
        _, fontpath = self.compile_font(self.getpath("TestBSLN-3.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030-0031,U+2EA2",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_bsln_3.ttx"), ["bsln"])

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

    def test_subset_lcar_remove(self):
        _, fontpath = self.compile_font(self.getpath("TestLCAR-0.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=one", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.assertNotIn("lcar", subsetfont)

    def test_subset_lcar_format_0(self):
        _, fontpath = self.compile_font(self.getpath("TestLCAR-0.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+FB01",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_lcar_0.ttx"), ["lcar"])

    def test_subset_lcar_format_1(self):
        _, fontpath = self.compile_font(self.getpath("TestLCAR-1.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+FB01",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_lcar_1.ttx"), ["lcar"])

    def test_subset_math(self):
        _, fontpath = self.compile_font(self.getpath("TestMATH-Regular.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0041,U+0028,U+0302,U+1D400,U+1D435", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_keep_math.ttx"), ["GlyphOrder", "CFF ", "MATH", "hmtx"])

    def test_subset_math_partial(self):
        _, fontpath = self.compile_font(self.getpath("test_math_partial.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--text=A", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_math_partial.ttx"), ["MATH"])

    def test_subset_opbd_remove(self):
        # In the test font, only the glyphs 'A' and 'zero' have an entry in
        # the Optical Bounds table. When subsetting, we do not request any
        # of those glyphs. Therefore, the produced subsetted font should
        # not contain an 'opbd' table.
        _, fontpath = self.compile_font(self.getpath("TestOPBD-0.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=one", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.assertNotIn("opbd", subsetfont)

    def test_subset_opbd_format_0(self):
        _, fontpath = self.compile_font(self.getpath("TestOPBD-0.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=A", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_opbd_0.ttx"), ["opbd"])

    def test_subset_opbd_format_1(self):
        _, fontpath = self.compile_font(self.getpath("TestOPBD-1.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=A", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_opbd_1.ttx"), ["opbd"])

    def test_subset_prop_remove_default_zero(self):
        # If all glyphs have an AAT glyph property with value 0,
        # the "prop" table should be removed from the subsetted font.
        _, fontpath = self.compile_font(self.getpath("TestPROP.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0041",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.assertNotIn("prop", subsetfont)

    def test_subset_prop_0(self):
        # If all glyphs share the same AAT glyph properties, the "prop" table
        # in the subsetted font should use format 0.
        #
        # Unless the shared value is zero, in which case the subsetted font
        # should have no "prop" table at all. But that case has already been
        # tested above in test_subset_prop_remove_default_zero().
        _, fontpath = self.compile_font(self.getpath("TestPROP.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030-0032", "--no-notdef-glyph",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_prop_0.ttx"), ["prop"])

    def test_subset_prop_1(self):
        # If not all glyphs share the same AAT glyph properties, the subsetted
        # font should contain a "prop" table in format 1. To save space, the
        # DefaultProperties should be set to the most frequent value.
        _, fontpath = self.compile_font(self.getpath("TestPROP.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=U+0030-0032", "--notdef-outline",
                     "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_prop_1.ttx"), ["prop"])

    def test_options(self):
        # https://github.com/fonttools/fonttools/issues/413
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

    def test_sbix(self):
        _, fontpath = self.compile_font(self.getpath("sbix.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--gids=0,1", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "expect_sbix.ttx"), ["sbix"])

    def test_timing_publishes_parts(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")

        options = subset.Options()
        options.timing = True
        subsetter = subset.Subsetter(options)
        subsetter.populate(text='ABC')
        font = TTFont(fontpath)
        with CapturingLogHandler('fontTools.subset.timer', logging.DEBUG) as captor:
            subsetter.subset(font)
        logs = captor.records

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

    def test_desubroutinize_hinted_subrs_CFF(self):
        ttxpath = self.getpath("test_hinted_subrs_CFF.ttx")
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--desubroutinize", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "test_hinted_subrs_CFF.desub.ttx"), ["CFF "])

    def test_desubroutinize_cntrmask_CFF(self):
        ttxpath = self.getpath("test_cntrmask_CFF.ttx")
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")
        subset.main([fontpath, "--desubroutinize", "--notdef-outline",
                     "--output-file=%s" % subsetpath, "*"])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath(
            "test_cntrmask_CFF.desub.ttx"), ["CFF "])

    def test_no_hinting_desubroutinize_CFF(self):
        ttxpath = self.getpath("test_hinted_subrs_CFF.ttx")
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

    def test_recalc_bounds_ttf(self):
        ttxpath = self.getpath("TestTTF-Regular.ttx")
        font = TTFont()
        font.importXML(ttxpath)
        head = font['head']
        bounds = [head.xMin, head.yMin, head.xMax, head.yMax]

        _, fontpath = self.compile_font(ttxpath, ".ttf")
        subsetpath = self.temp_path(".ttf")

        # by default, the subsetter does not recalculate the bounding box
        subset.main([fontpath, "--output-file=%s" % subsetpath, "*"])
        head = TTFont(subsetpath)['head']
        self.assertEqual(bounds, [head.xMin, head.yMin, head.xMax, head.yMax])

        subset.main([fontpath, "--recalc-bounds", "--output-file=%s" % subsetpath, "*"])
        head = TTFont(subsetpath)['head']
        bounds = [132, 304, 365, 567]
        self.assertEqual(bounds, [head.xMin, head.yMin, head.xMax, head.yMax])

    def test_recalc_bounds_otf(self):
        ttxpath = self.getpath("TestOTF-Regular.ttx")
        font = TTFont()
        font.importXML(ttxpath)
        head = font['head']
        bounds = [head.xMin, head.yMin, head.xMax, head.yMax]

        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")

        # by default, the subsetter does not recalculate the bounding box
        subset.main([fontpath, "--output-file=%s" % subsetpath, "*"])
        head = TTFont(subsetpath)['head']
        self.assertEqual(bounds, [head.xMin, head.yMin, head.xMax, head.yMax])

        subset.main([fontpath, "--recalc-bounds", "--output-file=%s" % subsetpath, "*"])
        head = TTFont(subsetpath)['head']
        bounds = [132, 304, 365, 567]
        self.assertEqual(bounds, [head.xMin, head.yMin, head.xMax, head.yMax])

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

    def test_recalc_max_context(self):
        ttxpath = self.getpath("Lobster.subset.ttx")
        font = TTFont()
        font.importXML(ttxpath)
        max_context = font['OS/2'].usMaxContext
        _, fontpath = self.compile_font(ttxpath, ".otf")
        subsetpath = self.temp_path(".otf")

        # by default, the subsetter does not recalculate the usMaxContext
        subset.main([fontpath, "--drop-tables+=GSUB,GPOS",
                               "--output-file=%s" % subsetpath])
        self.assertEqual(max_context, TTFont(subsetpath)['OS/2'].usMaxContext)

        subset.main([fontpath, "--recalc-max-context",
                               "--drop-tables+=GSUB,GPOS",
                               "--output-file=%s" % subsetpath])
        self.assertEqual(0, TTFont(subsetpath)['OS/2'].usMaxContext)

    def test_retain_gids_ttf(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")
        font = TTFont(fontpath)

        self.assertEqual(font["hmtx"]["A"], (500, 132))
        self.assertEqual(font["hmtx"]["B"], (400, 132))

        self.assertGreater(font["glyf"]["A"].numberOfContours, 0)
        self.assertGreater(font["glyf"]["B"].numberOfContours, 0)

        subsetpath = self.temp_path(".ttf")
        subset.main(
            [
                fontpath,
                "--retain-gids",
                "--output-file=%s" % subsetpath,
                "--glyph-names",
                "B",
            ]
        )
        subsetfont = TTFont(subsetpath)

        self.assertEqual(subsetfont.getGlyphOrder(), font.getGlyphOrder()[0:3])

        hmtx = subsetfont["hmtx"]
        self.assertEqual(hmtx["A"], (  0,   0))
        self.assertEqual(hmtx["B"], (400, 132))

        glyf = subsetfont["glyf"]
        self.assertEqual(glyf["A"].numberOfContours, 0)
        self.assertGreater(glyf["B"].numberOfContours, 0)

    def test_retain_gids_cff(self):
        _, fontpath = self.compile_font(self.getpath("TestOTF-Regular.ttx"), ".otf")
        font = TTFont(fontpath)

        self.assertEqual(font["hmtx"]["A"], (500, 132))
        self.assertEqual(font["hmtx"]["B"], (400, 132))
        self.assertEqual(font["hmtx"]["C"], (500,   0))

        font["CFF "].cff[0].decompileAllCharStrings()
        cs = font["CFF "].cff[0].CharStrings
        self.assertGreater(len(cs["A"].program), 0)
        self.assertGreater(len(cs["B"].program), 0)
        self.assertGreater(len(cs["C"].program), 0)

        subsetpath = self.temp_path(".otf")
        subset.main(
            [
                fontpath,
                "--retain-gids",
                "--output-file=%s" % subsetpath,
                "--glyph-names",
                "B",
            ]
        )
        subsetfont = TTFont(subsetpath)

        self.assertEqual(subsetfont.getGlyphOrder(), font.getGlyphOrder()[0:3])

        hmtx = subsetfont["hmtx"]
        self.assertEqual(hmtx["A"], (0,     0))
        self.assertEqual(hmtx["B"], (400, 132))

        subsetfont["CFF "].cff[0].decompileAllCharStrings()
        cs = subsetfont["CFF "].cff[0].CharStrings

        self.assertEqual(cs["A"].program, ["endchar"])
        self.assertGreater(len(cs["B"].program), 0)

    def test_retain_gids_cff2(self):
        ttx_path = self.getpath("../../varLib/data/master_ttx_varfont_otf/TestCFF2VF.ttx")
        font, fontpath = self.compile_font(ttx_path, ".otf")

        self.assertEqual(font["hmtx"]["A"], (600, 31))
        self.assertEqual(font["hmtx"]["T"], (600, 41))

        font["CFF2"].cff[0].decompileAllCharStrings()
        cs = font["CFF2"].cff[0].CharStrings
        self.assertGreater(len(cs["A"].program), 0)
        self.assertGreater(len(cs["T"].program), 0)

        subsetpath = self.temp_path(".otf")
        subset.main(
            [
                fontpath,
                "--retain-gids",
                "--output-file=%s" % subsetpath,
                "T",
            ]
        )
        subsetfont = TTFont(subsetpath)

        self.assertEqual(len(subsetfont.getGlyphOrder()), len(font.getGlyphOrder()[0:3]))

        hmtx = subsetfont["hmtx"]
        self.assertEqual(hmtx["glyph00001"], (  0,  0))
        self.assertEqual(hmtx["T"], (600, 41))

        subsetfont["CFF2"].cff[0].decompileAllCharStrings()
        cs = subsetfont["CFF2"].cff[0].CharStrings
        self.assertEqual(cs["glyph00001"].program, [])
        self.assertGreater(len(cs["T"].program), 0)

    def test_HVAR_VVAR(self):
        _, fontpath = self.compile_font(self.getpath("TestHVVAR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--text=BD", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_HVVAR.ttx"), ["GlyphOrder", "HVAR", "VVAR", "avar", "fvar"])

    def test_HVAR_VVAR_retain_gids(self):
        _, fontpath = self.compile_font(self.getpath("TestHVVAR.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--text=BD", "--retain-gids", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("expect_HVVAR_retain_gids.ttx"), ["GlyphOrder", "HVAR", "VVAR", "avar", "fvar"])

    def test_subset_flavor(self):
        _, fontpath = self.compile_font(self.getpath("TestTTF-Regular.ttx"), ".ttf")
        font = TTFont(fontpath)

        woff_path = self.temp_path(".woff")
        subset.main(
            [
                fontpath,
                "*",
                "--flavor=woff",
                "--output-file=%s" % woff_path,
            ]
        )
        woff = TTFont(woff_path)

        self.assertEqual(woff.flavor, "woff")

        woff2_path = self.temp_path(".woff2")
        subset.main(
            [
                woff_path,
                "*",
                "--flavor=woff2",
                "--output-file=%s" % woff2_path,
            ]
        )
        woff2 = TTFont(woff2_path)

        self.assertEqual(woff2.flavor, "woff2")

        ttf_path = self.temp_path(".ttf")
        subset.main(
            [
                woff2_path,
                "*",
                "--output-file=%s" % ttf_path,
            ]
        )
        ttf = TTFont(ttf_path)

        self.assertEqual(ttf.flavor, None)

    def test_subset_context_subst_format_3(self):
        # https://github.com/fonttools/fonttools/issues/1879
        # Test font contains 'calt' feature with Format 3 ContextSubst lookup subtables
        ttx = self.getpath("TestContextSubstFormat3.ttx")
        font, fontpath = self.compile_font(ttx, ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--unicodes=*", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        # check all glyphs are kept via GSUB closure, no changes expected
        self.expect_ttx(subsetfont, ttx)

    def test_cmap_prune_format12(self):
        _, fontpath = self.compile_font(self.getpath("CmapSubsetTest.ttx"), ".ttf")
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "--glyphs=a", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(subsetfont, self.getpath("CmapSubsetTest.subset.ttx"), ["cmap"])

    def test_GPOS_PairPos_Format2_useClass0(self):
        # Check two things related to class 0 ('every other glyph'):
        # 1) that it's reused for ClassDef1 when it becomes empty as the subset glyphset
        #    is intersected with the table's Coverage
        # 2) that it is never reused for ClassDef2 even when it happens to become empty
        #    because of the subset glyphset. In this case, we don't keep a PairPosClass2
        #    subtable if only ClassDef2's class0 survived subsetting.
        # The test font (from Harfbuzz test suite) is constructed to trigger these two
        # situations depending on the input subset --text.
        # https://github.com/fonttools/fonttools/pull/2221
        _, fontpath = self.compile_font(
            self.getpath("GPOS_PairPos_Format2_PR_2221.ttx"), ".ttf"
        )
        subsetpath = self.temp_path(".ttf")

        for n, text in enumerate("!#", start=1):
            expected_ttx = self.getpath(
                f"GPOS_PairPos_Format2_ClassDef{n}_useClass0.subset.ttx"
            )
            with self.subTest(text=text, expected_ttx=expected_ttx):
                subset.main(
                    [
                        fontpath,
                        f"--text='{text}'",
                        "--layout-features+=test",
                        "--output-file=%s" % subsetpath,
                    ]
                )
                subsetfont = TTFont(subsetpath)
                self.expect_ttx(subsetfont, expected_ttx, ["GPOS"])

    def test_GPOS_SinglePos_prune_post_subset_no_value(self):
        _, fontpath = self.compile_font(
            self.getpath("GPOS_SinglePos_no_value_issue_2312.ttx"), ".ttf"
        )
        subsetpath = self.temp_path(".ttf")
        subset.main([fontpath, "*", "--glyph-names", "--output-file=%s" % subsetpath])
        subsetfont = TTFont(subsetpath)
        self.expect_ttx(
            subsetfont,
            self.getpath("GPOS_SinglePos_no_value_issue_2312.subset.ttx"),
            ["GlyphOrder", "GPOS"],
        )


@pytest.fixture
def featureVarsTestFont():
    fb = FontBuilder(unitsPerEm=100)
    fb.setupGlyphOrder([".notdef", "f", "f_f", "dollar", "dollar.rvrn"])
    fb.setupCharacterMap({ord("f"): "f", ord("$"): "dollar"})
    fb.setupNameTable({"familyName": "TestFeatureVars", "styleName": "Regular"})
    fb.setupPost()
    fb.setupFvar(axes=[("wght", 100, 400, 900, "Weight")], instances=[])
    fb.addOpenTypeFeatures("""\
        feature dlig {
            sub f f by f_f;
        } dlig;
    """)
    fb.addFeatureVariations(
        [([{"wght": (0.20886, 1.0)}], {"dollar": "dollar.rvrn"})],
        featureTag="rvrn"
    )
    buf = io.BytesIO()
    fb.save(buf)
    buf.seek(0)

    return TTFont(buf)


def test_subset_feature_variations_keep_all(featureVarsTestFont):
    font = featureVarsTestFont

    options = subset.Options()
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord("f"), ord("$")])
    subsetter.subset(font)

    featureTags = {
        r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord
    }
    # 'dlig' is discretionary so it is dropped by default
    assert "dlig" not in featureTags
    assert "f_f" not in font.getGlyphOrder()
    # 'rvrn' is required so it is kept by default
    assert "rvrn" in featureTags
    assert "dollar.rvrn" in font.getGlyphOrder()


def test_subset_feature_variations_drop_all(featureVarsTestFont):
    font = featureVarsTestFont

    options = subset.Options()
    options.layout_features.remove("rvrn")  # drop 'rvrn'
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord("f"), ord("$")])
    subsetter.subset(font)

    featureTags = {
        r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord
    }
    glyphs = set(font.getGlyphOrder())

    assert "rvrn" not in featureTags
    assert glyphs == {".notdef", "f", "dollar"}
    # all FeatureVariationRecords were dropped
    assert font["GSUB"].table.FeatureVariations is None
    assert font["GSUB"].table.Version == 0x00010000


# TODO test_subset_feature_variations_drop_from_end_empty_records
# https://github.com/fonttools/fonttools/issues/1881#issuecomment-619415044


def test_subset_single_pos_format():
    fb = FontBuilder(unitsPerEm=1000)
    fb.setupGlyphOrder([".notdef", "a", "b", "c"])
    fb.setupCharacterMap({ord("a"): "a", ord("b"): "b", ord("c"): "c"})
    fb.setupNameTable({"familyName": "TestSingePosFormat", "styleName": "Regular"})
    fb.setupPost()
    fb.addOpenTypeFeatures("""
        feature kern {
            pos a -50;
            pos b -40;
            pos c -50;
        } kern;
    """)

    buf = io.BytesIO()
    fb.save(buf)
    buf.seek(0)

    font = TTFont(buf)

    # The input font has a SinglePos Format 2 subtable where each glyph has
    # different ValueRecords
    assert getXML(font["GPOS"].table.LookupList.Lookup[0].toXML, font) == [
        '<Lookup>',
        '  <LookupType value="1"/>',
        '  <LookupFlag value="0"/>',
        '  <!-- SubTableCount=1 -->',
        '  <SinglePos index="0" Format="2">',
        '    <Coverage>',
        '      <Glyph value="a"/>',
        '      <Glyph value="b"/>',
        '      <Glyph value="c"/>',
        '    </Coverage>',
        '    <ValueFormat value="4"/>',
        '    <!-- ValueCount=3 -->',
        '    <Value index="0" XAdvance="-50"/>',
        '    <Value index="1" XAdvance="-40"/>',
        '    <Value index="2" XAdvance="-50"/>',
        '  </SinglePos>',
        '</Lookup>',
    ]

    options = subset.Options()
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord("a"), ord("c")])
    subsetter.subset(font)

    # All the subsetted glyphs from the original SinglePos Format2 subtable
    # now have the same ValueRecord, so we use a more compact Format 1 subtable.
    assert getXML(font["GPOS"].table.LookupList.Lookup[0].toXML, font) == [
        '<Lookup>',
        '  <LookupType value="1"/>',
        '  <LookupFlag value="0"/>',
        '  <!-- SubTableCount=1 -->',
        '  <SinglePos index="0" Format="1">',
        '    <Coverage>',
        '      <Glyph value="a"/>',
        '      <Glyph value="c"/>',
        '    </Coverage>',
        '    <ValueFormat value="4"/>',
        '    <Value XAdvance="-50"/>',
        '  </SinglePos>',
        '</Lookup>',
    ]


@pytest.fixture
def ttf_path(tmp_path):
    # $(dirname $0)/../ttLib/data
    ttLib_data = pathlib.Path(__file__).parent.parent / "ttLib" / "data"
    font = TTFont()
    font.importXML(ttLib_data / "TestTTF-Regular.ttx")
    font_path = tmp_path / "TestTTF-Regular.ttf"
    font.save(font_path)
    return font_path


def test_subset_empty_glyf(tmp_path, ttf_path):
    subset_path = tmp_path / (ttf_path.name + ".subset")
    # only keep empty .notdef and space glyph, resulting in an empty glyf table
    subset.main(
        [
            str(ttf_path),
            "--no-notdef-outline",
            "--glyph-names",
            f"--output-file={subset_path}",
            "--glyphs=.notdef space",
        ]
    )
    subset_font = TTFont(subset_path)

    assert subset_font.getGlyphOrder() == [".notdef", "space"]
    assert subset_font.reader['glyf'] == b"\x00"

    glyf = subset_font["glyf"]
    assert all(glyf[g].numberOfContours == 0 for g in subset_font.getGlyphOrder())

    loca = subset_font["loca"]
    assert all(loc == 0 for loc in loca)


@pytest.fixture
def colrv1_path(tmp_path):
    base_glyph_names = ["uni%04X" % i for i in range(0xE000, 0xE000 + 10)]
    layer_glyph_names = ["glyph%05d" % i for i in range(10, 20)]
    glyph_order = [".notdef"] + base_glyph_names + layer_glyph_names

    pen = TTGlyphPen(glyphSet=None)
    pen.moveTo((0, 0))
    pen.lineTo((0, 500))
    pen.lineTo((500, 500))
    pen.lineTo((500, 0))
    pen.closePath()
    glyph = pen.glyph()
    glyphs = {g: glyph for g in glyph_order}

    fb = FontBuilder(unitsPerEm=1024, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({int(name[3:], 16): name for name in base_glyph_names})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({g: (500, 0) for g in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupOS2()
    fb.setupPost()
    fb.setupNameTable({"familyName": "TestCOLRv1", "styleName": "Regular"})

    fb.setupCOLR(
        {
            "uniE000": (
                ot.PaintFormat.PaintColrLayers,
                [
                    {
                        "Format": ot.PaintFormat.PaintGlyph,
                        "Paint": (ot.PaintFormat.PaintSolid, 0),
                        "Glyph": "glyph00010",
                    },
                    {
                        "Format": ot.PaintFormat.PaintGlyph,
                        "Paint": (ot.PaintFormat.PaintSolid, 2, 0.3),
                        "Glyph": "glyph00011",
                    },
                ],
            ),
            "uniE001": (
                ot.PaintFormat.PaintColrLayers,
                [
                    {
                        "Format": ot.PaintFormat.PaintTransform,
                        "Paint": {
                            "Format": ot.PaintFormat.PaintGlyph,
                            "Paint": {
                                "Format": ot.PaintFormat.PaintRadialGradient,
                                "x0": 250,
                                "y0": 250,
                                "r0": 250,
                                "x1": 200,
                                "y1": 200,
                                "r1": 0,
                                "ColorLine": {
                                    "ColorStop": [(0.0, 1), (1.0, 2)],
                                    "Extend": "repeat",
                                },
                            },
                            "Glyph": "glyph00012",
                        },
                        "Transform": (0.7071, 0.7071, -0.7071, 0.7071, 0, 0),
                    },
                    {
                        "Format": ot.PaintFormat.PaintGlyph,
                        "Paint": (ot.PaintFormat.PaintSolid, 1, 0.5),
                        "Glyph": "glyph00013",
                    },
                ],
            ),
            "uniE002": (
                ot.PaintFormat.PaintColrLayers,
                [
                    {
                        "Format": ot.PaintFormat.PaintGlyph,
                        "Paint": {
                            "Format": ot.PaintFormat.PaintLinearGradient,
                            "x0": 0,
                            "y0": 0,
                            "x1": 500,
                            "y1": 500,
                            "x2": -500,
                            "y2": 500,
                            "ColorLine": {"ColorStop": [(0.0, 1), (1.0, 2)]},
                        },
                        "Glyph": "glyph00014",
                    },
                    {
                        "Format": ot.PaintFormat.PaintTransform,
                        "Paint": {
                            "Format": ot.PaintFormat.PaintGlyph,
                            "Paint": (ot.PaintFormat.PaintSolid, 1),
                            "Glyph": "glyph00015",
                        },
                        "Transform": (1, 0, 0, 1, 400, 400),
                    },
                ],
            ),
            "uniE003": {
                "Format": ot.PaintFormat.PaintRotateAroundCenter,
                "Paint": {
                    "Format": ot.PaintFormat.PaintColrGlyph,
                    "Glyph": "uniE001",
                },
                "angle": 45,
                "centerX": 250,
                "centerY": 250,
            },
            "uniE004": [
                ("glyph00016", 1),
                ("glyph00017", 0xFFFF),  # special palette index for foreground text
                ("glyph00018", 2),
            ],
        },
    )
    fb.setupCPAL(
        [
            [
                (1.0, 0.0, 0.0, 1.0),  # red
                (0.0, 1.0, 0.0, 1.0),  # green
                (0.0, 0.0, 1.0, 1.0),  # blue
            ],
        ],
    )

    output_path = tmp_path / "TestCOLRv1.ttf"
    fb.save(output_path)

    return output_path


def test_subset_COLRv1_and_CPAL(colrv1_path):
    subset_path = colrv1_path.parent / (colrv1_path.name + ".subset")

    subset.main(
        [
            str(colrv1_path),
            "--glyph-names",
            f"--output-file={subset_path}",
            "--unicodes=E002,E003,E004",
        ]
    )
    subset_font = TTFont(subset_path)

    glyph_set = set(subset_font.getGlyphOrder())

    # uniE000 and its children are excluded from subset
    assert "uniE000" not in glyph_set
    assert "glyph00010" not in glyph_set
    assert "glyph00011" not in glyph_set

    # uniE001 and children are pulled in indirectly as PaintColrGlyph by uniE003
    assert "uniE001" in glyph_set
    assert "glyph00012" in glyph_set
    assert "glyph00013" in glyph_set

    assert "uniE002" in glyph_set
    assert "glyph00014" in glyph_set
    assert "glyph00015" in glyph_set

    assert "uniE003" in glyph_set

    assert "uniE004" in glyph_set
    assert "glyph00016" in glyph_set
    assert "glyph00017" in glyph_set
    assert "glyph00018" in glyph_set

    assert "COLR" in subset_font
    colr = subset_font["COLR"].table
    assert colr.Version == 1
    assert len(colr.BaseGlyphRecordArray.BaseGlyphRecord) == 1
    assert len(colr.BaseGlyphList.BaseGlyphPaintRecord) == 3  # was 4

    base = colr.BaseGlyphList.BaseGlyphPaintRecord[0]
    assert base.BaseGlyph == "uniE001"
    layers = colr.LayerList.Paint[
        base.Paint.FirstLayerIndex: base.Paint.FirstLayerIndex + base.Paint.NumLayers
    ]
    assert len(layers) == 2
    # check v1 palette indices were remapped
    assert layers[0].Paint.Paint.ColorLine.ColorStop[0].PaletteIndex == 0
    assert layers[0].Paint.Paint.ColorLine.ColorStop[1].PaletteIndex == 1
    assert layers[1].Paint.PaletteIndex == 0

    baseRecV0 = colr.BaseGlyphRecordArray.BaseGlyphRecord[0]
    assert baseRecV0.BaseGlyph == "uniE004"
    layersV0 = colr.LayerRecordArray.LayerRecord
    assert len(layersV0) == 3
    # check v0 palette indices were remapped (except for 0xFFFF)
    assert layersV0[0].PaletteIndex == 0
    assert layersV0[1].PaletteIndex == 0xFFFF
    assert layersV0[2].PaletteIndex == 1

    assert "CPAL" in subset_font
    cpal = subset_font["CPAL"]
    assert [
        tuple(v / 255 for v in (c.red, c.green, c.blue, c.alpha))
        for c in cpal.palettes[0]
    ] == [
        # the first color 'red' was pruned
        (0.0, 1.0, 0.0, 1.0),  # green
        (0.0, 0.0, 1.0, 1.0),  # blue
    ]


def test_subset_COLRv1_and_CPAL_drop_empty(colrv1_path):
    subset_path = colrv1_path.parent / (colrv1_path.name + ".subset")

    subset.main(
        [
            str(colrv1_path),
            "--glyph-names",
            f"--output-file={subset_path}",
            "--glyphs=glyph00010",
        ]
    )
    subset_font = TTFont(subset_path)

    glyph_set = set(subset_font.getGlyphOrder())

    assert "glyph00010" in glyph_set
    assert "uniE000" not in glyph_set

    assert "COLR" not in subset_font
    assert "CPAL" not in subset_font


def test_subset_COLRv1_downgrade_version(colrv1_path):
    subset_path = colrv1_path.parent / (colrv1_path.name + ".subset")

    subset.main(
        [
            str(colrv1_path),
            "--glyph-names",
            f"--output-file={subset_path}",
            "--unicodes=E004",
        ]
    )
    subset_font = TTFont(subset_path)

    assert set(subset_font.getGlyphOrder()) == {
        ".notdef",
        "uniE004",
        "glyph00016",
        "glyph00017",
        "glyph00018",
    }

    assert "COLR" in subset_font
    assert subset_font["COLR"].version == 0


def test_subset_COLRv1_drop_all_v0_glyphs(colrv1_path):
    subset_path = colrv1_path.parent / (colrv1_path.name + ".subset")

    subset.main(
        [
            str(colrv1_path),
            "--glyph-names",
            f"--output-file={subset_path}",
            "--unicodes=E003",
        ]
    )
    subset_font = TTFont(subset_path)

    assert set(subset_font.getGlyphOrder()) == {
        ".notdef",
        "uniE001",
        "uniE003",
        "glyph00012",
        "glyph00013",
    }

    assert "COLR" in subset_font
    colr = subset_font["COLR"]
    assert colr.version == 1
    assert colr.table.BaseGlyphRecordCount == 0
    assert colr.table.BaseGlyphRecordArray is None
    assert colr.table.LayerRecordArray is None
    assert colr.table.LayerRecordCount is 0


def test_subset_keep_size_drop_empty_stylistic_set():
    fb = FontBuilder(unitsPerEm=1000, isTTF=True)
    glyph_order = [".notdef", "a", "b", "b.ss01"]
    fb.setupGlyphOrder(glyph_order)
    fb.setupGlyf({g: TTGlyphPen(None).glyph() for g in glyph_order})
    fb.setupCharacterMap({ord("a"): "a", ord("b"): "b"})
    fb.setupHorizontalMetrics({g: (500, 0) for g in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupOS2()
    fb.setupPost()
    fb.setupNameTable({"familyName": "TestKeepSizeFeature", "styleName": "Regular"})
    fb.addOpenTypeFeatures("""
        feature size {
          parameters 10.0 0;
        } size;
        feature ss01 {
          featureNames {
            name "Alternate b";
          };
          sub b by b.ss01;
        } ss01;
    """)

    buf = io.BytesIO()
    fb.save(buf)
    buf.seek(0)

    font = TTFont(buf)

    gpos_features = font["GPOS"].table.FeatureList.FeatureRecord
    assert gpos_features[0].FeatureTag == "size"
    assert isinstance(gpos_features[0].Feature.FeatureParams, ot.FeatureParamsSize)
    assert gpos_features[0].Feature.LookupCount == 0
    gsub_features = font["GSUB"].table.FeatureList.FeatureRecord
    assert gsub_features[0].FeatureTag == "ss01"
    assert isinstance(
        gsub_features[0].Feature.FeatureParams, ot.FeatureParamsStylisticSet
    )

    options = subset.Options(layout_features=["*"])
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord("a")])
    subsetter.subset(font)

    # empty size feature was kept
    gpos_features = font["GPOS"].table.FeatureList.FeatureRecord
    assert gpos_features[0].FeatureTag == "size"
    assert isinstance(gpos_features[0].Feature.FeatureParams, ot.FeatureParamsSize)
    assert gpos_features[0].Feature.LookupCount == 0
    # empty ss01 feature was dropped
    assert font["GSUB"].table.FeatureList.FeatureCount == 0


if __name__ == "__main__":
    sys.exit(unittest.main())
