from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import build
from fontTools.varLib.interpolate_layout import interpolate_layout
from fontTools.varLib.interpolate_layout import main as interpolate_layout_main
import difflib
import os
import shutil
import sys
import tempfile
import unittest


class InterpolateLayoutTest(unittest.TestCase):
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

    def test_varlib_interpolate_layout_GSUB_only_ttf(self):
        """Only GSUB, and only in the base master.

        The variable font will inherit the GSUB table from the
        base master.
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('InterpolateLayout.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily2-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        instfont = interpolate_layout(ds_path, {'weight': 500}, finder)

        tables = ['GSUB']
        expected_ttx_path = self.get_test_output('InterpolateLayout.ttx')
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)


    def test_varlib_interpolate_layout_no_GSUB_ttf(self):
        """The base master has no GSUB table.

        The variable font will end up without a GSUB table.
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('InterpolateLayout2.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily2-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        instfont = interpolate_layout(ds_path, {'weight': 500}, finder)

        tables = ['GSUB']
        expected_ttx_path = self.get_test_output('InterpolateLayout2.ttx')
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)


    def test_varlib_interpolate_layout_GSUB_only_no_axes_ttf(self):
        """Only GSUB, and only in the base master.
        Designspace file has no <axes> element.

        The variable font will inherit the GSUB table from the
        base master.
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
        instfont = interpolate_layout(ds_path, {'weight': 500}, finder)

        tables = ['GSUB']
        expected_ttx_path = self.get_test_output('InterpolateLayout.ttx')
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)


    def test_varlib_interpolate_layout_main_ttf(self):
        """Mostly for testing varLib.interpolate_layout.main()
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

        finder = lambda s: s.replace(ufo_dir, ttf_dir).replace('.ufo', suffix)
        varfont, _, _ = build(ds_path, finder)
        varfont_name = 'InterpolateLayoutMain'
        varfont_path = os.path.join(self.tempdir, varfont_name + suffix)
        varfont.save(varfont_path)

        ds_copy = os.path.splitext(varfont_path)[0] + '.designspace'
        shutil.copy2(ds_path, ds_copy)
        args = [ds_copy, 'wght=500', 'cntr=50']
        interpolate_layout_main(args)

        instfont_path = os.path.splitext(varfont_path)[0] + '-instance' + suffix
        instfont = TTFont(instfont_path)
        tables = [table_tag for table_tag in instfont.keys() if table_tag != 'head']
        expected_ttx_path = self.get_test_output(varfont_name + '.ttx')
        self.expect_ttx(instfont, expected_ttx_path, tables)


if __name__ == "__main__":
    sys.exit(unittest.main())
