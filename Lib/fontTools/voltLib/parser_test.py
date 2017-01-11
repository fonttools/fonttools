from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.voltLib.error import VoltLibError
from fontTools.voltLib.parser import Parser
from io import open
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

    def test_def_glyph_base(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH ".notdef" ID 0 TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         (".notdef", 0, None, "BASE", None))

    def test_def_glyph_base_with_unicode(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "space" ID 3 UNICODE 32 TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("space", 3, [0x0020], "BASE", None))

    def test_def_glyph_base_with_unicodevalues(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "CR" ID 2 UNICODEVALUES "U+0009" '
            'TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("CR", 2, [0x0009], "BASE", None))

    def test_def_glyph_base_with_mult_unicodevalues(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "CR" ID 2 UNICODEVALUES "U+0009,U+000D" '
            'TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("CR", 2, [0x0009, 0x000D], "BASE", None))

    def test_def_glyph_base_with_empty_unicodevalues(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "i.locl" ID 269 UNICODEVALUES "" '
            'TYPE BASE END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("i.locl", 269, None, "BASE", None))

    def test_def_glyph_base_2_components(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "glyphBase" ID 320 TYPE BASE COMPONENTS 2 END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("glyphBase", 320, None, "BASE", 2))

    def test_def_glyph_ligature_2_components(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "f_f" ID 320 TYPE LIGATURE COMPONENTS 2 END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("f_f", 320, None, "LIGATURE", 2))

    def test_def_glyph_no_type(self):
        [def_glyph] = self.parse(
            'DEF_GLYPH "glyph20" ID 20 END_GLYPH'
        ).statements
        self.assertEqual((def_glyph.name, def_glyph.id, def_glyph.unicode,
                          def_glyph.type, def_glyph.components),
                         ("glyph20", 20, None, None, None))

    def test_def_glyph_case_sensitive(self):
        def_glyphs = self.parse(
            'DEF_GLYPH "A" ID 3 UNICODE 65 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "a" ID 4 UNICODE 97 TYPE BASE END_GLYPH\n'
        ).statements
        self.assertEqual((def_glyphs[0].name, def_glyphs[0].id,
                          def_glyphs[0].unicode, def_glyphs[0].type,
                          def_glyphs[0].components),
                         ("A", 3, [0x41], "BASE", None))
        self.assertEqual((def_glyphs[1].name, def_glyphs[1].id,
                          def_glyphs[1].unicode, def_glyphs[1].type,
                          def_glyphs[1].components),
                         ("a", 4, [0x61], "BASE", None))

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
                          ("aacute", "abreve", "acircumflex", "adieresis",
                           "ae", "agrave", "amacron", "aogonek", "aring",
                           "atilde")))

    def test_def_group_groups(self):
        [group1, group2, test_group] = self.parse(
            'DEF_GROUP "Group1"\n'
            'ENUM GLYPH "a" GLYPH "b" GLYPH "c" GLYPH "d" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "Group2"\n'
            'ENUM GLYPH "e" GLYPH "f" GLYPH "g" GLYPH "h" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "TestGroup"\n'
            'ENUM GROUP "Group1" GROUP "Group2" END_ENUM\n'
            'END_GROUP\n'
        ).statements
        self.assertEqual(
            (test_group.name, test_group.enum),
            ("TestGroup",
             (("Group1",), ("Group2",))))

    def test_def_group_groups_not_yet_defined(self):
        [group1, test_group1, test_group2, test_group3, group2] = self.parse(
            'DEF_GROUP "Group1"\n'
            'ENUM GLYPH "a" GLYPH "b" GLYPH "c" GLYPH "d" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "TestGroup1"\n'
            'ENUM GROUP "Group1" GROUP "Group2" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "TestGroup2"\n'
            'ENUM GROUP "Group2" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "TestGroup3"\n'
            'ENUM GROUP "Group2" GROUP "Group1" END_ENUM\n'
            'END_GROUP\n'
            'DEF_GROUP "Group2"\n'
            'ENUM GLYPH "e" GLYPH "f" GLYPH "g" GLYPH "h" END_ENUM\n'
            'END_GROUP\n'
        ).statements
        self.assertEqual(
            (test_group1.name, test_group1.enum),
            ("TestGroup1",
             (("Group1", ), ("Group2", ))))
        self.assertEqual(
            (test_group2.name, test_group2.enum),
            ("TestGroup2",
             (("Group2", ), )))
        self.assertEqual(
            (test_group3.name, test_group3.enum),
            ("TestGroup3",
             (("Group2", ), ("Group1", ))))

    # def test_def_group_groups_undefined(self):
    #     with self.assertRaisesRegex(
    #             VoltLibError,
    #             r'Group "Group2" is used but undefined.'):
    #         [group1, test_group, group2] = self.parse(
    #             'DEF_GROUP "Group1"\n'
    #             'ENUM GLYPH "a" GLYPH "b" GLYPH "c" GLYPH "d" END_ENUM\n'
    #             'END_GROUP\n'
    #             'DEF_GROUP "TestGroup"\n'
    #             'ENUM GROUP "Group1" GROUP "Group2" END_ENUM\n'
    #             'END_GROUP\n'
    #         ).statements

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
                          ("a", ("aaccented", ))))

    def test_def_group_range(self):
        [def_group] = self.parse(
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM RANGE "a" TO "atilde" GLYPH "b" RANGE "c" TO "cdotaccent" '
            'END_ENUM\n'
            'END_GROUP'
        ).statements
        self.assertEqual((def_group.name, def_group.enum),
                         ("KERN_lc_a_2ND",
                          (("a", "atilde"), "b", ("c", "cdotaccent"))))

    def test_group_duplicate(self):
        self.assertRaisesRegex(
            VoltLibError,
            'Glyph group "dupe" already defined, '
            'group names are case insensitive',
            self.parse, 'DEF_GROUP "dupe"\n'
                        'ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
                        'END_GROUP\n'
                        'DEF_GROUP "dupe"\n'
                        'ENUM GLYPH "x" END_ENUM\n'
                        'END_GROUP\n'
        )

    def test_group_duplicate_case_insensitive(self):
        self.assertRaisesRegex(
            VoltLibError,
            'Glyph group "Dupe" already defined, '
            'group names are case insensitive',
            self.parse, 'DEF_GROUP "dupe"\n'
                        'ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
                        'END_GROUP\n'
                        'DEF_GROUP "Dupe"\n'
                        'ENUM GLYPH "x" END_ENUM\n'
                        'END_GROUP\n'
        )

    def test_script_without_langsys(self):
        [script] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'END_SCRIPT'
        ).statements
        self.assertEqual((script.name, script.tag, script.langs),
                         ("Latin", "latn", []))

    def test_langsys_normal(self):
        [def_script] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'END_LANGSYS\n'
            'DEF_LANGSYS NAME "Moldavian" TAG "MOL "\n'
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
        def_lang = def_script.langs[1]
        self.assertEqual((def_lang.name, def_lang.tag),
                         ("Moldavian",
                          "MOL "))

    def test_langsys_no_script_name(self):
        [langsys] = self.parse(
            'DEF_SCRIPT TAG "latn"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        self.assertEqual((langsys.name, langsys.tag),
                         (None,
                          "latn"))
        lang = langsys.langs[0]
        self.assertEqual((lang.name, lang.tag),
                         ("Default",
                          "dflt"))

    def test_langsys_no_script_tag_fails(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'.*Expected "TAG"'):
            [langsys] = self.parse(
                'DEF_SCRIPT NAME "Latin"\n'
                'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
                'END_LANGSYS\n'
                'END_SCRIPT'
            ).statements

    def test_langsys_duplicate_script(self):
        with self.assertRaisesRegex(
                VoltLibError,
                'Script "DFLT" already defined, '
                'script tags are case insensitive'):
            [langsys1, langsys2] = self.parse(
                'DEF_SCRIPT NAME "Default" TAG "DFLT"\n'
                'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
                'END_LANGSYS\n'
                'END_SCRIPT\n'
                'DEF_SCRIPT TAG "DFLT"\n'
                'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
                'END_LANGSYS\n'
                'END_SCRIPT'
            ).statements

    def test_langsys_duplicate_lang(self):
        with self.assertRaisesRegex(
                VoltLibError,
                'Language "dflt" already defined in script "DFLT", '
                'language tags are case insensitive'):
            [langsys] = self.parse(
                'DEF_SCRIPT NAME "Default" TAG "DFLT"\n'
                'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
                'END_LANGSYS\n'
                'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
                'END_LANGSYS\n'
                'END_SCRIPT\n'
            ).statements

    def test_langsys_lang_in_separate_scripts(self):
        [langsys1, langsys2] = self.parse(
            'DEF_SCRIPT NAME "Default" TAG "DFLT"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            'END_LANGSYS\n'
            'DEF_LANGSYS NAME "Default" TAG "ROM "\n'
            'END_LANGSYS\n'
            'END_SCRIPT\n'
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            'END_LANGSYS\n'
            'DEF_LANGSYS NAME "Default" TAG "ROM "\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        self.assertEqual((langsys1.langs[0].tag, langsys1.langs[1].tag),
                         ("dflt", "ROM "))
        self.assertEqual((langsys2.langs[0].tag, langsys2.langs[1].tag),
                         ("dflt", "ROM "))

    def test_langsys_no_lang_name(self):
        [langsys] = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS TAG "dflt"\n'
            'END_LANGSYS\n'
            'END_SCRIPT'
        ).statements
        self.assertEqual((langsys.name, langsys.tag),
                         ("Latin",
                          "latn"))
        lang = langsys.langs[0]
        self.assertEqual((lang.name, lang.tag),
                         (None,
                          "dflt"))

    def test_langsys_no_langsys_tag_fails(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'.*Expected "TAG"'):
            [langsys] = self.parse(
                'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
                'DEF_LANGSYS NAME "Default"\n'
                'END_LANGSYS\n'
                'END_SCRIPT'
            ).statements

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

    def test_lookup_duplicate(self):
        with self.assertRaisesRegex(
            VoltLibError,
            'Lookup "dupe" already defined, '
            'lookup names are case insensitive',
        ):
            [lookup1, lookup2] = self.parse(
                'DEF_LOOKUP "dupe"\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "a"\n'
                'WITH GLYPH "a.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION\n'
                'DEF_LOOKUP "dupe"\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "b"\n'
                'WITH GLYPH "b.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION\n'
            ).statements

    def test_lookup_duplicate_insensitive_case(self):
        with self.assertRaisesRegex(
            VoltLibError,
            'Lookup "Dupe" already defined, '
            'lookup names are case insensitive',
        ):
            [lookup1, lookup2] = self.parse(
                'DEF_LOOKUP "dupe"\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "a"\n'
                'WITH GLYPH "a.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION\n'
                'DEF_LOOKUP "Dupe"\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "b"\n'
                'WITH GLYPH "b.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION\n'
            ).statements

    def test_lookup_name_starts_with_letter(self):
        with self.assertRaisesRegex(
            VoltLibError,
            'Lookup name "\\\lookupname" must start with a letter'
        ):
            [lookup] = self.parse(
                'DEF_LOOKUP "\lookupname"\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "a"\n'
                'WITH GLYPH "a.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION\n'
            ).statements

    def test_substitution_empty(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'Expected SUB'):
            [lookup] = self.parse(
                'DEF_LOOKUP "empty_substitution" PROCESS_BASE PROCESS_MARKS '
                'ALL DIRECTION LTR\n'
                'IN_CONTEXT\n'
                'END_CONTEXT\n'
                'AS_SUBSTITUTION\n'
                'END_SUBSTITUTION'
            ).statements

    def test_substitution_invalid_many_to_many(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'Invalid substitution type'):
            [lookup] = self.parse(
                'DEF_LOOKUP "invalid_substitution" PROCESS_BASE PROCESS_MARKS '
                'ALL DIRECTION LTR\n'
                'IN_CONTEXT\n'
                'END_CONTEXT\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "f" GLYPH "i"\n'
                'WITH GLYPH "f.alt" GLYPH "i.alt"\n'
                'END_SUB\n'
                'END_SUBSTITUTION'
            ).statements

    def test_substitution_invalid_reverse_chaining_single(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'Invalid substitution type'):
            [lookup] = self.parse(
                'DEF_LOOKUP "invalid_substitution" PROCESS_BASE PROCESS_MARKS '
                'ALL DIRECTION LTR REVERSAL\n'
                'IN_CONTEXT\n'
                'END_CONTEXT\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "f" GLYPH "i"\n'
                'WITH GLYPH "f_i"\n'
                'END_SUB\n'
                'END_SUBSTITUTION'
            ).statements

    def test_substitution_invalid_mixed(self):
        with self.assertRaisesRegex(
                VoltLibError,
                r'Invalid substitution type'):
            [lookup] = self.parse(
                'DEF_LOOKUP "invalid_substitution" PROCESS_BASE PROCESS_MARKS '
                'ALL DIRECTION LTR\n'
                'IN_CONTEXT\n'
                'END_CONTEXT\n'
                'AS_SUBSTITUTION\n'
                'SUB GLYPH "fi"\n'
                'WITH GLYPH "f" GLYPH "i"\n'
                'END_SUB\n'
                'SUB GLYPH "f" GLYPH "l"\n'
                'WITH GLYPH "f_l"\n'
                'END_SUB\n'
                'END_SUBSTITUTION'
            ).statements

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
        self.assertEqual((lookup.name, list(lookup.sub.mapping.items())),
                         ("smcp", [(("a",), ("a.sc",)), (("b",), ("b.sc",))]))

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
        self.assertEqual(
            (lookup.name, list(lookup.sub.mapping.items()),
             context.ex_or_in, context.left, context.right),
            ("fracdnom", [(("one",), ("one.dnom",)), (("two",), ("two.dnom",))],
             "IN_CONTEXT", [((("Denominators",), "fraction"),)], [])
        )

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
        self.assertEqual(
            (lookup.name, context1.ex_or_in, context1.left,
             context1.right, context2.ex_or_in,
             context2.left, context2.right),
            ("HebrewCurrency", "IN_CONTEXT", [],
             [(("Hebrew",),), ("one.Hebr",)], "IN_CONTEXT",
             [(("Hebrew",),), ("one.Hebr",)], []))

    def test_substitution_skip_base(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "SomeSub" SKIP_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        process_base = lookup.process_base
        self.assertEqual(
            (lookup.name, process_base),
            ("SomeSub", False))

    def test_substitution_process_base(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "SomeSub" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        process_base = lookup.process_base
        self.assertEqual(
            (lookup.name, process_base),
            ("SomeSub", True))

    def test_substitution_skip_marks(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "SomeSub" PROCESS_BASE SKIP_MARKS '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        process_marks = lookup.process_marks
        self.assertEqual(
            (lookup.name, process_marks),
            ("SomeSub", False))

    def test_substitution_process_marks(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "acutecmb" GLYPH "gravecmb" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "SomeSub" PROCESS_BASE '
            'PROCESS_MARKS "SomeMarks" \n'
            'DIRECTION RTL\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        process_marks = lookup.process_marks
        self.assertEqual(
            (lookup.name, process_marks),
            ("SomeSub", "SomeMarks"))

    def test_substitution_process_all_marks(self):
        [group, lookup] = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "acutecmb" GLYPH "gravecmb" '
            'END_ENUM END_GROUP\n'
            'DEF_LOOKUP "SomeSub" PROCESS_BASE '
            'PROCESS_MARKS ALL \n'
            'DIRECTION RTL\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        process_marks = lookup.process_marks
        self.assertEqual(
            (lookup.name, process_marks),
            ("SomeSub", True))

    def test_substitution_no_reversal(self):
        # TODO: check right context with no reversal
        [lookup] = self.parse(
            'DEF_LOOKUP "Lookup" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'RIGHT ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "a"\n'
            'WITH GLYPH "a.alt"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.reversal),
            ("Lookup", None)
        )

    def test_substitution_reversal(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "RevLookup" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR REVERSAL\n'
            'IN_CONTEXT\n'
            'RIGHT ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GROUP "DFLT_Num_standardFigures"\n'
            'WITH GROUP "DFLT_Num_numerators"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.reversal),
            ("RevLookup", True)
        )

    def test_substitution_single_to_multiple(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "ccmp" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "aacute"\n'
            'WITH GLYPH "a" GLYPH "acutecomb"\n'
            'END_SUB\n'
            'SUB GLYPH "agrave"\n'
            'WITH GLYPH "a" GLYPH "gravecomb"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual((lookup.name, list(lookup.sub.mapping.items())),
                         ("ccmp",
                          [(("aacute",), ("a", "acutecomb")),
                           (("agrave",), ("a", "gravecomb"))]
                          ))

    def test_substitution_multiple_to_single(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "liga" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB GLYPH "f" GLYPH "i"\n'
            'WITH GLYPH "f_i"\n'
            'END_SUB\n'
            'SUB GLYPH "f" GLYPH "t"\n'
            'WITH GLYPH "f_t"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual((lookup.name, list(lookup.sub.mapping.items())),
                         ("liga",
                          [(("f", "i"), ("f_i",)),
                           (("f", "t"), ("f_t",))]))

    def test_substitution_reverse_chaining_single(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "numr" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR REVERSAL\n'
            'IN_CONTEXT\n'
            'RIGHT ENUM '
            'GLYPH "fraction" '
            'RANGE "zero.numr" TO "nine.numr" '
            'END_ENUM\n'
            'END_CONTEXT\n'
            'AS_SUBSTITUTION\n'
            'SUB RANGE "zero" TO "nine"\n'
            'WITH RANGE "zero.numr" TO "nine.numr"\n'
            'END_SUB\n'
            'END_SUBSTITUTION'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.context[0].right,
             list(lookup.sub.mapping.items())),
            ("numr", [(("fraction", ("zero.numr", "nine.numr")),)],
             [((("zero", "nine"),), (("zero.numr", "nine.numr"),))]))

    # GPOS
    #  ATTACH_CURSIVE
    #  ATTACH
    #  ADJUST_PAIR
    #  ADJUST_SINGLE
    def test_position_empty(self):
        with self.assertRaisesRegex(
                VoltLibError,
                'Expected ATTACH, ATTACH_CURSIVE, ADJUST_PAIR, ADJUST_SINGLE'):
            [lookup] = self.parse(
                'DEF_LOOKUP "empty_position" PROCESS_BASE PROCESS_MARKS ALL '
                'DIRECTION LTR\n'
                'EXCEPT_CONTEXT\n'
                'LEFT GLYPH "glyph"\n'
                'END_CONTEXT\n'
                'AS_POSITION\n'
                'END_POSITION'
            ).statements

    def test_position_attach(self):
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
            ("anchor_top", ("a", "e"), [(("acutecomb",), "top"),
                                        (("gravecomb",), "top")])
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

    def test_position_attach_cursive(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "SomeLookup" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION RTL\n'
            'IN_CONTEXT\n'
            'END_CONTEXT\n'
            'AS_POSITION\n'
            'ATTACH_CURSIVE EXIT GLYPH "a" GLYPH "b" ENTER GLYPH "c"\n'
            'END_ATTACH\n'
            'END_POSITION\n'
        ).statements
        self.assertEqual(
            (lookup.name,
             lookup.pos.coverages_exit, lookup.pos.coverages_enter),
            ("SomeLookup",
             [("a", "b")], [("c",)])
        )

    def test_position_adjust_pair(self):
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
             lookup.pos.adjust_pair),
            ("kern1", [("A",)], [("V",)],
             {(1, 2): ((-30, None, None, {}, {}, {}),
                       (None, None, None, {}, {}, {})),
              (2, 1): ((-30, None, None, {}, {}, {}),
                       (None, None, None, {}, {}, {}))})
        )

    def test_position_adjust_single(self):
        [lookup] = self.parse(
            'DEF_LOOKUP "TestLookup" PROCESS_BASE PROCESS_MARKS ALL '
            'DIRECTION LTR\n'
            'IN_CONTEXT\n'
            # 'LEFT GLYPH "leftGlyph"\n'
            # 'RIGHT GLYPH "rightGlyph"\n'
            'END_CONTEXT\n'
            'AS_POSITION\n'
            'ADJUST_SINGLE'
            ' GLYPH "glyph1" BY POS ADV 0 DX 123 END_POS\n'
            ' GLYPH "glyph2" BY POS ADV 0 DX 456 END_POS\n'
            'END_ADJUST\n'
            'END_POSITION\n'
        ).statements
        self.assertEqual(
            (lookup.name, lookup.pos.adjust_single),
            ("TestLookup",
             [(("glyph1",), (0, 123, None, {}, {}, {})),
              (("glyph2",), (0, 456, None, {}, {}, {}))])
        )

    def test_def_anchor(self):
        [anchor1, anchor2, anchor3] = self.parse(
            'DEF_ANCHOR "top" ON 120 GLYPH a '
            'COMPONENT 1 AT POS DX 250 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb '
            'COMPONENT 1 AT POS DX 0 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "bottom" ON 120 GLYPH a '
            'COMPONENT 1 AT POS DX 250 DY 0 END_POS END_ANCHOR\n'
        ).statements
        self.assertEqual(
            (anchor1.name, anchor1.gid, anchor1.glyph_name, anchor1.component,
             anchor1.locked, anchor1.pos),
            ("top", 120, "a", 1,
             False, (None, 250, 450, {}, {}, {}))
        )
        self.assertEqual(
            (anchor2.name, anchor2.gid, anchor2.glyph_name, anchor2.component,
             anchor2.locked, anchor2.pos),
            ("MARK_top", 120, "acutecomb", 1,
             False, (None, 0, 450, {}, {}, {}))
        )
        self.assertEqual(
            (anchor3.name, anchor3.gid, anchor3.glyph_name, anchor3.component,
             anchor3.locked, anchor3.pos),
            ("bottom", 120, "a", 1,
             False, (None, 250, 0, {}, {}, {}))
        )

    def test_def_anchor_duplicate(self):
        self.assertRaisesRegex(
            VoltLibError,
            'Anchor "dupe" already defined, '
            'anchor names are case insensitive',
            self.parse,
            'DEF_ANCHOR "dupe" ON 120 GLYPH a '
            'COMPONENT 1 AT POS DX 250 DY 450 END_POS END_ANCHOR\n'
            'DEF_ANCHOR "dupe" ON 120 GLYPH a '
            'COMPONENT 1 AT POS DX 250 DY 450 END_POS END_ANCHOR\n'
        )

    def test_def_anchor_locked(self):
        [anchor] = self.parse(
            'DEF_ANCHOR "top" ON 120 GLYPH a '
            'COMPONENT 1 LOCKED AT POS DX 250 DY 450 END_POS END_ANCHOR\n'
        ).statements
        self.assertEqual(
            (anchor.name, anchor.gid, anchor.glyph_name, anchor.component,
             anchor.locked, anchor.pos),
            ("top", 120, "a", 1,
             True, (None, 250, 450, {}, {}, {}))
        )

    def test_anchor_adjust_device(self):
        [anchor] = self.parse(
            'DEF_ANCHOR "MARK_top" ON 123 GLYPH diacglyph '
            'COMPONENT 1 AT POS DX 0 DY 456 ADJUST_BY 12 AT 34 '
            'ADJUST_BY 56 AT 78 END_POS END_ANCHOR'
        ).statements
        self.assertEqual(
            (anchor.name, anchor.pos),
            ("MARK_top", (None, 0, 456, {}, {}, {34: 12, 78: 56}))
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
        with open(path, "w") as outfile:
            outfile.write(text)
        return Parser(path).parse()

if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
