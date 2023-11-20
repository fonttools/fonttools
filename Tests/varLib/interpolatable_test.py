from fontTools.ttLib import TTFont
from fontTools.varLib.interpolatable import main as interpolatable_main
import os
import shutil
import sys
import tempfile
import unittest
import pytest

try:
    import scipy
except:
    scipy = None

try:
    import munkres
except ImportError:
    munkres = None


@unittest.skipUnless(scipy or munkres, "scipy or munkres not installed")
class InterpolatableTest(unittest.TestCase):
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
    def get_test_input(*test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", *test_file_or_folder)

    @staticmethod
    def get_file_list(folder, suffix, prefix=""):
        all_files = os.listdir(folder)
        file_list = []
        for p in all_files:
            if p.startswith(prefix) and p.endswith(suffix):
                file_list.append(os.path.abspath(os.path.join(folder, p)))
        return sorted(file_list)

    def temp_path(self, suffix):
        self.temp_dir()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir, "tmp%d%s" % (self.num_tempfiles, suffix))

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

    def compile_font(self, path, suffix, temp_dir):
        ttx_filename = os.path.basename(path)
        savepath = os.path.join(temp_dir, ttx_filename.replace(".ttx", suffix))
        font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

    # -----
    # Tests
    # -----

    def test_interpolatable_ttf(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(ttf_paths))

    def test_interpolatable_otf(self):
        suffix = ".otf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_otf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "TestFamily2-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        otf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(otf_paths))

    def test_interpolatable_ufo(self):
        ttx_dir = self.get_test_input("master_ufo")
        ufo_paths = self.get_file_list(ttx_dir, ".ufo", "TestFamily2-")
        self.assertIsNone(interpolatable_main(ufo_paths))

    def test_designspace(self):
        designspace_path = self.get_test_input("InterpolateLayout.designspace")
        self.assertIsNone(interpolatable_main([designspace_path]))

    def test_glyphsapp(self):
        pytest.importorskip("glyphsLib")
        glyphsapp_path = self.get_test_input("InterpolateLayout.glyphs")
        self.assertIsNone(interpolatable_main([glyphsapp_path]))

    def test_VF(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_varfont_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "SparseMasters-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)

        problems = interpolatable_main(["--quiet"] + ttf_paths)
        self.assertIsNone(problems)

    def test_sparse_interpolatable_ttfs(self):
        suffix = ".ttf"
        ttx_dir = self.get_test_input("master_ttx_interpolatable_ttf")

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, ".ttx", "SparseMasters-")
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)

        # without --ignore-missing
        problems = interpolatable_main(["--quiet"] + ttf_paths)
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing"] + ttf_paths))
        # purposely putting the sparse master (medium) first
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ttf_paths[1]] + [ttf_paths[0]] + [ttf_paths[2]]
            )
        )
        # purposely putting the sparse master (medium) last
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ttf_paths[0]] + [ttf_paths[2]] + [ttf_paths[1]]
            )
        )

    def test_sparse_interpolatable_ufos(self):
        ttx_dir = self.get_test_input("master_ufo")
        ufo_paths = self.get_file_list(ttx_dir, ".ufo", "SparseMasters-")

        # without --ignore-missing
        problems = interpolatable_main(["--quiet"] + ufo_paths)
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing"] + ufo_paths))
        # purposely putting the sparse master (medium) first
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ufo_paths[1]] + [ufo_paths[0]] + [ufo_paths[2]]
            )
        )
        # purposely putting the sparse master (medium) last
        self.assertIsNone(
            interpolatable_main(
                ["--ignore-missing"] + [ufo_paths[0]] + [ufo_paths[2]] + [ufo_paths[1]]
            )
        )

    def test_sparse_designspace(self):
        designspace_path = self.get_test_input("SparseMasters_ufo.designspace")

        problems = interpolatable_main(["--quiet", designspace_path])
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "SparseMasters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing", designspace_path]))

    def test_sparse_glyphsapp(self):
        pytest.importorskip("glyphsLib")
        glyphsapp_path = self.get_test_input("SparseMasters.glyphs")

        problems = interpolatable_main(["--quiet", glyphsapp_path])
        self.assertEqual(
            problems["a"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["s"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["edotabove"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )
        self.assertEqual(
            problems["dotabovecomb"],
            [{"type": "missing", "master": "Sparse Masters-Medium", "master_idx": 1}],
        )

        # normal order, with --ignore-missing
        self.assertIsNone(interpolatable_main(["--ignore-missing", glyphsapp_path]))

    def test_interpolatable_varComposite(self):
        input_path = self.get_test_input(
            "..", "..", "ttLib", "data", "varc-ac00-ac01.ttf"
        )
        # This particular test font which was generated by machine-learning
        # exhibits an "error" in one of the masters; it's a false-positive.
        # Just make sure the code runs.
        interpolatable_main((input_path,))


if __name__ == "__main__":
    sys.exit(unittest.main())
