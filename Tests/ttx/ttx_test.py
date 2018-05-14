from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.timeTools import timestampSinceEpoch
from fontTools.ttLib import TTFont, TTLibError
from fontTools import ttx
import getopt
import logging
import os
import shutil
import tempfile
import unittest

import pytest

class TTXTest(unittest.TestCase):
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

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

    def temp_font(self, font_path, file_name):
        self.temp_dir()
        temppath = os.path.join(self.tempdir, file_name)
        shutil.copy2(font_path, temppath)
        return temppath

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.readlines()

# -----
# Tests
# -----

    def test_parseOptions_no_args(self):
        with self.assertRaises(getopt.GetoptError) as cm:
            ttx.parseOptions([])
        self.assertTrue('Must specify at least one input file' in str(cm.exception))

    def test_parseOptions_invalid_path(self):
        file_path = 'invalid_font_path'
        with self.assertRaises(getopt.GetoptError) as cm:
            ttx.parseOptions([file_path])
        self.assertTrue('File not found: "%s"' % file_path in str(cm.exception))

    def test_parseOptions_font2ttx_1st_time(self):
        file_name = 'TestOTF.otf'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        jobs, _ = ttx.parseOptions([temp_path])
        self.assertEqual(jobs[0][0].__name__, 'ttDump')
        self.assertEqual(jobs[0][1:],
                        (os.path.join(self.tempdir, file_name),
                         os.path.join(self.tempdir, file_name.split('.')[0] + '.ttx')))

    def test_parseOptions_font2ttx_2nd_time(self):
        file_name = 'TestTTF.ttf'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        _, _ = ttx.parseOptions([temp_path]) # this is NOT a mistake
        jobs, _ = ttx.parseOptions([temp_path])
        self.assertEqual(jobs[0][0].__name__, 'ttDump')
        self.assertEqual(jobs[0][1:],
                        (os.path.join(self.tempdir, file_name),
                         os.path.join(self.tempdir, file_name.split('.')[0] + '#1.ttx')))

    def test_parseOptions_ttx2font_1st_time(self):
        file_name = 'TestTTF.ttx'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        jobs, _ = ttx.parseOptions([temp_path])
        self.assertEqual(jobs[0][0].__name__, 'ttCompile')
        self.assertEqual(jobs[0][1:],
                        (os.path.join(self.tempdir, file_name),
                         os.path.join(self.tempdir, file_name.split('.')[0] + '.ttf')))

    def test_parseOptions_ttx2font_2nd_time(self):
        file_name = 'TestOTF.ttx'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        _, _ = ttx.parseOptions([temp_path]) # this is NOT a mistake
        jobs, _ = ttx.parseOptions([temp_path])
        self.assertEqual(jobs[0][0].__name__, 'ttCompile')
        self.assertEqual(jobs[0][1:],
                        (os.path.join(self.tempdir, file_name),
                         os.path.join(self.tempdir, file_name.split('.')[0] + '#1.otf')))

    def test_parseOptions_multiple_fonts(self):
        file_names = ['TestOTF.otf', 'TestTTF.ttf']
        font_paths = [self.getpath(file_name) for file_name in file_names]
        temp_paths = [self.temp_font(font_path, file_name) \
                      for font_path, file_name in zip(font_paths, file_names)]
        jobs, _ = ttx.parseOptions(temp_paths)
        for i in range(len(jobs)):
            self.assertEqual(jobs[i][0].__name__, 'ttDump')
            self.assertEqual(jobs[i][1:],
                    (os.path.join(self.tempdir, file_names[i]),
                     os.path.join(self.tempdir, file_names[i].split('.')[0] + '.ttx')))

    def test_parseOptions_mixed_files(self):
        operations = ['ttDump', 'ttCompile']
        extensions = ['.ttx', '.ttf']
        file_names = ['TestOTF.otf', 'TestTTF.ttx']
        font_paths = [self.getpath(file_name) for file_name in file_names]
        temp_paths = [self.temp_font(font_path, file_name) \
                      for font_path, file_name in zip(font_paths, file_names)]
        jobs, _ = ttx.parseOptions(temp_paths)
        for i in range(len(jobs)):
            self.assertEqual(jobs[i][0].__name__, operations[i])
            self.assertEqual(jobs[i][1:],
                (os.path.join(self.tempdir, file_names[i]),
                 os.path.join(self.tempdir, file_names[i].split('.')[0] + extensions[i])))

    def test_parseOptions_splitTables(self):
        file_name = 'TestTTF.ttf'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        args = ['-s', temp_path]

        jobs, options = ttx.parseOptions(args)

        ttx_file_path = jobs[0][2]
        temp_folder = os.path.dirname(ttx_file_path)
        self.assertTrue(options.splitTables)
        self.assertTrue(os.path.exists(ttx_file_path))

        ttx.process(jobs, options)

        # Read the TTX file but strip the first two and the last lines:
        # <?xml version="1.0" encoding="UTF-8"?>
        # <ttFont sfntVersion="\x00\x01\x00\x00" ttLibVersion="3.22">
        # ...
        # </ttFont>
        parsed_xml = parseXML(self.read_file(ttx_file_path)[2:-1])
        for item in parsed_xml:
            if not isinstance(item, tuple):
                continue
            # the tuple looks like this:
            # (u'head', {u'src': u'TestTTF._h_e_a_d.ttx'}, [])
            table_file_name = item[1].get('src')
            table_file_path = os.path.join(temp_folder, table_file_name)
            self.assertTrue(os.path.exists(table_file_path))

    def test_parseOptions_splitGlyphs(self):
        file_name = 'TestTTF.ttf'
        font_path = self.getpath(file_name)
        temp_path = self.temp_font(font_path, file_name)
        args = ['-g', temp_path]

        jobs, options = ttx.parseOptions(args)

        ttx_file_path = jobs[0][2]
        temp_folder = os.path.dirname(ttx_file_path)
        self.assertTrue(options.splitGlyphs)
        # splitGlyphs also forces splitTables
        self.assertTrue(options.splitTables)
        self.assertTrue(os.path.exists(ttx_file_path))

        ttx.process(jobs, options)

        # Read the TTX file but strip the first two and the last lines:
        # <?xml version="1.0" encoding="UTF-8"?>
        # <ttFont sfntVersion="\x00\x01\x00\x00" ttLibVersion="3.22">
        # ...
        # </ttFont>
        for item in parseXML(self.read_file(ttx_file_path)[2:-1]):
            if not isinstance(item, tuple):
                continue
            # the tuple looks like this:
            # (u'head', {u'src': u'TestTTF._h_e_a_d.ttx'}, [])
            table_tag = item[0]
            table_file_name = item[1].get('src')
            table_file_path = os.path.join(temp_folder, table_file_name)
            self.assertTrue(os.path.exists(table_file_path))
            if table_tag != "glyf":
                continue
            # also strip the enclosing 'glyf' element
            for item in parseXML(self.read_file(table_file_path)[4:-3]):
                if not isinstance(item, tuple):
                    continue
                # glyphs without outline data only have 'name' attribute
                glyph_file_name = item[1].get('src')
                if glyph_file_name is not None:
                    glyph_file_path = os.path.join(temp_folder,
                                                   glyph_file_name)
                    self.assertTrue(os.path.exists(glyph_file_path))

    def test_guessFileType_ttf(self):
        file_name = 'TestTTF.ttf'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTF')

    def test_guessFileType_otf(self):
        file_name = 'TestOTF.otf'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'OTF')

    def test_guessFileType_woff(self):
        file_name = 'TestWOFF.woff'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'WOFF')

    def test_guessFileType_woff2(self):
        file_name = 'TestWOFF2.woff2'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'WOFF2')

    def test_guessFileType_ttc(self):
        file_name = 'TestTTC.ttc'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTC')

    def test_guessFileType_dfont(self):
        file_name = 'TestDFONT.dfont'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTF')

    def test_guessFileType_ttx_ttf(self):
        file_name = 'TestTTF.ttx'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTX')

    def test_guessFileType_ttx_otf(self):
        file_name = 'TestOTF.ttx'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'OTX')

    def test_guessFileType_ttx_bom(self):
        file_name = 'TestBOM.ttx'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTX')

    def test_guessFileType_ttx_no_sfntVersion(self):
        file_name = 'TestNoSFNT.ttx'
        font_path = self.getpath(file_name)
        self.assertEqual(ttx.guessFileType(font_path), 'TTX')

    def test_guessFileType_ttx_no_xml(self):
        file_name = 'TestNoXML.ttx'
        font_path = self.getpath(file_name)
        self.assertIsNone(ttx.guessFileType(font_path))

    def test_guessFileType_invalid_path(self):
        font_path = 'invalid_font_path'
        self.assertIsNone(ttx.guessFileType(font_path))


# -----------------------
# ttx.Options class tests
# -----------------------


def test_ttx_options_class_defaults():
    tto = ttx.Options([(None, None)], 1)
    assert tto.listTables is False
    assert tto.outputDir is None
    assert tto.outputFile is None
    assert tto.overWrite is False
    assert tto.verbose is False
    assert tto.quiet is False
    assert tto.splitTables is False
    assert tto.splitGlyphs is False
    assert tto.disassembleInstructions is True
    assert tto.mergeFile is None
    assert tto.recalcBBoxes is True
    assert tto.allowVID is False
    assert tto.ignoreDecompileErrors is True
    assert tto.bitmapGlyphDataFormat == "raw"
    assert tto.unicodedata is None
    assert tto.newlinestr is None
    assert tto.recalcTimestamp is False
    assert tto.flavor is None
    assert tto.useZopfli is False
    assert tto.onlyTables == []
    assert tto.skipTables == []
    assert tto.fontNumber == -1
    assert tto.logLevel == logging.INFO


def test_ttx_options_class_flag_h(capsys):
    with pytest.raises(SystemExit):
        ttx.Options([("-h", None)], 1)

    out, err = capsys.readouterr()
    assert "TTX -- From OpenType To XML And Back" in out


def test_ttx_options_class_flag_version(capsys):
    with pytest.raises(SystemExit):
        ttx.Options([("--version", None)], 1)

    out, err = capsys.readouterr()
    version_list = out.split(".")
    assert len(version_list) >= 3
    assert version_list[0].isdigit()
    assert version_list[1].isdigit()
    assert version_list[2].isdigit()


def test_ttx_options_class_flag_d_goodpath(tmpdir):
    temp_dir_path = str(tmpdir)
    tto = ttx.Options([("-d", temp_dir_path)], 1)
    assert tto.outputDir == temp_dir_path


def test_ttx_options_class_flag_d_badpath():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-d", "bogusdir")], 1)


def test_ttx_options_class_flag_o():
    tto = ttx.Options([("-o", "testfile.ttx")], 1)
    assert tto.outputFile == "testfile.ttx"


def test_ttx_options_class_flag_f():
    tto = ttx.Options([("-f", "")], 1)
    assert tto.overWrite is True


def test_ttx_options_class_flag_v():
    tto = ttx.Options([("-v", "")], 1)
    assert tto.verbose is True
    assert tto.logLevel == logging.DEBUG


def test_ttx_options_class_flag_q():
    tto = ttx.Options([("-q", "")], 1)
    assert tto.quiet is True
    assert tto.logLevel == logging.WARNING


def test_ttx_options_class_flag_l():
    tto = ttx.Options([("-l", "")], 1)
    assert tto.listTables is True


def test_ttx_options_class_flag_t_nopadding():
    tto = ttx.Options([("-t", "CFF2")], 1)
    assert len(tto.onlyTables) == 1
    assert tto.onlyTables[0] == "CFF2"


def test_ttx_options_class_flag_t_withpadding():
    tto = ttx.Options([("-t", "CFF")], 1)
    assert len(tto.onlyTables) == 1
    assert tto.onlyTables[0] == "CFF "


def test_ttx_options_class_flag_s():
    tto = ttx.Options([("-s", "")], 1)
    assert tto.splitTables is True
    assert tto.splitGlyphs is False


def test_ttx_options_class_flag_g():
    tto = ttx.Options([("-g", "")], 1)
    assert tto.splitGlyphs is True
    assert tto.splitTables is True


def test_ttx_options_class_flag_i():
    tto = ttx.Options([("-i", "")], 1)
    assert tto.disassembleInstructions is False


def test_ttx_options_class_flag_z_validoptions():
    valid_options = ('raw', 'row', 'bitwise', 'extfile')
    for option in valid_options:
        tto = ttx.Options([("-z", option)], 1)
        assert tto.bitmapGlyphDataFormat == option


def test_ttx_options_class_flag_z_invalidoption():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-z", "bogus")], 1)


def test_ttx_options_class_flag_y_validvalue():
    tto = ttx.Options([("-y", "1")], 1)
    assert tto.fontNumber == 1


# TODO: fix this with a check in the ttx module: str.isdigit()
def test_ttx_options_class_flag_y_invalidvalue():
    with pytest.raises(ValueError):
        ttx.Options([("-y", "A")], 1)


def test_ttx_options_class_flag_m():
    tto = ttx.Options([("-m", "testfont.ttf")], 1)
    assert tto.mergeFile == "testfont.ttf"


def test_ttx_options_class_flag_b():
    tto = ttx.Options([("-b", "")], 1)
    assert tto.recalcBBoxes is False


def test_ttx_options_class_flag_a():
    tto = ttx.Options([("-a", "")], 1)
    assert tto.allowVID is True


def test_ttx_options_class_flag_e():
    tto = ttx.Options([("-e", "")], 1)
    assert tto.ignoreDecompileErrors is False


def test_ttx_options_class_flag_unicodedata():
    tto = ttx.Options([("--unicodedata", "UnicodeData.txt")], 1)
    assert tto.unicodedata == "UnicodeData.txt"


def test_ttx_options_class_flag_newline_lf():
    tto = ttx.Options([("--newline", "LF")], 1)
    assert tto.newlinestr == "\n"


def test_ttx_options_class_flag_newline_cr():
    tto = ttx.Options([("--newline", "CR")], 1)
    assert tto.newlinestr == "\r"


def test_ttx_options_class_flag_newline_crlf():
    tto = ttx.Options([("--newline", "CRLF")], 1)
    assert tto.newlinestr == "\r\n"


def test_ttx_options_class_flag_newline_invalid():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("--newline", "BOGUS")], 1)


def test_ttx_options_class_flag_recalc_timestamp():
    tto = ttx.Options([("--recalc-timestamp", "")], 1)
    assert tto.recalcTimestamp is True


def test_ttx_options_class_flag_flavor():
    tto = ttx.Options([("--flavor", "woff")], 1)
    assert tto.flavor == "woff"


def test_ttx_options_class_flag_with_zopfli():
    tto = ttx.Options([("--with-zopfli", ""), ("--flavor", "woff")], 1)
    assert tto.useZopfli is True


def test_ttx_options_class_flag_with_zopfli_fails_without_woff_flavor():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("--with-zopfli", "")], 1)


def test_ttx_options_class_flag_quiet_and_verbose_shouldfail():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-q", ""), ("-v", "")], 1)


def test_ttx_options_class_flag_mergefile_and_flavor_shouldfail():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-m", "testfont.ttf"), ("--flavor", "woff")], 1)


def test_ttx_options_class_flag_onlytables_and_skiptables_shouldfail():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-t", "CFF"), ("-x", "CFF2")], 1)


def test_ttx_options_class_flag_mergefile_and_multiplefiles_shouldfail():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("-m", "testfont.ttf")], 2)


def test_ttx_options_class_flag_woff2_and_zopfli_shouldfail():
    with pytest.raises(getopt.GetoptError):
        ttx.Options([("--with-zopfli", ""), ("--flavor", "woff2")], 1)

# ----------------------------
# ttx.ttCompile function tests
# ----------------------------


def test_ttx_ttcompile_otf_compile_default(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestOTF.ttx")
    outotf = os.path.join(str(tmpdir), "TestOTF.otf")
    default_options = ttx.Options([("", "")], 1)
    ttx.ttCompile(inttx, outotf, default_options)
    # confirm that font was built
    assert os.path.isfile(outotf) is True
    # confirm that it is valid OTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outotf)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_otf_to_woff_without_zopfli(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestOTF.ttx")
    outwoff = os.path.join(str(tmpdir), "TestOTF.woff")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff"
    ttx.ttCompile(inttx, outwoff, options)
    # confirm that font was built
    assert os.path.isfile(outwoff) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_otf_to_woff_with_zopfli(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestOTF.ttx")
    outwoff = os.path.join(str(tmpdir), "TestOTF.woff")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff"
    options.useZopfli = True
    ttx.ttCompile(inttx, outwoff, options)
    # confirm that font was built
    assert os.path.isfile(outwoff) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_otf_to_woff2(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestOTF.ttx")
    outwoff2 = os.path.join(str(tmpdir), "TestTTF.woff2")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff2"
    ttx.ttCompile(inttx, outwoff2, options)
    # confirm that font was built
    assert os.path.isfile(outwoff2) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff2)
    # DSIG should not be included from original ttx as per woff2 spec (https://dev.w3.org/webfonts/WOFF2/spec/)
    assert "DSIG" not in ttf
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_ttf_compile_default(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outttf = os.path.join(str(tmpdir), "TestTTF.ttf")
    default_options = ttx.Options([("", "")], 1)
    ttx.ttCompile(inttx, outttf, default_options)
    # confirm that font was built
    assert os.path.isfile(outttf) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outttf)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_ttf_to_woff_without_zopfli(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outwoff = os.path.join(str(tmpdir), "TestTTF.woff")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff"
    ttx.ttCompile(inttx, outwoff, options)
    # confirm that font was built
    assert os.path.isfile(outwoff) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_ttf_to_woff_with_zopfli(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outwoff = os.path.join(str(tmpdir), "TestTTF.woff")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff"
    options.useZopfli = True
    ttx.ttCompile(inttx, outwoff, options)
    # confirm that font was built
    assert os.path.isfile(outwoff) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff)
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp", "DSIG")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_ttf_to_woff2(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outwoff2 = os.path.join(str(tmpdir), "TestTTF.woff2")
    options = ttx.Options([("", "")], 1)
    options.flavor = "woff2"
    ttx.ttCompile(inttx, outwoff2, options)
    # confirm that font was built
    assert os.path.isfile(outwoff2) is True
    # confirm that it is valid TTF file, can instantiate a TTFont, has expected OpenType tables
    ttf = TTFont(outwoff2)
    # DSIG should not be included from original ttx as per woff2 spec (https://dev.w3.org/webfonts/WOFF2/spec/)
    assert "DSIG" not in ttf
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp")
    for table in expected_tables:
        assert table in ttf


def test_ttx_ttcompile_ttf_timestamp_calcs(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outttf1 = os.path.join(str(tmpdir), "TestTTF1.ttf")
    outttf2 = os.path.join(str(tmpdir), "TestTTF2.ttf")
    options = ttx.Options([("", "")], 1)
    # build with default options = do not recalculate timestamp
    ttx.ttCompile(inttx, outttf1, options)
    # confirm that font was built
    assert os.path.isfile(outttf1) is True
    # confirm that timestamp is same as modified time on ttx file
    mtime = os.path.getmtime(inttx)
    epochtime = timestampSinceEpoch(mtime)
    ttf = TTFont(outttf1)
    assert ttf['head'].modified == epochtime

    # reset options to recalculate the timestamp and compile new font
    options.recalcTimestamp = True
    ttx.ttCompile(inttx, outttf2, options)
    # confirm that font was built
    assert os.path.isfile(outttf2) is True
    # confirm that timestamp is more recent than modified time on ttx file
    mtime = os.path.getmtime(inttx)
    epochtime = timestampSinceEpoch(mtime)
    ttf = TTFont(outttf2)
    assert ttf['head'].modified > epochtime


def test_ttx_ttcompile_otf_timestamp_calcs(tmpdir):
    inttx = os.path.join("Tests", "ttx", "data", "TestOTF.ttx")
    outotf1 = os.path.join(str(tmpdir), "TestOTF1.ttf")
    outotf2 = os.path.join(str(tmpdir), "TestOTF2.ttf")
    options = ttx.Options([("", "")], 1)
    # build with default options = do not recalculate timestamp
    ttx.ttCompile(inttx, outotf1, options)
    # confirm that font was built
    assert os.path.isfile(outotf1) is True
    # confirm that timestamp is same as modified time on ttx file
    mtime = os.path.getmtime(inttx)
    epochtime = timestampSinceEpoch(mtime)
    ttf = TTFont(outotf1)
    assert ttf['head'].modified == epochtime

    # reset options to recalculate the timestamp and compile new font
    options.recalcTimestamp = True
    ttx.ttCompile(inttx, outotf2, options)
    # confirm that font was built
    assert os.path.isfile(outotf2) is True
    # confirm that timestamp is more recent than modified time on ttx file
    mtime = os.path.getmtime(inttx)
    epochtime = timestampSinceEpoch(mtime)
    ttf = TTFont(outotf2)
    assert ttf['head'].modified > epochtime


# -------------------------
# ttx.ttList function tests
# -------------------------

def test_ttx_ttlist_ttf(capsys, tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttf")
    fakeoutpath = os.path.join(str(tmpdir), "TestTTF.ttx")
    options = ttx.Options([("", "")], 1)
    options.listTables = True
    ttx.ttList(inpath, fakeoutpath, options)
    out, err = capsys.readouterr()
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp", "DSIG")
    # confirm that expected tables are printed to stdout
    for table in expected_tables:
        assert table in out
    # test for one of the expected tag/checksum/length/offset strings
    assert "OS/2  0x67230FF8        96       376" in out


def test_ttx_ttlist_otf(capsys, tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestOTF.Otf")
    fakeoutpath = os.path.join(str(tmpdir), "TestOTF.ttx")
    options = ttx.Options([("", "")], 1)
    options.listTables = True
    ttx.ttList(inpath, fakeoutpath, options)
    out, err = capsys.readouterr()
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG")
    # confirm that expected tables are printed to stdout
    for table in expected_tables:
        assert table in out
    # test for one of the expected tag/checksum/length/offset strings
    assert "OS/2  0x67230FF8        96       272" in out


def test_ttx_ttlist_woff(capsys, tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestWOFF.woff")
    fakeoutpath = os.path.join(str(tmpdir), "TestWOFF.ttx")
    options = ttx.Options([("", "")], 1)
    options.listTables = True
    options.flavor = "woff"
    ttx.ttList(inpath, fakeoutpath, options)
    out, err = capsys.readouterr()
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG")
    # confirm that expected tables are printed to stdout
    for table in expected_tables:
        assert table in out
    # test for one of the expected tag/checksum/length/offset strings
    assert "OS/2  0x67230FF8        84       340" in out


def test_ttx_ttlist_woff2(capsys, tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestWOFF2.woff2")
    fakeoutpath = os.path.join(str(tmpdir), "TestWOFF2.ttx")
    options = ttx.Options([("", "")], 1)
    options.listTables = True
    options.flavor = "woff2"
    ttx.ttList(inpath, fakeoutpath, options)
    out, err = capsys.readouterr()
    expected_tables = ("head", "hhea", "maxp", "OS/2", "name", "cmap", "hmtx", "fpgm", "prep", "cvt ", "loca", "glyf", "post", "gasp")
    # confirm that expected tables are printed to stdout
    for table in expected_tables:
        assert table in out
    # test for one of the expected tag/checksum/length/offset strings
    assert "OS/2  0x67230FF8        96         0" in out

# -------------------
# main function tests
# -------------------


def test_ttx_main_default_ttf_dump_to_ttx(tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttf")
    outpath = os.path.join(str(tmpdir), "TestTTF.ttx")
    args = ["-o", outpath, inpath]
    ttx.main(args)
    assert os.path.isfile(outpath)


def test_ttx_main_default_ttx_compile_to_ttf(tmpdir):
    inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
    outpath = os.path.join(str(tmpdir), "TestTTF.ttf")
    args = ["-o", outpath, inpath]
    ttx.main(args)
    assert os.path.isfile(outpath)


def test_ttx_main_getopterror_missing_directory():
    with pytest.raises(SystemExit):
        with pytest.raises(getopt.GetoptError):
            inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttf")
            args = ["-d", "bogusdir", inpath]
            ttx.main(args)


def test_ttx_main_keyboard_interrupt(tmpdir, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
        outpath = os.path.join(str(tmpdir), "TestTTF.ttf")
        args = ["-o", outpath, inpath]
        monkeypatch.setattr(ttx, 'process', (lambda x, y: raise_exception(KeyboardInterrupt)))
        ttx.main(args)

    out, err = capsys.readouterr()
    assert "(Cancelled.)" in err


def test_ttx_main_system_exit(tmpdir, monkeypatch):
    with pytest.raises(SystemExit):
        inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
        outpath = os.path.join(str(tmpdir), "TestTTF.ttf")
        args = ["-o", outpath, inpath]
        monkeypatch.setattr(ttx, 'process', (lambda x, y: raise_exception(SystemExit)))
        ttx.main(args)


def test_ttx_main_ttlib_error(tmpdir, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
        outpath = os.path.join(str(tmpdir), "TestTTF.ttf")
        args = ["-o", outpath, inpath]
        monkeypatch.setattr(ttx, 'process', (lambda x, y: raise_exception(TTLibError("Test error"))))
        ttx.main(args)

    out, err = capsys.readouterr()
    assert "Test error" in err


def test_ttx_main_base_exception(tmpdir, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        inpath = os.path.join("Tests", "ttx", "data", "TestTTF.ttx")
        outpath = os.path.join(str(tmpdir), "TestTTF.ttf")
        args = ["-o", outpath, inpath]
        monkeypatch.setattr(ttx, 'process', (lambda x, y: raise_exception(Exception("Test error"))))
        ttx.main(args)

    out, err = capsys.readouterr()
    assert "Unhandled exception has occurred" in err

# ---------------------------
# support functions for tests
# ---------------------------


def raise_exception(exception):
    raise exception



