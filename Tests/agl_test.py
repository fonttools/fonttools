# -*- coding: utf-8 -*-
from __future__ import (print_function, division, absolute_import,
                        unicode_literals)
from fontTools.misc.py23 import *
from fontTools import agl
import unittest


class AglToUnicodeTest(unittest.TestCase):
    def test_spec_examples(self):
        # https://github.com/adobe-type-tools/agl-specification#3-examples
        #
        # TODO: Currently, we only handle AGLFN instead of legacy AGL names.
        # Therefore, the test cases below use Iogonek instead of Lcommaaccent.
        # Change Iogonek to Lcommaaccent as soon as the implementation has
        # been fixed to also support legacy AGL names.
        # https://github.com/fonttools/fonttools/issues/775
        self.assertEqual(agl.toUnicode("Iogonek"), "Į")
        self.assertEqual(agl.toUnicode("uni20AC0308"), "\u20AC\u0308")
        self.assertEqual(agl.toUnicode("u1040C"), "\U0001040C")
        self.assertEqual(agl.toUnicode("uniD801DC0C"), "")
        self.assertEqual(agl.toUnicode("uni20ac"), "")
        self.assertEqual(
            agl.toUnicode("Iogonek_uni20AC0308_u1040C.alternate"),
            "\u012E\u20AC\u0308\U0001040C")
        self.assertEqual(agl.toUnicode("Iogonek_uni012E_u012E"), "ĮĮĮ")
        self.assertEqual(agl.toUnicode("foo"), "")
        self.assertEqual(agl.toUnicode(".notdef"), "")

    def test_aglfn(self):
        self.assertEqual(agl.toUnicode("longs_t"), "ſt")
        self.assertEqual(agl.toUnicode("f_f_i.alt123"), "ffi")

    def test_uniABCD(self):
        self.assertEqual(agl.toUnicode("uni0041"), "A")
        self.assertEqual(agl.toUnicode("uni0041_uni0042_uni0043"), "ABC")
        self.assertEqual(agl.toUnicode("uni004100420043"), "ABC")
        self.assertEqual(agl.toUnicode("uni"), "")
        self.assertEqual(agl.toUnicode("uni41"), "")
        self.assertEqual(agl.toUnicode("uni004101"), "")
        self.assertEqual(agl.toUnicode("uniDC00"), "")

    def test_uABCD(self):
        self.assertEqual(agl.toUnicode("u0041"), "A")
        self.assertEqual(agl.toUnicode("u00041"), "A")
        self.assertEqual(agl.toUnicode("u000041"), "A")
        self.assertEqual(agl.toUnicode("u0000041"), "")
        self.assertEqual(agl.toUnicode("u0041_uni0041_A.alt"), "AAA")

    def test_union(self):
        # Interesting test case because "uni" is a prefix of "union".
        self.assertEqual(agl.toUnicode("union"), "∪")
        # U+222A U+FE00 is a Standardized Variant for UNION WITH SERIFS.
        self.assertEqual(agl.toUnicode("union_uniFE00"), "\u222A\uFE00")

    def test_dingbats(self):
        self.assertEqual(agl.toUnicode("a20", isZapfDingbats=True), "✔")
        self.assertEqual(agl.toUnicode("a20.alt", isZapfDingbats=True), "✔")
        self.assertEqual(agl.toUnicode("a206", isZapfDingbats=True), "❰")
        self.assertEqual(agl.toUnicode("a20", isZapfDingbats=False), "")
        self.assertEqual(agl.toUnicode("a0", isZapfDingbats=True), "")
        self.assertEqual(agl.toUnicode("a207", isZapfDingbats=True), "")
        self.assertEqual(agl.toUnicode("abcdef", isZapfDingbats=True), "")


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
