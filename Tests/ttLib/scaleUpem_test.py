from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
import difflib
import os
import shutil
import sys
import tempfile
import unittest
import pytest


class ScaleUpemTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def get_path(test_file_or_folder):
        parent_dir = os.path.dirname(__file__)
        return os.path.join(parent_dir, "data", test_file_or_folder)

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

    def test_scale_upem_ttf(self):
        font = TTFont(self.get_path("I.ttf"))
        tables = [table_tag for table_tag in font.keys() if table_tag != "head"]

        scale_upem(font, 512)

        expected_ttx_path = self.get_path("I-512upem.ttx")
        self.expect_ttx(font, expected_ttx_path, tables)

    def test_scale_upem_varComposite(self):
        font = TTFont(self.get_path("varc-ac00-ac01.ttf"))
        tables = [table_tag for table_tag in font.keys() if table_tag != "head"]

        scale_upem(font, 500)

        expected_ttx_path = self.get_path("varc-ac00-ac01-500upem.ttx")
        self.expect_ttx(font, expected_ttx_path, tables)

        # Scale our other varComposite font as well; without checking the expected
        font = TTFont(self.get_path("varc-6868.ttf"))
        scale_upem(font, 500)

    def test_scale_upem_otf(self):
        # Just test that it doesn't crash

        font = TTFont(self.get_path("TestVGID-Regular.otf"))

        scale_upem(font, 500)
