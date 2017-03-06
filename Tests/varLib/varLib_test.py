from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import build
from fontTools.varLib import main as varLib_main
import difflib
import os
import shutil
import sys
import tempfile
import unittest


class BuildTest(unittest.TestCase):
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
    def get_test_input(test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", test_file_or_folder)

    @staticmethod
    def get_test_output(test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", "test_results", test_file_or_folder)

    @staticmethod
    def get_file_list(folder, suffix, prefix=''):
        all_files = os.listdir(folder)
        file_list = []
        for p in all_files:
            if p.startswith(prefix) and p.endswith(suffix):
                file_list.append(os.path.abspath(os.path.join(folder, p)))
        return file_list

    def temp_path(self, suffix):
        self.temp_dir()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir,
                            "tmp%d%s" % (self.num_tempfiles, suffix))

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

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

    def check_ttx_dump(self, font, expected_ttx, tables, suffix):
        """Ensure the TTX dump is the same after saving and reloading the font."""
        path = self.temp_path(suffix=suffix)
        font.save(path)
        self.expect_ttx(TTFont(path), expected_ttx, tables)

    def compile_font(self, path, suffix, temp_dir):
        ttx_filename = os.path.basename(path)
        savepath = os.path.join(temp_dir, ttx_filename.replace('.ttx', suffix))
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

# -----
# Tests
# -----

    def test_varlib_build_ttf(self):
        """Designspace file contains <axes> element.
        build() is called without an axisMap parameter.
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('Build.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        varfont, model, _ = build(ds_path, finder)

        tables = ['GDEF', 'HVAR', 'fvar', 'gvar']
        expected_ttx_path = self.get_test_output('Build.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)


    def test_varlib_build2_ttf(self):
        """Designspace file does not contain an <axes> element.
        build() is called with an axisMap parameter.
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('Build2.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        axisMap = {'contrast': ('cntr', 'Contrast')}
        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        varfont, model, _ = build(ds_path, finder, axisMap)

        tables = ['GDEF', 'HVAR', 'fvar', 'gvar']
        expected_ttx_path = self.get_test_output('Build.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)


    def test_varlib_build3_ttf(self):
        """Designspace file does not contain an <axes> element.
        build() is called without an axisMap parameter.
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('InterpolateLayout3.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily2-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        varfont, model, _ = build(ds_path, finder)

        tables = ['GDEF', 'HVAR', 'fvar', 'gvar']
        expected_ttx_path = self.get_test_output('Build3.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)


    def test_varlib_main_ttf(self):
        """Mostly for testing varLib.main()
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('Build.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttf_dir = os.path.join(self.tempdir, 'master_ttf_interpolatable')
        os.makedirs(ttf_dir)
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily-')
        for path in ttx_paths:
            self.compile_font(path, suffix, ttf_dir)

        ds_copy = os.path.join(self.tempdir, 'BuildMain.designspace')
        shutil.copy2(ds_path, ds_copy)
        varLib_main([ds_copy])

        varfont_path = os.path.splitext(ds_copy)[0] + '-VF' + suffix
        varfont = TTFont(varfont_path)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != 'head']
        expected_ttx_path = self.get_test_output('BuildMain.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)


if __name__ == "__main__":
    sys.exit(unittest.main())
