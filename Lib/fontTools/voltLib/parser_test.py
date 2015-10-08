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

    def test_def_group_glyphs(self):
        [def_group] = self.parse(
            'DEF_GROUP "aaccented"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" GLYPH "acircumflex" '
            'GLYPH "adieresis" GLYPH "ae" GLYPH "agrave" GLYPH "amacron" '
            'GLYPH "aogonek" GLYPH "aring" GLYPH "atilde" END_ENUM\n'
            'END_GROUP\n'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("aaccented",
                          ["aacute", "abreve", "acircumflex", "adieresis",
                           "ae", "agrave", "amacron", "aogonek", "aring",
                           "atilde"]))

    def test_def_group_glyphs_and_group(self):
        [def_group1, def_group2] = self.parse(
            'DEF_GROUP "aaccented"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" GLYPH "acircumflex" '
            'GLYPH "adieresis" GLYPH "ae" GLYPH "agrave" GLYPH "amacron" '
            'GLYPH "aogonek" GLYPH "aring" GLYPH "atilde" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM GLYPH "a" GROUP "aaccented" END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group2.name, def_group2.enum),
                         ("KERN_lc_a_2ND",
                          ["a", "aacute", "abreve", "acircumflex", "adieresis",
                           "ae", "agrave", "amacron", "aogonek", "aring",
                           "atilde"]))

    def test_def_group_range(self):
        [def_group] = self.parse(
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM RANGE "a" "atilde" GLYPH "b" RANGE "c" "cdotaccent" '
            'END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("KERN_lc_a_2ND",
                          [("a", "atilde"), "b", ("c", "cdotaccent")]))

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

    def test_feature(self):
        [def_script] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'DEF_FEATURE NAME "Fractions" TAG "frac"\n'
            'LOOKUP "fraclookup"\n'
            'END_FEATURE\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        def_feature = def_script.langs[0].features[0]
        self.assertEqual((def_feature.name, def_feature.tag,
                          def_feature.lookups),
                         ("Fractions",
                          "frac",
                          ["fraclookup"]))
        [def_script] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'DEF_FEATURE NAME "Kerning" TAG "kern"\n'
            'LOOKUP "kern1" LOOKUP "kern2"\n'
            'END_FEATURE\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        def_feature = def_script.langs[0].features[0]
        self.assertEqual((def_feature.name, def_feature.tag,
                          def_feature.lookups),
                         ("Kerning",
                          "kern",
                          ["kern1", "kern2"]))

    def test_substitution_single(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "smcp" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "a"\n'
            'WITH GLYPH "a.sc"\n'
            'END_SUB\n'
            'SUB GLYPH "b"\n'
            'WITH GLYPH "b.sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual((lookup.name, list(lookup.sub.mapping)),
                         ("smcp", [("a", "a.sc"), ("b", "b.sc")]))

    def test_substitution_single_in_context(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "Denominators" ENUM GLYPH "one.dnom" GLYPH "two.dnom" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "fracdnom" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT LEFT ENUM GROUP "Denominators" GLYPH "fraction" '
            'END_ENUM\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "one"\n'
            'WITH GLYPH "one.dnom"\n'
            'END_SUB\n'
            'SUB GLYPH "two"\n'
            'WITH GLYPH "two.dnom"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        context = lookup.context[0]
        self.assertEqual((lookup.name, list(lookup.sub.mapping), context.ex_or_in,
                          context.left, context.right),
                         ("fracdnom",
                          [("one", "one.dnom"), ("two", "two.dnom")],
                          "IN_CONTEXT",
                          [[["one.dnom", "two.dnom", "fraction"]]],
                          []))

    def test_substitution_single_in_contexts(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "Hebrew" ENUM GLYPH "uni05D0" GLYPH "uni05D1" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "HebrewCurrency" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'RIGHT GROUP "Hebrew"\n'
            'RIGHT GLYPH "one.Hebr"\n'
            'END_CONTEXT\n'
            'IN_CONTEXT\n'
            'LEFT GROUP "Hebrew"\n'
            'LEFT GLYPH "one.Hebr"\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "dollar"\n'
            'WITH GLYPH "dollar.Hebr"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        context1 = lookup.context[0]
        context2 = lookup.context[1]
        self.assertEqual((lookup.name, context1.ex_or_in, context1.left,
                          context1.right, context2.ex_or_in, context2.left,
                          context2.right),
                         ("HebrewCurrency",
                          "IN_CONTEXT",
                          [],
                          [["uni05D0", "uni05D1"], ["one.Hebr"]],
                          "IN_CONTEXT",
                          [["uni05D0", "uni05D1"], ["one.Hebr"]],
                          []))

    def test_def_attach(self):
        [lookup, anchor1, anchor2, anchor3, anchor4] = self.parse(
            'DEF_LOOKUP "anchor_top" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION RTL\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_POSITION\n'
            'ATTACH GLYPH "a" GLYPH "e"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top" '
            'GLYPH "gravecomb" AT ANCHOR "top"\n'
            'END_ATTACH\n'
            'END_POSITION\n'
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb COMPONENT 1 '
            'AT POS DX 0 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "MARK_top" ON 121 GLYPH gravecomb COMPONENT 1 '
            'AT POS DX 0 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "top" ON 31 GLYPH a COMPONENT 1 '
            'AT POS DX 210 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "top" ON 35 GLYPH e COMPONENT 1 '
            'AT POS DX 215 DY 450 END_POS END_ANCHOR\n'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.pos.coverage, lookup.pos.coverage_to),
            ("anchor_top", ["a", "e"], [(["acutecomb"], "top"),
                                        (["gravecomb"], "top")])
        )
        self.assertEqual(
            (anchor1.name, anchor1.gid, anchor1.glyph_name, anchor1.component,
             anchor1.locked, anchor1.pos),
            ("MARK_top", 120, "acutecomb", 1, False, (None, 0, 450, {}, {},
             {}))
        )
        self.assertEqual(
            (anchor2.name, anchor2.gid, anchor2.glyph_name, anchor2.component,
             anchor2.locked, anchor2.pos),
            ("MARK_top", 121, "gravecomb", 1, False, (None, 0, 450, {}, {},
             {}))
        )
        self.assertEqual(
            (anchor3.name, anchor3.gid, anchor3.glyph_name, anchor3.component,
             anchor3.locked, anchor3.pos),
            ("top", 31, "a", 1, False, (None, 210, 450, {}, {}, {}))
        )
        self.assertEqual(
            (anchor4.name, anchor4.gid, anchor4.glyph_name, anchor4.component,
             anchor4.locked, anchor4.pos),
            ("top", 35, "e", 1, False, (None, 215, 450, {}, {}, {}))
        )

    def test_adjust_pair(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "kern1" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION RTL\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_POSITION\n'
            'ADJUST_PAIR\n'
            ' FIRST GLYPH "A"\n'
            ' SECOND GLYPH "V"\n'
            ' 1 2 BY POS ADV -30 END_POS POS END_POS\n'
            ' 2 1 BY POS ADV -30 END_POS POS END_POS\n'
            'END_ADJUST\n'
            'END_POSITION\n'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.pos.coverages_1, lookup.pos.coverages_2,
             lookup.pos.adjust),
            ("kern1", [["A"]], [["V"]],
             {(1, 2): ((-30, None, None, {}, {}, {}),
                       (None, None, None, {}, {}, {})),
              (2, 1): ((-30, None, None, {}, {}, {}),
                       (None, None, None, {}, {}, {}))})
        )

    def test_def_anchor(self):
        [anchor] = self.parse(
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb COMPONENT 1 AT POS DX 0 DY 450 END_POS END_ANCHOR'
        ).statements
        self.assertEqual(
            (anchor.name, anchor.gid, anchor.glyph_name, anchor.component,
             anchor.locked, anchor.pos),
            ("MARK_top", 120, "acutecomb", 1, False, (None, 0, 450, {}, {},
                                                      {}))
        )

    def test_ppem(self):
        [grid_ppem, pres_ppem, ppos_ppem] = self.parse(
            'GRID_PPEM 20\n'
            'PRESENTATION_PPEM 72\n'
            'PPOSITIONING_PPEM 144\n'
        ).statements
        self.assertEqual(
            ((grid_ppem.name, grid_ppem.value),
             (pres_ppem.name, pres_ppem.value),
             (ppos_ppem.name, ppos_ppem.value)),
            (("GRID_PPEM", 20), ("PRESENTATION_PPEM", 72),
             ("PPOSITIONING_PPEM", 144))
        )

    def test_compiler_flags(self):
        [setting1, setting2] = self.parse(
            'COMPILER_USEEXTENSIONLOOKUPS\n'
            'COMPILER_USEPAIRPOSFORMAT2\n'
        ).statements
        self.assertEqual(
            ((setting1.name, setting1.value),
             (setting2.name, setting2.value)),
            (("COMPILER_USEEXTENSIONLOOKUPS", True),
             ("COMPILER_USEPAIRPOSFORMAT2", True))
        )

    def test_cmap(self):
        [cmap_format1, cmap_format2, cmap_format3] = self.parse(
            'CMAP_FORMAT 0 3 4\n'
            'CMAP_FORMAT 1 0 6\n'
            'CMAP_FORMAT 3 1 4\n'
        ).statements
        self.assertEqual(
            ((cmap_format1.name, cmap_format1.value),
             (cmap_format2.name, cmap_format2.value),
             (cmap_format3.name, cmap_format3.value)),
            (("CMAP_FORMAT", (0, 3, 4)),
             ("CMAP_FORMAT", (1, 0, 6)),
             ("CMAP_FORMAT", (3, 1, 4)))
        )

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
