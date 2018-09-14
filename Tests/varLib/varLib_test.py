from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib import build
from fontTools.varLib import main as varLib_main
from fontTools.designspaceLib import DesignSpaceDocumentError
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

    def _run_varlib_build_test(self, designspace_name, font_name, tables,
                               expected_ttx_name, save_before_dump=False):
        suffix = '.ttf'
        ds_path = self.get_test_input(designspace_name + '.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', font_name + '-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace('.ufo', suffix)
        varfont, model, _ = build(ds_path, finder)

        if save_before_dump:
            # some data (e.g. counts printed in TTX inline comments) is only
            # calculated at compile time, so before we can compare the TTX
            # dumps we need to save to a temporary stream, and realod the font
            buf = BytesIO()
            varfont.save(buf)
            buf.seek(0)
            varfont = TTFont(buf)

        expected_ttx_path = self.get_test_output(expected_ttx_name + '.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)
# -----
# Tests
# -----

    def test_varlib_build_ttf(self):
        """Designspace file contains <axes> element."""
        self._run_varlib_build_test(
            designspace_name='Build',
            font_name='TestFamily',
            tables=['GDEF', 'HVAR', 'MVAR', 'fvar', 'gvar'],
            expected_ttx_name='Build'
        )

    def test_varlib_build_no_axes_ttf(self):
        """Designspace file does not contain an <axes> element."""
        ds_path = self.get_test_input('InterpolateLayout3.designspace')
        with self.assertRaisesRegex(DesignSpaceDocumentError, "No axes defined"):
            build(ds_path)

    def test_varlib_avar_single_axis(self):
        """Designspace file contains a 'weight' axis with <map> elements
        modifying the normalization mapping. An 'avar' table is generated.
        """
        test_name = 'BuildAvarSingleAxis'
        self._run_varlib_build_test(
            designspace_name=test_name,
            font_name='TestFamily3',
            tables=['avar'],
            expected_ttx_name=test_name
        )

    def test_varlib_avar_with_identity_maps(self):
        """Designspace file contains two 'weight' and 'width' axes both with
        <map> elements.

        The 'width' axis only contains identity mappings, however the resulting
        avar segment will not be empty but will contain the default axis value
        maps: {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}.

        This is to to work around an issue with some rasterizers:
        https://github.com/googlei18n/fontmake/issues/295
        https://github.com/fonttools/fonttools/issues/1011
        """
        test_name = 'BuildAvarIdentityMaps'
        self._run_varlib_build_test(
            designspace_name=test_name,
            font_name='TestFamily3',
            tables=['avar'],
            expected_ttx_name=test_name
        )

    def test_varlib_avar_empty_axis(self):
        """Designspace file contains two 'weight' and 'width' axes, but
        only one axis ('weight') has some <map> elements.

        Even if no <map> elements are defined for the 'width' axis, the
        resulting avar segment still contains the default axis value maps:
        {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}.

        This is again to to work around an issue with some rasterizers:
        https://github.com/googlei18n/fontmake/issues/295
        https://github.com/fonttools/fonttools/issues/1011
        """
        test_name = 'BuildAvarEmptyAxis'
        self._run_varlib_build_test(
            designspace_name=test_name,
            font_name='TestFamily3',
            tables=['avar'],
            expected_ttx_name=test_name
        )

    def test_varlib_build_feature_variations(self):
        """Designspace file contains <rules> element, used to build
        GSUB FeatureVariations table.
        """
        self._run_varlib_build_test(
            designspace_name="FeatureVars",
            font_name="TestFamily",
            tables=["fvar", "GSUB"],
            expected_ttx_name="FeatureVars",
            save_before_dump=True,
        )

    def test_varlib_main_ttf(self):
        """Mostly for testing varLib.main()
        """
        suffix = '.ttf'
        ds_path = self.get_test_input('Build.designspace')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttf_dir = os.path.join(self.tempdir, 'master_ttf_interpolatable')
        os.makedirs(ttf_dir)
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily-')
        for path in ttx_paths:
            self.compile_font(path, suffix, ttf_dir)

        ds_copy = os.path.join(self.tempdir, 'BuildMain.designspace')
        shutil.copy2(ds_path, ds_copy)

        # by default, varLib.main finds master TTFs inside a
        # 'master_ttf_interpolatable' subfolder in current working dir
        cwd = os.getcwd()
        os.chdir(self.tempdir)
        try:
            varLib_main([ds_copy])
        finally:
            os.chdir(cwd)

        varfont_path = os.path.splitext(ds_copy)[0] + '-VF' + suffix
        self.assertTrue(os.path.exists(varfont_path))

        # try again passing an explicit --master-finder
        os.remove(varfont_path)
        finder = "%s/master_ttf_interpolatable/{stem}.ttf" % self.tempdir
        varLib_main([ds_copy, "--master-finder", finder])
        self.assertTrue(os.path.exists(varfont_path))

        # and also with explicit -o output option
        os.remove(varfont_path)
        varfont_path = os.path.splitext(varfont_path)[0] + "-o" + suffix
        varLib_main([ds_copy, "-o", varfont_path, "--master-finder", finder])
        self.assertTrue(os.path.exists(varfont_path))

        varfont = TTFont(varfont_path)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != 'head']
        expected_ttx_path = self.get_test_output('BuildMain.ttx')
        self.expect_ttx(varfont, expected_ttx_path, tables)


if __name__ == "__main__":
    sys.exit(unittest.main())
