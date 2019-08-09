from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.varLib.interpolatable import main as interpolatable_main
import os
import shutil
import sys
import tempfile
import unittest

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
    def get_test_input(test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", test_file_or_folder)

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

    def test_interpolatable_ttf(self):
        suffix = '.ttf'
        ttx_dir = self.get_test_input('master_ttx_interpolatable_ttf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily2-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        ttf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(ttf_paths))


    def test_interpolatable_otf(self):
        suffix = '.otf'
        ttx_dir = self.get_test_input('master_ttx_interpolatable_otf')

        self.temp_dir()
        ttx_paths = self.get_file_list(ttx_dir, '.ttx', 'TestFamily2-')
        for path in ttx_paths:
            self.compile_font(path, suffix, self.tempdir)

        otf_paths = self.get_file_list(self.tempdir, suffix)
        self.assertIsNone(interpolatable_main(otf_paths))


if __name__ == "__main__":
    sys.exit(unittest.main())
