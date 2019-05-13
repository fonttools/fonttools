from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import build
from fontTools.varLib import main as varLib_main, load_masters
from fontTools.designspaceLib import (
    DesignSpaceDocumentError, DesignSpaceDocument, SourceDescriptor,
)
import difflib
import os
import shutil
import sys
import tempfile
import unittest
import pytest


def reload_font(font):
    """(De)serialize to get final binary layout."""
    buf = BytesIO()
    font.save(buf)
    buf.seek(0)
    return TTFont(buf)


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
            varfont = reload_font(varfont)

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

        This is to work around an issue with some rasterizers:
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

        This is again to work around an issue with some rasterizers:
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

    def test_varlib_gvar_explicit_delta(self):
        """The variable font contains a composite glyph odieresis which does not
        need a gvar entry, because all its deltas are 0, but it must be added
        anyway to work around an issue with macOS 10.14.

        https://github.com/fonttools/fonttools/issues/1381
        """
        test_name = 'BuildGvarCompositeExplicitDelta'
        self._run_varlib_build_test(
            designspace_name=test_name,
            font_name='TestFamily4',
            tables=['gvar'],
            expected_ttx_name=test_name
        )

    def test_varlib_build_CFF2(self):
        ds_path = self.get_test_input('TestCFF2.designspace')
        ttx_dir = self.get_test_input("master_cff2")
        expected_ttx_path = self.get_test_output("BuildTestCFF2.ttx")

        self.temp_dir()
        for path in self.get_file_list(ttx_dir, '.ttx', 'TestCFF2_'):
            self.compile_font(path, ".otf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".otf")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        tables = ["fvar", "CFF2"]
        self.expect_ttx(varfont, expected_ttx_path, tables)


    def test_varlib_build_sparse_CFF2(self):
        ds_path = self.get_test_input('TestSparseCFF2VF.designspace')
        ttx_dir = self.get_test_input("master_sparse_cff2")
        expected_ttx_path = self.get_test_output("TestSparseCFF2VF.ttx")

        self.temp_dir()
        for path in self.get_file_list(ttx_dir, '.ttx', 'MasterSet_Kanji-'):
            self.compile_font(path, ".otf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".otf")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        tables = ["fvar", "CFF2"]
        self.expect_ttx(varfont, expected_ttx_path, tables)


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

    def test_varlib_build_from_ds_object_in_memory_ttfonts(self):
        ds_path = self.get_test_input("Build.designspace")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")
        expected_ttx_path = self.get_test_output("BuildMain.ttx")

        self.temp_dir()
        for path in self.get_file_list(ttx_dir, '.ttx', 'TestFamily-'):
            self.compile_font(path, ".ttf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            filename = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".ttf")
            )
            source.font = TTFont(
                filename, recalcBBoxes=False, recalcTimestamp=False, lazy=True
            )
            source.filename = None  # Make sure no file path gets into build()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != "head"]
        self.expect_ttx(varfont, expected_ttx_path, tables)

    def test_varlib_build_from_ttf_paths(self):
        ds_path = self.get_test_input("Build.designspace")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")
        expected_ttx_path = self.get_test_output("BuildMain.ttx")

        self.temp_dir()
        for path in self.get_file_list(ttx_dir, '.ttx', 'TestFamily-'):
            self.compile_font(path, ".ttf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".ttf")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != "head"]
        self.expect_ttx(varfont, expected_ttx_path, tables)

    def test_varlib_build_from_ttx_paths(self):
        ds_path = self.get_test_input("Build.designspace")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")
        expected_ttx_path = self.get_test_output("BuildMain.ttx")

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                ttx_dir, os.path.basename(source.filename).replace(".ufo", ".ttx")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != "head"]
        self.expect_ttx(varfont, expected_ttx_path, tables)

    def test_varlib_build_sparse_masters(self):
        ds_path = self.get_test_input("SparseMasters.designspace")
        expected_ttx_path = self.get_test_output("SparseMasters.ttx")

        varfont, _, _ = build(ds_path)
        varfont = reload_font(varfont)
        tables = [table_tag for table_tag in varfont.keys() if table_tag != "head"]
        self.expect_ttx(varfont, expected_ttx_path, tables)

    def test_varlib_build_sparse_masters_MVAR(self):
        import fontTools.varLib.mvar

        ds_path = self.get_test_input("SparseMasters.designspace")
        ds = DesignSpaceDocument.fromfile(ds_path)
        load_masters(ds)

        # Trigger MVAR generation so varLib is forced to create deltas with a
        # sparse master inbetween.
        font_0_os2 = ds.sources[0].font["OS/2"]
        font_0_os2.sTypoAscender = 1
        font_0_os2.sTypoDescender = 1
        font_0_os2.sTypoLineGap = 1
        font_0_os2.usWinAscent = 1
        font_0_os2.usWinDescent = 1
        font_0_os2.sxHeight = 1
        font_0_os2.sCapHeight = 1
        font_0_os2.ySubscriptXSize = 1
        font_0_os2.ySubscriptYSize = 1
        font_0_os2.ySubscriptXOffset = 1
        font_0_os2.ySubscriptYOffset = 1
        font_0_os2.ySuperscriptXSize = 1
        font_0_os2.ySuperscriptYSize = 1
        font_0_os2.ySuperscriptXOffset = 1
        font_0_os2.ySuperscriptYOffset = 1
        font_0_os2.yStrikeoutSize = 1
        font_0_os2.yStrikeoutPosition = 1
        font_0_vhea = newTable("vhea")
        font_0_vhea.ascent = 1
        font_0_vhea.descent = 1
        font_0_vhea.lineGap = 1
        font_0_vhea.caretSlopeRise = 1
        font_0_vhea.caretSlopeRun = 1
        font_0_vhea.caretOffset = 1
        ds.sources[0].font["vhea"] = font_0_vhea
        font_0_hhea = ds.sources[0].font["hhea"]
        font_0_hhea.caretSlopeRise = 1
        font_0_hhea.caretSlopeRun = 1
        font_0_hhea.caretOffset = 1
        font_0_post = ds.sources[0].font["post"]
        font_0_post.underlineThickness = 1
        font_0_post.underlinePosition = 1

        font_2_os2 = ds.sources[2].font["OS/2"]
        font_2_os2.sTypoAscender = 800
        font_2_os2.sTypoDescender = 800
        font_2_os2.sTypoLineGap = 800
        font_2_os2.usWinAscent = 800
        font_2_os2.usWinDescent = 800
        font_2_os2.sxHeight = 800
        font_2_os2.sCapHeight = 800
        font_2_os2.ySubscriptXSize = 800
        font_2_os2.ySubscriptYSize = 800
        font_2_os2.ySubscriptXOffset = 800
        font_2_os2.ySubscriptYOffset = 800
        font_2_os2.ySuperscriptXSize = 800
        font_2_os2.ySuperscriptYSize = 800
        font_2_os2.ySuperscriptXOffset = 800
        font_2_os2.ySuperscriptYOffset = 800
        font_2_os2.yStrikeoutSize = 800
        font_2_os2.yStrikeoutPosition = 800
        font_2_vhea = newTable("vhea")
        font_2_vhea.ascent = 800
        font_2_vhea.descent = 800
        font_2_vhea.lineGap = 800
        font_2_vhea.caretSlopeRise = 800
        font_2_vhea.caretSlopeRun = 800
        font_2_vhea.caretOffset = 800
        ds.sources[2].font["vhea"] = font_2_vhea
        font_2_hhea = ds.sources[2].font["hhea"]
        font_2_hhea.caretSlopeRise = 800
        font_2_hhea.caretSlopeRun = 800
        font_2_hhea.caretOffset = 800
        font_2_post = ds.sources[2].font["post"]
        font_2_post.underlineThickness = 800
        font_2_post.underlinePosition = 800

        varfont, _, _ = build(ds)
        mvar_tags = [vr.ValueTag for vr in varfont["MVAR"].table.ValueRecord]
        assert all(tag in mvar_tags for tag in fontTools.varLib.mvar.MVAR_ENTRIES)

    def test_varlib_build_VVAR_CFF2(self):
        ds_path = self.get_test_input('TestVVAR.designspace')
        ttx_dir = self.get_test_input("master_vvar_cff2")
        expected_ttx_name = 'TestVVAR'
        suffix = '.otf'

        self.temp_dir()
        for path in self.get_file_list(ttx_dir, '.ttx', 'TestVVAR'):
            font, savepath = self.compile_font(path, suffix, self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", suffix)
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        expected_ttx_path = self.get_test_output(expected_ttx_name + '.ttx')
        tables = ["VVAR"]
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)


def test_load_masters_layerName_without_required_font():
    ds = DesignSpaceDocument()
    s = SourceDescriptor()
    s.font = None
    s.layerName = "Medium"
    ds.addSource(s)

    with pytest.raises(
        AttributeError,
        match="specified a layer name but lacks the required TTFont object",
    ):
        load_masters(ds)


if __name__ == "__main__":
    sys.exit(unittest.main())
