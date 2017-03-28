from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttx
import getopt
import os
import shutil
import sys
import tempfile
import unittest


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


if __name__ == "__main__":
    sys.exit(unittest.main())
