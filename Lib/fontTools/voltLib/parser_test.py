from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.voltLib.error import VoltLibError
from fontTools.voltLib.parser import Parser
import codecs
import os
import shutil
import tempfile
import unittest


class ParserTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_def_glyph(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH ".notdef" ID 0 TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         (".notdef", 0, None, "BASE", None))
        [def_glyph] = self.parse(
            'DEF_GLYPH "space" ID 3 UNICODE 32 TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("space", 3, [0x0020], "BASE", None))
        [def_glyph] = self.parse(
            'DEF_GLYPH "CR" ID 2 UNICODEVALUES "U+0009,U+000D" '
            'TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("CR", 2, [0x0009, 0x000D], "BASE", None))
        [def_glyph] = self.parse(
            'DEF_GLYPH "f_f" ID 320 TYPE LIGATURE COMPONENTS 2 END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("f_f", 320, None, "LIGATURE", 2))
        [def_glyph] = self.parse(
            'DEF_GLYPH "glyph20" ID 20 END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("glyph20", 20, None, None, None))

    def test_def_group(self):
        [def_group] = self.parse(
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM GLYPH "a" GLYPH "aacute" GLYPH "abreve" GLYPH "acircumflex" '
            'GLYPH "adieresis" GLYPH "ae" GLYPH "agrave" GLYPH "amacron" '
            'GLYPH "aogonek" GLYPH "aring" GLYPH "atilde" END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("KERN_lc_a_2ND",
                          {"glyphs": ["a", "aacute", "abreve", "acircumflex",
                                      "adieresis", "ae", "agrave", "amacron",
                                      "aogonek", "aring", "atilde"],
                           "groups": [],
                           "ranges": []}))
        [def_group] = self.parse(
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM GLYPH "a" GROUP "aaccented" END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("KERN_lc_a_2ND",
                          {"glyphs": ["a"],
                           "groups": ["aaccented"],
                           "ranges": []}))
        [def_group] = self.parse(
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM RANGE "a" "atilde" GLYPH "b" RANGE "c" "cdotaccent" '
            'END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("KERN_lc_a_2ND",
                          {"glyphs": ["b"],
                           "groups": [],
                           "ranges": [("a", "atilde"),
                                      ("c", "cdotaccent")]}))

    def test_group_duplicate(self):
        self.assertRaisesRegex(
            VoltLibError, 'Glyph group "dup" already defined',
            self.parse, 'DEF_GROUP "dup"\n'
                        'ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
                        'END_GROUP\n'
                        'DEF_GROUP "dup"\n'
                        'ENUM GLYPH "x" END_ENUM\n'
                        'END_GROUP\n'
        )

    def test_langsys(self):
        [def_script] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        self.assertEqual((def_script.name, def_script.tag),
                         ("Latin",
                          "latn"))
        def_lang = def_script.langs[0]
        self.assertEqual((def_lang.name, def_lang.tag),
                         ("Romanian",
                          "ROM "))

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
        path = os.path.join(self.tempdir, "tmp%d.vtp" % self.num_tempfiles)
        with codecs.open(path, "wb", "utf-8") as outfile:
            outfile.write(text)
        return Parser(path).parse()

if __name__ == "__main__":
    unittest.main()
