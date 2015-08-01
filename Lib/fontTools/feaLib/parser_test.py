from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.lexer import LexerError
from fontTools.feaLib.parser import Parser, ParserError
from fontTools.misc.py23 import *
import codecs
import os
import shutil
import sys
import tempfile
import unittest


class ParserTest(unittest.TestCase):
    def test_languagesystem(self):
        langsys = self.parse("languagesystem latn DEU;").language_system
        self.assertEqual(langsys, {"latn": {"DEU "}})
        self.assertRaisesRegexp(
            ParserError, "Expected ';'",
            self.parse, "languagesystem latn DEU")
        self.assertRaisesRegexp(
            ParserError, "longer than 4 characters",
            self.parse, "languagesystem foobar DEU")
        self.assertRaisesRegexp(
            ParserError, "longer than 4 characters",
            self.parse, "languagesystem latn FOOBAR")

    def test_roundtrip(self):
        self.roundtrip("mini.fea")

    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    def parse(self, text):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()
        self.num_tempfiles += 1
        path = os.path.join(self.tempdir, "tmp%d.fea" % self.num_tempfiles)
        with codecs.open(path, "wb", "utf-8") as outfile:
            outfile.write(text)
        return Parser(path).parse()

    def roundtrip(self, testfile):
        buffer1, buffer2 = StringIO(), StringIO()
        Parser(ParserTest.getpath(testfile)).parse().write(buffer1)
        text1 = buffer1.getvalue().decode("utf-8")
        self.parse(text1).write(buffer2)
        text2 = buffer2.getvalue().decode("utf-8")
        self.assertEqual(text1, text2)

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", testfile)


if __name__ == "__main__":
    unittest.main()
