from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import build, load_designspace
from fontTools.varLib.errors import VarLibValidationError
from fontTools.varLib.mutator import instantiateVariableFont
from fontTools.varLib import main as varLib_main, load_masters
from fontTools.varLib import set_default_weight_width_slant
from fontTools.designspaceLib import (
    DesignSpaceDocumentError, DesignSpaceDocument, SourceDescriptor,
)
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
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
    # Close the font to release filesystem resources so that on Windows the tearDown
    # method can successfully remove the temporary directory created during setUp.
    font.close()
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

    def get_test_input(self, test_file_or_folder, copy=False):
        parent_dir = os.path.dirname(__file__)
        path = os.path.join(parent_dir, "data", test_file_or_folder)
        if copy:
            copied_path = os.path.join(self.tempdir, test_file_or_folder)
            shutil.copy2(path, copied_path)
            return copied_path
        else:
            return path

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
                               expected_ttx_name, save_before_dump=False,
                               post_process_master=None):
        suffix = '.ttf'
        ds_path = self.get_test_input(designspace_name + '.designspace')
        ufo_dir = self.get_test_input('master_ufo')
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', font_name + '-')
        for path in ttx_paths:
            font, savepath = self.compile_font(path, suffix, self.tempdir)
            if post_process_master is not None:
                post_process_master(font, savepath)

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

    def test_varlib_build_feature_variations_custom_tag(self):
        """Designspace file contains <rules> element, used to build
        GSUB FeatureVariations table.
        """
        self._run_varlib_build_test(
            designspace_name="FeatureVarsCustomTag",
            font_name="TestFamily",
            tables=["fvar", "GSUB"],
            expected_ttx_name="FeatureVarsCustomTag",
            save_before_dump=True,
        )

    def test_varlib_build_feature_variations_whole_range(self):
        """Designspace file contains <rules> element specifying the entire design
        space, used to build GSUB FeatureVariations table.
        """
        self._run_varlib_build_test(
            designspace_name="FeatureVarsWholeRange",
            font_name="TestFamily",
            tables=["fvar", "GSUB"],
            expected_ttx_name="FeatureVarsWholeRange",
            save_before_dump=True,
        )

    def test_varlib_build_feature_variations_whole_range_empty(self):
        """Designspace file contains <rules> element without a condition, specifying
        the entire design space, used to build GSUB FeatureVariations table.
        """
        self._run_varlib_build_test(
            designspace_name="FeatureVarsWholeRangeEmpty",
            font_name="TestFamily",
            tables=["fvar", "GSUB"],
            expected_ttx_name="FeatureVarsWholeRange",
            save_before_dump=True,
        )

    def test_varlib_build_feature_variations_with_existing_rclt(self):
        """Designspace file contains <rules> element, used to build GSUB
        FeatureVariations table. <rules> is specified to do its OT processing
        "last", so a 'rclt' feature will be used or created. This test covers
        the case when a 'rclt' already exists in the masters.

        We dynamically add a 'rclt' feature to an existing set of test
        masters, to avoid adding more test data.

        The multiple languages are done to verify whether multiple existing
        'rclt' features are updated correctly.
        """
        def add_rclt(font, savepath):
            features = """
            languagesystem DFLT dflt;
            languagesystem latn dflt;
            languagesystem latn NLD;

            feature rclt {
                script latn;
                language NLD;
                lookup A {
                    sub uni0041 by uni0061;
                } A;
                language dflt;
                lookup B {
                    sub uni0041 by uni0061;
                } B;
            } rclt;
            """
            addOpenTypeFeaturesFromString(font, features)
            font.save(savepath)
        self._run_varlib_build_test(
            designspace_name="FeatureVars",
            font_name="TestFamily",
            tables=["fvar", "GSUB"],
            expected_ttx_name="FeatureVars_rclt",
            save_before_dump=True,
            post_process_master=add_rclt,
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

    def test_varlib_nonmarking_CFF2(self):
        self.temp_dir()

        ds_path = self.get_test_input('TestNonMarkingCFF2.designspace', copy=True)
        ttx_dir = self.get_test_input("master_non_marking_cff2")
        expected_ttx_path = self.get_test_output("TestNonMarkingCFF2.ttx")

        for path in self.get_file_list(ttx_dir, '.ttx', 'TestNonMarkingCFF2_'):
            self.compile_font(path, ".otf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".otf")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        tables = ["CFF2"]
        self.expect_ttx(varfont, expected_ttx_path, tables)

    def test_varlib_build_CFF2(self):
        self.temp_dir()

        ds_path = self.get_test_input('TestCFF2.designspace', copy=True)
        ttx_dir = self.get_test_input("master_cff2")
        expected_ttx_path = self.get_test_output("BuildTestCFF2.ttx")

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

    def test_varlib_build_CFF2_from_CFF2(self):
        self.temp_dir()

        ds_path = self.get_test_input('TestCFF2Input.designspace', copy=True)
        ttx_dir = self.get_test_input("master_cff2_input")
        expected_ttx_path = self.get_test_output("BuildTestCFF2.ttx")

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
        self.temp_dir()

        ds_path = self.get_test_input('TestSparseCFF2VF.designspace', copy=True)
        ttx_dir = self.get_test_input("master_sparse_cff2")
        expected_ttx_path = self.get_test_output("TestSparseCFF2VF.ttx")

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

    def test_varlib_build_vpal(self):
        self.temp_dir()

        ds_path = self.get_test_input('test_vpal.designspace', copy=True)
        ttx_dir = self.get_test_input("master_vpal_test")
        expected_ttx_path = self.get_test_output("test_vpal.ttx")

        for path in self.get_file_list(ttx_dir, '.ttx', 'master_vpal_test_'):
            self.compile_font(path, ".otf", self.tempdir)

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            source.path = os.path.join(
                self.tempdir, os.path.basename(source.filename).replace(".ufo", ".otf")
            )
        ds.updatePaths()

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        tables = ["GPOS"]
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
        self.temp_dir()

        ds_path = self.get_test_input("Build.designspace", copy=True)
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")
        expected_ttx_path = self.get_test_output("BuildMain.ttx")

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

    def test_varlib_build_lazy_masters(self):
        # See https://github.com/fonttools/fonttools/issues/1808
        ds_path = self.get_test_input("SparseMasters.designspace")
        expected_ttx_path = self.get_test_output("SparseMasters.ttx")

        def _open_font(master_path, master_finder=lambda s: s):
            font = TTFont()
            font.importXML(master_path)
            buf = BytesIO()
            font.save(buf, reorderTables=False)
            buf.seek(0)
            font = TTFont(buf, lazy=True)  # reopen in lazy mode, to reproduce #1808
            return font

        ds = DesignSpaceDocument.fromfile(ds_path)
        ds.loadSourceFonts(_open_font)
        varfont, _, _ = build(ds)
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
        self.temp_dir()

        ds_path = self.get_test_input('TestVVAR.designspace', copy=True)
        ttx_dir = self.get_test_input("master_vvar_cff2")
        expected_ttx_name = 'TestVVAR'
        suffix = '.otf'

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

    def test_varlib_build_BASE(self):
        self.temp_dir()

        ds_path = self.get_test_input('TestBASE.designspace', copy=True)
        ttx_dir = self.get_test_input("master_base_test")
        expected_ttx_name = 'TestBASE'
        suffix = '.otf'

        for path in self.get_file_list(ttx_dir, '.ttx', 'TestBASE'):
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
        tables = ["BASE"]
        self.expect_ttx(varfont, expected_ttx_path, tables)
        self.check_ttx_dump(varfont, expected_ttx_path, tables, suffix)

    def test_varlib_build_single_master(self):
        self._run_varlib_build_test(
            designspace_name='SingleMaster',
            font_name='TestFamily',
            tables=['GDEF', 'HVAR', 'MVAR', 'STAT', 'fvar', 'cvar', 'gvar', 'name'],
            expected_ttx_name='SingleMaster',
            save_before_dump=True,
        )

    def test_kerning_merging(self):
        """Test the correct merging of class-based pair kerning.

        Problem description at https://github.com/fonttools/fonttools/pull/1638.
        Test font and Designspace generated by 
        https://gist.github.com/madig/183d0440c9f7d05f04bd1280b9664bd1.
        """
        ds_path = self.get_test_input("KerningMerging.designspace")
        ttx_dir = self.get_test_input("master_kerning_merging")

        ds = DesignSpaceDocument.fromfile(ds_path)
        for source in ds.sources:
            ttx_dump = TTFont()
            ttx_dump.importXML(
                os.path.join(
                    ttx_dir, os.path.basename(source.filename).replace(".ttf", ".ttx")
                )
            )
            source.font = reload_font(ttx_dump)

        varfont, _, _ = build(ds)
        varfont = reload_font(varfont)

        class_kerning_tables = [
            t
            for l in varfont["GPOS"].table.LookupList.Lookup
            for t in l.SubTable
            if t.Format == 2
        ]
        assert len(class_kerning_tables) == 1
        class_kerning_table = class_kerning_tables[0]

        # Test that no class kerned against class zero (containing all glyphs not
        # classed) has a `XAdvDevice` table attached, which in the variable font
        # context is a "VariationIndex" table and points to kerning deltas in the GDEF
        # table. Variation deltas of any kerning class against class zero should
        # probably never exist.
        for class1_record in class_kerning_table.Class1Record:
            class2_zero = class1_record.Class2Record[0]
            assert getattr(class2_zero.Value1, "XAdvDevice", None) is None

        # Assert the variable font's kerning table (without deltas) is equal to the
        # default font's kerning table. The bug fixed in 
        # https://github.com/fonttools/fonttools/pull/1638 caused rogue kerning
        # values to be written to the variable font.
        assert _extract_flat_kerning(varfont, class_kerning_table) == {
            ("A", ".notdef"): 0,
            ("A", "A"): 0,
            ("A", "B"): -20,
            ("A", "C"): 0,
            ("A", "D"): -20,
            ("B", ".notdef"): 0,
            ("B", "A"): 0,
            ("B", "B"): 0,
            ("B", "C"): 0,
            ("B", "D"): 0,
        }

        instance_thin = instantiateVariableFont(varfont, {"wght": 100})
        instance_thin_kerning_table = (
            instance_thin["GPOS"].table.LookupList.Lookup[0].SubTable[0]
        )
        assert _extract_flat_kerning(instance_thin, instance_thin_kerning_table) == {
            ("A", ".notdef"): 0,
            ("A", "A"): 0,
            ("A", "B"): 0,
            ("A", "C"): 10,
            ("A", "D"): 0,
            ("B", ".notdef"): 0,
            ("B", "A"): 0,
            ("B", "B"): 0,
            ("B", "C"): 10,
            ("B", "D"): 0,
        }

        instance_black = instantiateVariableFont(varfont, {"wght": 900})
        instance_black_kerning_table = (
            instance_black["GPOS"].table.LookupList.Lookup[0].SubTable[0]
        )
        assert _extract_flat_kerning(instance_black, instance_black_kerning_table) == {
            ("A", ".notdef"): 0,
            ("A", "A"): 0,
            ("A", "B"): 0,
            ("A", "C"): 0,
            ("A", "D"): 40,
            ("B", ".notdef"): 0,
            ("B", "A"): 0,
            ("B", "B"): 0,
            ("B", "C"): 0,
            ("B", "D"): 40,
        }

    def test_designspace_fill_in_location(self):
        ds_path = self.get_test_input("VarLibLocationTest.designspace")
        ds = DesignSpaceDocument.fromfile(ds_path)
        ds_loaded = load_designspace(ds)

        assert ds_loaded.instances[0].location == {"weight": 0, "width": 50}


def test_load_masters_layerName_without_required_font():
    ds = DesignSpaceDocument()
    s = SourceDescriptor()
    s.font = None
    s.layerName = "Medium"
    ds.addSource(s)

    with pytest.raises(
        VarLibValidationError,
        match="specified a layer name but lacks the required TTFont object",
    ):
        load_masters(ds)


def _extract_flat_kerning(font, pairpos_table):
    extracted_kerning = {}
    for glyph_name_1 in pairpos_table.Coverage.glyphs:
        class_def_1 = pairpos_table.ClassDef1.classDefs.get(glyph_name_1, 0)
        for glyph_name_2 in font.getGlyphOrder():
            class_def_2 = pairpos_table.ClassDef2.classDefs.get(glyph_name_2, 0)
            kern_value = (
                pairpos_table.Class1Record[class_def_1]
                .Class2Record[class_def_2]
                .Value1.XAdvance
            )
            extracted_kerning[(glyph_name_1, glyph_name_2)] = kern_value
    return extracted_kerning


@pytest.fixture
def ttFont():
    f = TTFont()
    f["OS/2"] = newTable("OS/2")
    f["OS/2"].usWeightClass = 400
    f["OS/2"].usWidthClass = 100
    f["post"] = newTable("post")
    f["post"].italicAngle = 0
    return f


class SetDefaultWeightWidthSlantTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": 0}, 1),
            ({"wght": 1}, 1),
            ({"wght": 100}, 100),
            ({"wght": 1000}, 1000),
            ({"wght": 1001}, 1000),
        ],
    )
    def test_wght(self, ttFont, location, expected):
        set_default_weight_width_slant(ttFont, location)

        assert ttFont["OS/2"].usWeightClass == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wdth": 0}, 1),
            ({"wdth": 56}, 1),
            ({"wdth": 57}, 2),
            ({"wdth": 62.5}, 2),
            ({"wdth": 75}, 3),
            ({"wdth": 87.5}, 4),
            ({"wdth": 100}, 5),
            ({"wdth": 112.5}, 6),
            ({"wdth": 125}, 7),
            ({"wdth": 150}, 8),
            ({"wdth": 200}, 9),
            ({"wdth": 201}, 9),
            ({"wdth": 1000}, 9),
        ],
    )
    def test_wdth(self, ttFont, location, expected):
        set_default_weight_width_slant(ttFont, location)

        assert ttFont["OS/2"].usWidthClass == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"slnt": -91}, -90),
            ({"slnt": -90}, -90),
            ({"slnt": 0}, 0),
            ({"slnt": 11.5}, 11.5),
            ({"slnt": 90}, 90),
            ({"slnt": 91}, 90),
        ],
    )
    def test_slnt(self, ttFont, location, expected):
        set_default_weight_width_slant(ttFont, location)

        assert ttFont["post"].italicAngle == expected

    def test_all(self, ttFont):
        set_default_weight_width_slant(
            ttFont, {"wght": 500, "wdth": 150, "slnt": -12.0}
        )

        assert ttFont["OS/2"].usWeightClass == 500
        assert ttFont["OS/2"].usWidthClass == 8
        assert ttFont["post"].italicAngle == -12.0


if __name__ == "__main__":
    sys.exit(unittest.main())
