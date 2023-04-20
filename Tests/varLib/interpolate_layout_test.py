from fontTools.ttLib import TTFont
from fontTools.varLib import build
from fontTools.varLib.interpolate_layout import interpolate_layout
from fontTools.varLib.interpolate_layout import main as interpolate_layout_main
from fontTools.designspaceLib import DesignSpaceDocument, DesignSpaceDocumentError
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
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
    def get_file_list(folder, suffix, prefix=""):
        all_files = os.listdir(folder)
        file_list = []
        for p in all_files:
            if p.startswith(prefix) and p.endswith(suffix):
                file_list.append(os.path.abspath(os.path.join(folder, p)))
        return file_list

    def temp_path(self, suffix):
        self.temp_dir()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir, "tmp%d%s" % (self.num_tempfiles, suffix))

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

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

    def expect_ttx(self, font, expected_ttx, tables):
        path = self.temp_path(suffix=".ttx")
        font.saveXML(path, tables=tables)
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                expected, actual, fromfile=expected_ttx, tofile=path
            ):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def check_ttx_dump(self, font, expected_ttx, tables, suffix):
        """Ensure the TTX dump is the same after saving and reloading the font."""
        path = self.temp_path(suffix=suffix)
        font.save(path)
        self.expect_ttx(TTFont(path), expected_ttx, tables)

    def compile_font(self, path, suffix, temp_dir, features=None, cfg=None):
        ttx_filename = os.path.basename(path)
        savepath = os.path.join(temp_dir, ttx_filename.replace(".ttx", suffix))
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        if cfg:
            font.cfg.update(cfg)
        font.importXML(path)
        if features:
            addOpenTypeFeaturesFromString(font, features)
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
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GSUB"]
        expected_ttx_path = self.get_test_output("InterpolateLayout.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_no_GSUB_ttf(self):
        """The base master has no GSUB table.

        The variable font will end up without a GSUB table.
        """
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout2.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GSUB"]
        expected_ttx_path = self.get_test_output("InterpolateLayout2.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GSUB_only_no_axes_ttf(self):
        """Only GSUB, and only in the base master.
        Designspace file has no <axes> element.

        The variable font will inherit the GSUB table from the
        base master.
        """
        ds_path = self.get_test_input("InterpolateLayout3.designspace")
        with self.assertRaisesRegex(DesignSpaceDocumentError, "No axes defined"):
            instfont = interpolate_layout(ds_path, {"weight": 500})

    def test_varlib_interpolate_layout_GPOS_only_size_feat_same_val_ttf(self):
        """Only GPOS; 'size' feature; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        feature size {
            parameters 10.0 0;
        } size;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_size_feat_same.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_1_same_val_ttf(self):
        """Only GPOS; LookupType 1; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        feature xxxx {
            pos A <-80 0 -160 0>;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_1_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_1_diff_val_ttf(self):
        """Only GPOS; LookupType 1; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos A <-80 0 -160 0>;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos A <-97 0 -195 0>;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_1_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_1_diff2_val_ttf(self):
        """Only GPOS; LookupType 1; different values and items in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos A <-80 0 -160 0>;
            pos a <-55 0 -105 0>;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos A <-97 0 -195 0>;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_1_diff2.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_spec_pairs_same_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 specific pairs; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        feature xxxx {
            pos A a -53;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_spec_same.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_spec_pairs_diff_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 specific pairs; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos A a -53;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos A a -27;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_spec_diff.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_spec_pairs_diff2_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 specific pairs; different values and items in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos A a -53;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos A a -27;
            pos a a 19;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_spec_diff2.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_class_pairs_same_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 class pairs; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        feature xxxx {
            pos [A] [a] -53;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_class_same.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_class_pairs_diff_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 class pairs; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos [A] [a] -53;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos [A] [a] -27;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_class_diff.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_2_class_pairs_diff2_val_ttf(
        self,
    ):
        """Only GPOS; LookupType 2 class pairs; different values and items in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos [A] [a] -53;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos [A] [a] -27;
            pos [a] [a] 19;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output(
            "InterpolateLayoutGPOS_2_class_diff2.ttx"
        )
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_3_same_val_ttf(self):
        """Only GPOS; LookupType 3; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        feature xxxx {
            pos cursive a <anchor 60 15> <anchor 405 310>;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_3_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_3_diff_val_ttf(self):
        """Only GPOS; LookupType 3; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        feature xxxx {
            pos cursive a <anchor 60 15> <anchor 405 310>;
        } xxxx;
        """
        fea_str_1 = """
        feature xxxx {
            pos cursive a <anchor 38 42> <anchor 483 279>;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_3_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_4_same_val_ttf(self):
        """Only GPOS; LookupType 4; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        feature xxxx {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_4_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_4_diff_val_ttf(self):
        """Only GPOS; LookupType 4; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        feature xxxx {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } xxxx;
        """
        fea_str_1 = """
        markClass uni0303 <anchor 0 520> @MARKS_ABOVE;
        feature xxxx {
            pos base a <anchor 285 520> mark @MARKS_ABOVE;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_4_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_5_same_val_ttf(self):
        """Only GPOS; LookupType 5; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        markClass uni0330 <anchor 0 -50> @MARKS_BELOW;
        feature xxxx {
            pos ligature f_t <anchor 115 -50> mark @MARKS_BELOW
                ligComponent <anchor 430 -50> mark @MARKS_BELOW;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_5_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_5_diff_val_ttf(self):
        """Only GPOS; LookupType 5; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        markClass uni0330 <anchor 0 -50> @MARKS_BELOW;
        feature xxxx {
            pos ligature f_t <anchor 115 -50> mark @MARKS_BELOW
                ligComponent <anchor 430 -50> mark @MARKS_BELOW;
        } xxxx;
        """
        fea_str_1 = """
        markClass uni0330 <anchor 0 -20> @MARKS_BELOW;
        feature xxxx {
            pos ligature f_t <anchor 173 -20> mark @MARKS_BELOW
                ligComponent <anchor 577 -20> mark @MARKS_BELOW;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_5_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_6_same_val_ttf(self):
        """Only GPOS; LookupType 6; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        feature xxxx {
            pos mark uni0308 <anchor 0 675> mark @MARKS_ABOVE;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_6_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_6_diff_val_ttf(self):
        """Only GPOS; LookupType 6; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        feature xxxx {
            pos mark uni0308 <anchor 0 675> mark @MARKS_ABOVE;
        } xxxx;
        """
        fea_str_1 = """
        markClass uni0303 <anchor 0 520> @MARKS_ABOVE;
        feature xxxx {
            pos mark uni0308 <anchor 0 730> mark @MARKS_ABOVE;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_6_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_7_same_val_ttf(self):
        """Only GPOS; LookupType 7; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a -23;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        cfg = {"fontTools.otlLib.builder:WRITE_GPOS7": True}
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i], cfg)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_7_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_7_diff_val_ttf(self):
        """Only GPOS; LookupType 7; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a -23;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        fea_str_1 = """
        markClass uni0303 <anchor 0 520> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a 57;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 285 520> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        cfg = {"fontTools.otlLib.builder:WRITE_GPOS7": True}
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i], cfg)

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_7_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_8_same_val_ttf(self):
        """Only GPOS; LookupType 8; same values in all masters."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a -23;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        features = [fea_str] * 2

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_8_same.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_GPOS_only_LookupType_8_diff_val_ttf(self):
        """Only GPOS; LookupType 8; different values in each master."""
        suffix = ".ttf"
        ds_path = self.get_test_input("InterpolateLayout.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        fea_str_0 = """
        markClass uni0303 <anchor 0 500> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a -23;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 260 500> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        fea_str_1 = """
        markClass uni0303 <anchor 0 520> @MARKS_ABOVE;
        lookup CNTXT_PAIR_POS {
            pos A a 57;
        } CNTXT_PAIR_POS;

        lookup CNTXT_MARK_TO_BASE {
            pos base a <anchor 285 520> mark @MARKS_ABOVE;
        } CNTXT_MARK_TO_BASE;

        feature xxxx {
            pos A' lookup CNTXT_PAIR_POS a' @MARKS_ABOVE' lookup CNTXT_MARK_TO_BASE;
        } xxxx;
        """
        features = [fea_str_0, fea_str_1]

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for i, path in enumerate(ttx_paths):
            self.compile_font(path, suffix, self.tempdir, features[i])

        finder = lambda s: s.replace(ufo_dir, self.tempdir).replace(".ufo", suffix)
        instfont = interpolate_layout(ds_path, {"weight": 500}, finder)

        tables = ["GPOS"]
        expected_ttx_path = self.get_test_output("InterpolateLayoutGPOS_8_diff.ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)
        self.check_ttx_dump(instfont, expected_ttx_path, tables, suffix)

    def test_varlib_interpolate_layout_main_ttf(self):
        """Mostly for testing varLib.interpolate_layout.main()"""
        suffix = ".ttf"
        ds_path = self.get_test_input("Build.designspace")
        ufo_dir = self.get_test_input("master_ufo")
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttf_dir = os.path.join(self.tempdir, "master_ttf_interpolatable")
        os.makedirs(ttf_dir)
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily-")
        for path in ttx_paths:
            self.compile_font(path, suffix, ttf_dir)

        finder = lambda s: s.replace(ufo_dir, ttf_dir).replace(".ufo", suffix)
        varfont, _, _ = build(ds_path, finder)
        varfont_name = "InterpolateLayoutMain"
        varfont_path = os.path.join(self.tempdir, varfont_name + suffix)
        varfont.save(varfont_path)

        ds_copy = os.path.splitext(varfont_path)[0] + ".designspace"
        shutil.copy2(ds_path, ds_copy)
        args = [ds_copy, "weight=500", "contrast=50"]
        interpolate_layout_main(args)

        instfont_path = os.path.splitext(varfont_path)[0] + "-instance" + suffix
        instfont = TTFont(instfont_path)
        tables = [table_tag for table_tag in instfont.keys() if table_tag != "head"]
        expected_ttx_path = self.get_test_output(varfont_name + ".ttx")
        self.expect_ttx(instfont, expected_ttx_path, tables)


if __name__ == "__main__":
    sys.exit(unittest.main())
