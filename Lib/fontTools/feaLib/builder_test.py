from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.builder import Builder, addOpenTypeFeatures
from fontTools.feaLib.error import FeatureLibError
from fontTools.ttLib import TTFont
import codecs
import difflib
import os
import shutil
import sys
import tempfile
import unittest


class BuilderTest(unittest.TestCase):
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
        return os.path.join(path, "testdata", testfile)

    def temp_path(self, suffix):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir,
                            "tmp%d%s" % (self.num_tempfiles, suffix))

    def read_ttx(self, path):
        lines = []
        with codecs.open(path, "r", "utf-8") as ttx:
            for line in ttx.readlines():
                # Elide ttFont attributes because ttLibVersion may change,
                # and use os-native line separators so we can run difflib.
                if line.startswith("<ttFont "):
                    lines.append("<ttFont>" + os.linesep)
                else:
                    lines.append(line.rstrip() + os.linesep)
        return lines

    def expect_ttx(self, font, expected_ttx):
        path = self.temp_path(suffix=".ttx")
        font.saveXML(path, quiet=True, tables=['GSUB', 'GPOS'])
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                    expected, actual, fromfile=path, tofile=expected_ttx):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def build(self, featureFile):
        path = self.temp_path(suffix=".fea")
        with codecs.open(path, "wb", "utf-8") as outfile:
            outfile.write(featureFile)
        font = TTFont()
        addOpenTypeFeatures(path, font)
        return font

    def test_spec4h1(self):
        # OpenType Feature File specification, section 4.h, example 1.
        font = TTFont()
        addOpenTypeFeatures(self.getpath("spec4h1.fea"), font)
        self.expect_ttx(font, self.getpath("spec4h1_expected.ttx"))

    def test_languagesystem(self):
        builder = Builder(None, TTFont())
        builder.add_language_system(None, 'latn', 'FRA')
        builder.add_language_system(None, 'cyrl', 'RUS')
        builder.start_feature(location=None, name='test')
        self.assertEqual(builder.language_systems,
                         {('latn', 'FRA'), ('cyrl', 'RUS')})

    def test_languagesystem_none_specified(self):
        builder = Builder(None, TTFont())
        builder.start_feature(location=None, name='test')
        self.assertEqual(builder.language_systems, {('DFLT', 'dflt')})

    def test_languagesystem_DFLT_dflt_not_first(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "If \"languagesystem DFLT dflt\" is present, "
            "it must be the first of the languagesystem statements",
            self.build, "languagesystem latn TRK; languagesystem DFLT dflt;")

    def test_script(self):
        builder = Builder(None, TTFont())
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        self.assertEqual(builder.language_systems,
                         {('DFLT', 'dflt'), ('cyrl', 'dflt')})

    def test_language(self):
        builder = Builder(None, TTFont())
        builder.add_language_system(None, 'latn', 'FRA')
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        builder.set_language(location=None, language='RUS',
                             include_default=False)
        self.assertEqual(builder.language_systems, {('cyrl', 'RUS')})
        builder.set_language(location=None, language='BGR',
                             include_default=True)
        self.assertEqual(builder.language_systems,
                         {('latn', 'FRA'), ('cyrl', 'BGR')})


if __name__ == "__main__":
    unittest.main()
