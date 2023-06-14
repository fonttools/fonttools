import pathlib
import shutil
import tempfile
import unittest
from io import StringIO

from fontTools.voltLib.voltToFea import VoltToFea

DATADIR = pathlib.Path(__file__).parent / "data"


class ToFeaTest(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        cls.tempdir = None
        cls.num_tempfiles = 0

    @classmethod
    def teardown_class(cls):
        if cls.tempdir:
            shutil.rmtree(cls.tempdir, ignore_errors=True)

    @classmethod
    def temp_path(cls):
        if not cls.tempdir:
            cls.tempdir = pathlib.Path(tempfile.mkdtemp())
        cls.num_tempfiles += 1
        return cls.tempdir / f"tmp{cls.num_tempfiles}"

    def test_def_glyph_base(self):
        fea = self.parse('DEF_GLYPH ".notdef" ID 0 TYPE BASE END_GLYPH')
        self.assertEqual(
            fea,
            "@GDEF_base = [.notdef];\n"
            "table GDEF {\n"
            "    GlyphClassDef @GDEF_base, , , ;\n"
            "} GDEF;\n",
        )

    def test_def_glyph_base_2_components(self):
        fea = self.parse(
            'DEF_GLYPH "glyphBase" ID 320 TYPE BASE COMPONENTS 2 END_GLYPH'
        )
        self.assertEqual(
            fea,
            "@GDEF_base = [glyphBase];\n"
            "table GDEF {\n"
            "    GlyphClassDef @GDEF_base, , , ;\n"
            "} GDEF;\n",
        )

    def test_def_glyph_ligature_2_components(self):
        fea = self.parse('DEF_GLYPH "f_f" ID 320 TYPE LIGATURE COMPONENTS 2 END_GLYPH')
        self.assertEqual(
            fea,
            "@GDEF_ligature = [f_f];\n"
            "table GDEF {\n"
            "    GlyphClassDef , @GDEF_ligature, , ;\n"
            "} GDEF;\n",
        )

    def test_def_glyph_mark(self):
        fea = self.parse('DEF_GLYPH "brevecomb" ID 320 TYPE MARK END_GLYPH')
        self.assertEqual(
            fea,
            "@GDEF_mark = [brevecomb];\n"
            "table GDEF {\n"
            "    GlyphClassDef , , @GDEF_mark, ;\n"
            "} GDEF;\n",
        )

    def test_def_glyph_component(self):
        fea = self.parse('DEF_GLYPH "f.f_f" ID 320 TYPE COMPONENT END_GLYPH')
        self.assertEqual(
            fea,
            "@GDEF_component = [f.f_f];\n"
            "table GDEF {\n"
            "    GlyphClassDef , , , @GDEF_component;\n"
            "} GDEF;\n",
        )

    def test_def_glyph_no_type(self):
        fea = self.parse('DEF_GLYPH "glyph20" ID 20 END_GLYPH')
        self.assertEqual(fea, "")

    def test_def_glyph_case_sensitive(self):
        fea = self.parse(
            'DEF_GLYPH "A" ID 3 UNICODE 65 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "a" ID 4 UNICODE 97 TYPE BASE END_GLYPH\n'
        )
        self.assertEqual(
            fea,
            "@GDEF_base = [A a];\n"
            "table GDEF {\n"
            "    GlyphClassDef @GDEF_base, , , ;\n"
            "} GDEF;\n",
        )

    def test_def_group_glyphs(self):
        fea = self.parse(
            'DEF_GROUP "aaccented"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" GLYPH "acircumflex" '
            'GLYPH "adieresis" GLYPH "ae" GLYPH "agrave" GLYPH "amacron" '
            'GLYPH "aogonek" GLYPH "aring" GLYPH "atilde" END_ENUM\n'
            "END_GROUP\n"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@aaccented = [aacute abreve acircumflex adieresis ae"
            " agrave amacron aogonek aring atilde];",
        )

    def test_def_group_groups(self):
        fea = self.parse(
            'DEF_GROUP "Group1"\n'
            'ENUM GLYPH "a" GLYPH "b" GLYPH "c" GLYPH "d" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "Group2"\n'
            'ENUM GLYPH "e" GLYPH "f" GLYPH "g" GLYPH "h" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "TestGroup"\n'
            'ENUM GROUP "Group1" GROUP "Group2" END_ENUM\n'
            "END_GROUP\n"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@Group1 = [a b c d];\n"
            "@Group2 = [e f g h];\n"
            "@TestGroup = [@Group1 @Group2];",
        )

    def test_def_group_groups_not_yet_defined(self):
        fea = self.parse(
            'DEF_GROUP "Group1"\n'
            'ENUM GLYPH "a" GLYPH "b" GLYPH "c" GLYPH "d" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "TestGroup1"\n'
            'ENUM GROUP "Group1" GROUP "Group2" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "TestGroup2"\n'
            'ENUM GROUP "Group2" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "TestGroup3"\n'
            'ENUM GROUP "Group2" GROUP "Group1" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "Group2"\n'
            'ENUM GLYPH "e" GLYPH "f" GLYPH "g" GLYPH "h" END_ENUM\n'
            "END_GROUP\n"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@Group1 = [a b c d];\n"
            "@Group2 = [e f g h];\n"
            "@TestGroup1 = [@Group1 @Group2];\n"
            "@TestGroup2 = [@Group2];\n"
            "@TestGroup3 = [@Group2 @Group1];",
        )

    def test_def_group_glyphs_and_group(self):
        fea = self.parse(
            'DEF_GROUP "aaccented"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" GLYPH "acircumflex" '
            'GLYPH "adieresis" GLYPH "ae" GLYPH "agrave" GLYPH "amacron" '
            'GLYPH "aogonek" GLYPH "aring" GLYPH "atilde" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM GLYPH "a" GROUP "aaccented" END_ENUM\n'
            "END_GROUP"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@aaccented = [aacute abreve acircumflex adieresis ae"
            " agrave amacron aogonek aring atilde];\n"
            "@KERN_lc_a_2ND = [a @aaccented];",
        )

    def test_def_group_range(self):
        fea = self.parse(
            'DEF_GLYPH "a" ID 163 UNICODE 97 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "agrave" ID 194 UNICODE 224 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "aacute" ID 195 UNICODE 225 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "acircumflex" ID 196 UNICODE 226 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "atilde" ID 197 UNICODE 227 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "c" ID 165 UNICODE 99 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "ccaron" ID 209 UNICODE 269 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "ccedilla" ID 210 UNICODE 231 TYPE BASE END_GLYPH\n'
            'DEF_GLYPH "cdotaccent" ID 210 UNICODE 267 TYPE BASE END_GLYPH\n'
            'DEF_GROUP "KERN_lc_a_2ND"\n'
            'ENUM RANGE "a" TO "atilde" GLYPH "b" RANGE "c" TO "cdotaccent" '
            "END_ENUM\n"
            "END_GROUP"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@KERN_lc_a_2ND = [a - atilde b c - cdotaccent];\n"
            "@GDEF_base = [a agrave aacute acircumflex atilde c"
            " ccaron ccedilla cdotaccent];\n"
            "table GDEF {\n"
            "    GlyphClassDef @GDEF_base, , , ;\n"
            "} GDEF;\n",
        )

    def test_script_without_langsys(self):
        fea = self.parse('DEF_SCRIPT NAME "Latin" TAG "latn"\n' "END_SCRIPT")
        self.assertEqual(fea, "")

    def test_langsys_normal(self):
        fea = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            "END_LANGSYS\n"
            'DEF_LANGSYS NAME "Moldavian" TAG "MOL "\n'
            "END_LANGSYS\n"
            "END_SCRIPT"
        )
        self.assertEqual(fea, "")

    def test_langsys_no_script_name(self):
        fea = self.parse(
            'DEF_SCRIPT TAG "latn"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            "END_LANGSYS\n"
            "END_SCRIPT"
        )
        self.assertEqual(fea, "")

    def test_langsys_lang_in_separate_scripts(self):
        fea = self.parse(
            'DEF_SCRIPT NAME "Default" TAG "DFLT"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            "END_LANGSYS\n"
            'DEF_LANGSYS NAME "Default" TAG "ROM "\n'
            "END_LANGSYS\n"
            "END_SCRIPT\n"
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Default" TAG "dflt"\n'
            "END_LANGSYS\n"
            'DEF_LANGSYS NAME "Default" TAG "ROM "\n'
            "END_LANGSYS\n"
            "END_SCRIPT"
        )
        self.assertEqual(fea, "")

    def test_langsys_no_lang_name(self):
        fea = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS TAG "dflt"\n'
            "END_LANGSYS\n"
            "END_SCRIPT"
        )
        self.assertEqual(fea, "")

    def test_feature(self):
        fea = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'DEF_FEATURE NAME "Fractions" TAG "frac"\n'
            'LOOKUP "fraclookup"\n'
            "END_FEATURE\n"
            "END_LANGSYS\n"
            "END_SCRIPT\n"
            'DEF_LOOKUP "fraclookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "one" GLYPH "slash" GLYPH "two"\n'
            'WITH GLYPH "one_slash_two.frac"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup fraclookup {\n"
            "    sub one slash two by one_slash_two.frac;\n"
            "} fraclookup;\n"
            "\n"
            "# Features\n"
            "feature frac {\n"
            "    script latn;\n"
            "    language ROM exclude_dflt;\n"
            "    lookup fraclookup;\n"
            "} frac;\n",
        )

    def test_feature_sub_lookups(self):
        fea = self.parse(
            'DEF_SCRIPT NAME "Latin" TAG "latn"\n'
            'DEF_LANGSYS NAME "Romanian" TAG "ROM "\n'
            'DEF_FEATURE NAME "Fractions" TAG "frac"\n'
            'LOOKUP "fraclookup\\1"\n'
            'LOOKUP "fraclookup\\1"\n'
            "END_FEATURE\n"
            "END_LANGSYS\n"
            "END_SCRIPT\n"
            'DEF_LOOKUP "fraclookup\\1" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "one" GLYPH "slash" GLYPH "two"\n'
            'WITH GLYPH "one_slash_two.frac"\n'
            "END_SUB\n"
            "END_SUBSTITUTION\n"
            'DEF_LOOKUP "fraclookup\\2" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "one" GLYPH "slash" GLYPH "three"\n'
            'WITH GLYPH "one_slash_three.frac"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup fraclookup {\n"
            "    lookupflag RightToLeft;\n"
            "    # fraclookup\\1\n"
            "    sub one slash two by one_slash_two.frac;\n"
            "    subtable;\n"
            "    # fraclookup\\2\n"
            "    sub one slash three by one_slash_three.frac;\n"
            "} fraclookup;\n"
            "\n"
            "# Features\n"
            "feature frac {\n"
            "    script latn;\n"
            "    language ROM exclude_dflt;\n"
            "    lookup fraclookup;\n"
            "} frac;\n",
        )

    def test_lookup_comment(self):
        fea = self.parse(
            'DEF_LOOKUP "smcp" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            'COMMENTS "Smallcaps lookup for testing"\n'
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "a"\n'
            'WITH GLYPH "a.sc"\n'
            "END_SUB\n"
            'SUB GLYPH "b"\n'
            'WITH GLYPH "b.sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup smcp {\n"
            "    # Smallcaps lookup for testing\n"
            "    sub a by a.sc;\n"
            "    sub b by b.sc;\n"
            "} smcp;\n",
        )

    def test_substitution_single(self):
        fea = self.parse(
            'DEF_LOOKUP "smcp" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "a"\n'
            'WITH GLYPH "a.sc"\n'
            "END_SUB\n"
            'SUB GLYPH "b"\n'
            'WITH GLYPH "b.sc"\n'
            "END_SUB\n"
            "SUB WITH\n"  # Empty substitution, will be ignored
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup smcp {\n"
            "    sub a by a.sc;\n"
            "    sub b by b.sc;\n"
            "} smcp;\n",
        )

    def test_substitution_single_in_context(self):
        fea = self.parse(
            'DEF_GROUP "Denominators" ENUM GLYPH "one.dnom" GLYPH "two.dnom" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "fracdnom" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            'IN_CONTEXT LEFT ENUM GROUP "Denominators" GLYPH "fraction" '
            "END_ENUM\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "one"\n'
            'WITH GLYPH "one.dnom"\n'
            "END_SUB\n"
            'SUB GLYPH "two"\n'
            'WITH GLYPH "two.dnom"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@Denominators = [one.dnom two.dnom];\n"
            "\n"
            "# Lookups\n"
            "lookup fracdnom {\n"
            "    sub [@Denominators fraction] one' by one.dnom;\n"
            "    sub [@Denominators fraction] two' by two.dnom;\n"
            "} fracdnom;\n",
        )

    def test_substitution_single_in_contexts(self):
        fea = self.parse(
            'DEF_GROUP "Hebrew" ENUM GLYPH "uni05D0" GLYPH "uni05D1" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "HebrewCurrency" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            'RIGHT GROUP "Hebrew"\n'
            'RIGHT GLYPH "one.Hebr"\n'
            "END_CONTEXT\n"
            "IN_CONTEXT\n"
            'LEFT GROUP "Hebrew"\n'
            'LEFT GLYPH "one.Hebr"\n'
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "dollar"\n'
            'WITH GLYPH "dollar.Hebr"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@Hebrew = [uni05D0 uni05D1];\n"
            "\n"
            "# Lookups\n"
            "lookup HebrewCurrency {\n"
            "    sub dollar' @Hebrew one.Hebr by dollar.Hebr;\n"
            "    sub @Hebrew one.Hebr dollar' by dollar.Hebr;\n"
            "} HebrewCurrency;\n",
        )

    def test_substitution_single_except_context(self):
        fea = self.parse(
            'DEF_GROUP "Hebrew" ENUM GLYPH "uni05D0" GLYPH "uni05D1" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "HebrewCurrency" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "EXCEPT_CONTEXT\n"
            'RIGHT GROUP "Hebrew"\n'
            'RIGHT GLYPH "one.Hebr"\n'
            "END_CONTEXT\n"
            "IN_CONTEXT\n"
            'LEFT GROUP "Hebrew"\n'
            'LEFT GLYPH "one.Hebr"\n'
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "dollar"\n'
            'WITH GLYPH "dollar.Hebr"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@Hebrew = [uni05D0 uni05D1];\n"
            "\n"
            "# Lookups\n"
            "lookup HebrewCurrency {\n"
            "    ignore sub dollar' @Hebrew one.Hebr;\n"
            "    sub @Hebrew one.Hebr dollar' by dollar.Hebr;\n"
            "} HebrewCurrency;\n",
        )

    def test_substitution_skip_base(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" SKIP_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [marka markb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag IgnoreBaseGlyphs;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_process_base(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [marka markb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_process_marks_all(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE PROCESS_MARKS "ALL"'
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [marka markb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_process_marks_none(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE PROCESS_MARKS "NONE"'
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [marka markb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag IgnoreMarks;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_skip_marks(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "marka" GLYPH "markb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE SKIP_MARKS '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [marka markb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag IgnoreMarks;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_mark_attachment(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "acutecmb" GLYPH "gravecmb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE '
            'PROCESS_MARKS "SomeMarks" \n'
            "DIRECTION RTL\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [acutecmb gravecmb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag RightToLeft MarkAttachmentType"
            " @SomeMarks;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_mark_glyph_set(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "acutecmb" GLYPH "gravecmb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE '
            'PROCESS_MARKS MARK_GLYPH_SET "SomeMarks" \n'
            "DIRECTION RTL\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [acutecmb gravecmb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag RightToLeft UseMarkFilteringSet"
            " @SomeMarks;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_process_all_marks(self):
        fea = self.parse(
            'DEF_GROUP "SomeMarks" ENUM GLYPH "acutecmb" GLYPH "gravecmb" '
            "END_ENUM END_GROUP\n"
            'DEF_LOOKUP "SomeSub" PROCESS_BASE '
            "PROCESS_MARKS ALL \n"
            "DIRECTION RTL\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "A"\n'
            'WITH GLYPH "A.c2sc"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@SomeMarks = [acutecmb gravecmb];\n"
            "\n"
            "# Lookups\n"
            "lookup SomeSub {\n"
            "    lookupflag RightToLeft;\n"
            "    sub A by A.c2sc;\n"
            "} SomeSub;\n",
        )

    def test_substitution_no_reversal(self):
        # TODO: check right context with no reversal
        fea = self.parse(
            'DEF_LOOKUP "Lookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            'RIGHT ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "a"\n'
            'WITH GLYPH "a.alt"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup Lookup {\n"
            "    sub a' [a b] by a.alt;\n"
            "} Lookup;\n",
        )

    def test_substitution_reversal(self):
        fea = self.parse(
            'DEF_GROUP "DFLT_Num_standardFigures"\n'
            'ENUM GLYPH "zero" GLYPH "one" GLYPH "two" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "DFLT_Num_numerators"\n'
            'ENUM GLYPH "zero.numr" GLYPH "one.numr" GLYPH "two.numr" END_ENUM\n'
            "END_GROUP\n"
            'DEF_LOOKUP "RevLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR REVERSAL\n"
            "IN_CONTEXT\n"
            'RIGHT ENUM GLYPH "a" GLYPH "b" END_ENUM\n'
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GROUP "DFLT_Num_standardFigures"\n'
            'WITH GROUP "DFLT_Num_numerators"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@DFLT_Num_standardFigures = [zero one two];\n"
            "@DFLT_Num_numerators = [zero.numr one.numr two.numr];\n"
            "\n"
            "# Lookups\n"
            "lookup RevLookup {\n"
            "    rsub @DFLT_Num_standardFigures' [a b] by @DFLT_Num_numerators;\n"
            "} RevLookup;\n",
        )

    def test_substitution_single_to_multiple(self):
        fea = self.parse(
            'DEF_LOOKUP "ccmp" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "aacute"\n'
            'WITH GLYPH "a" GLYPH "acutecomb"\n'
            "END_SUB\n"
            'SUB GLYPH "agrave"\n'
            'WITH GLYPH "a" GLYPH "gravecomb"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup ccmp {\n"
            "    sub aacute by a acutecomb;\n"
            "    sub agrave by a gravecomb;\n"
            "} ccmp;\n",
        )

    def test_substitution_multiple_to_single(self):
        fea = self.parse(
            'DEF_LOOKUP "liga" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB GLYPH "f" GLYPH "i"\n'
            'WITH GLYPH "f_i"\n'
            "END_SUB\n"
            'SUB GLYPH "f" GLYPH "t"\n'
            'WITH GLYPH "f_t"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup liga {\n"
            "    sub f i by f_i;\n"
            "    sub f t by f_t;\n"
            "} liga;\n",
        )

    def test_substitution_reverse_chaining_single(self):
        fea = self.parse(
            'DEF_LOOKUP "numr" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR REVERSAL\n"
            "IN_CONTEXT\n"
            "RIGHT ENUM "
            'GLYPH "fraction" '
            'RANGE "zero.numr" TO "nine.numr" '
            "END_ENUM\n"
            "END_CONTEXT\n"
            "AS_SUBSTITUTION\n"
            'SUB RANGE "zero" TO "nine"\n'
            'WITH RANGE "zero.numr" TO "nine.numr"\n'
            "END_SUB\n"
            "END_SUBSTITUTION"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup numr {\n"
            "    rsub zero - nine' [fraction zero.numr - nine.numr] by zero.numr - nine.numr;\n"
            "} numr;\n",
        )

    # GPOS
    #  ATTACH_CURSIVE
    #  ATTACH
    #  ADJUST_PAIR
    #  ADJUST_SINGLE
    def test_position_attach(self):
        fea = self.parse(
            'DEF_LOOKUP "anchor_top" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            'ATTACH GLYPH "a" GLYPH "e"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top" '
            'GLYPH "gravecomb" AT ANCHOR "top"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb COMPONENT 1 '
            "AT POS DX 0 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "MARK_top" ON 121 GLYPH gravecomb COMPONENT 1 '
            "AT POS DX 0 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "top" ON 31 GLYPH a COMPONENT 1 '
            "AT POS DX 210 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "top" ON 35 GLYPH e COMPONENT 1 '
            "AT POS DX 215 DY 450 END_POS END_ANCHOR\n"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "markClass acutecomb <anchor 0 450> @top;\n"
            "markClass gravecomb <anchor 0 450> @top;\n"
            "\n"
            "# Lookups\n"
            "lookup anchor_top {\n"
            "    lookupflag RightToLeft;\n"
            "    pos base a\n"
            "        <anchor 210 450> mark @top;\n"
            "    pos base e\n"
            "        <anchor 215 450> mark @top;\n"
            "} anchor_top;\n",
        )

    def test_position_attach_mkmk(self):
        fea = self.parse(
            'DEF_GLYPH "brevecomb" ID 1 TYPE MARK END_GLYPH\n'
            'DEF_GLYPH "gravecomb" ID 2 TYPE MARK END_GLYPH\n'
            'DEF_LOOKUP "anchor_top" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            'ATTACH GLYPH "gravecomb"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_ANCHOR "MARK_top" ON 1 GLYPH acutecomb COMPONENT 1 '
            "AT POS DX 0 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "top" ON 2 GLYPH gravecomb COMPONENT 1 '
            "AT POS DX 210 DY 450 END_POS END_ANCHOR\n"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "markClass acutecomb <anchor 0 450> @top;\n"
            "\n"
            "# Lookups\n"
            "lookup anchor_top {\n"
            "    lookupflag RightToLeft;\n"
            "    pos mark gravecomb\n"
            "        <anchor 210 450> mark @top;\n"
            "} anchor_top;\n"
            "\n"
            "@GDEF_mark = [brevecomb gravecomb];\n"
            "table GDEF {\n"
            "    GlyphClassDef , , @GDEF_mark, ;\n"
            "} GDEF;\n",
        )

    def test_position_attach_in_context(self):
        fea = self.parse(
            'DEF_LOOKUP "test" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            'EXCEPT_CONTEXT LEFT GLYPH "a" END_CONTEXT\n'
            "AS_POSITION\n"
            'ATTACH GLYPH "a"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top" '
            'GLYPH "gravecomb" AT ANCHOR "top"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb COMPONENT 1 '
            "AT POS DX 0 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "MARK_top" ON 121 GLYPH gravecomb COMPONENT 1 '
            "AT POS DX 0 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "top" ON 31 GLYPH a COMPONENT 1 '
            "AT POS DX 210 DY 450 END_POS END_ANCHOR\n"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "markClass acutecomb <anchor 0 450> @top;\n"
            "markClass gravecomb <anchor 0 450> @top;\n"
            "\n"
            "# Lookups\n"
            "lookup test_target {\n"
            "    pos base a\n"
            "        <anchor 210 450> mark @top;\n"
            "} test_target;\n"
            "\n"
            "lookup test {\n"
            "    lookupflag RightToLeft;\n"
            "    ignore pos a [acutecomb gravecomb]';\n"
            "    pos [acutecomb gravecomb]' lookup test_target;\n"
            "} test;\n",
        )

    def test_position_attach_cursive(self):
        fea = self.parse(
            'DEF_LOOKUP "SomeLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            'ATTACH_CURSIVE EXIT GLYPH "a" GLYPH "b" '
            'ENTER GLYPH "a" GLYPH "c"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_ANCHOR "exit"  ON 1 GLYPH a COMPONENT 1 AT POS END_POS END_ANCHOR\n'
            'DEF_ANCHOR "entry" ON 1 GLYPH a COMPONENT 1 AT POS END_POS END_ANCHOR\n'
            'DEF_ANCHOR "exit"  ON 2 GLYPH b COMPONENT 1 AT POS END_POS END_ANCHOR\n'
            'DEF_ANCHOR "entry" ON 3 GLYPH c COMPONENT 1 AT POS END_POS END_ANCHOR\n'
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup SomeLookup {\n"
            "    lookupflag RightToLeft;\n"
            "    pos cursive a <anchor 0 0> <anchor 0 0>;\n"
            "    pos cursive c <anchor 0 0> <anchor NULL>;\n"
            "    pos cursive b <anchor NULL> <anchor 0 0>;\n"
            "} SomeLookup;\n",
        )

    def test_position_adjust_pair(self):
        fea = self.parse(
            'DEF_LOOKUP "kern1" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION RTL\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            "ADJUST_PAIR\n"
            ' FIRST GLYPH "A" FIRST GLYPH "V"\n'
            ' SECOND GLYPH "A" SECOND GLYPH "V"\n'
            " 1 2 BY POS ADV -30 END_POS POS END_POS\n"
            " 2 1 BY POS ADV -25 END_POS POS END_POS\n"
            "END_ADJUST\n"
            "END_POSITION\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup kern1 {\n"
            "    lookupflag RightToLeft;\n"
            "    enum pos A V -30;\n"
            "    enum pos V A -25;\n"
            "} kern1;\n",
        )

    def test_position_adjust_pair_in_context(self):
        fea = self.parse(
            'DEF_LOOKUP "kern1" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            'EXCEPT_CONTEXT LEFT GLYPH "A" END_CONTEXT\n'
            "AS_POSITION\n"
            "ADJUST_PAIR\n"
            ' FIRST GLYPH "A" FIRST GLYPH "V"\n'
            ' SECOND GLYPH "A" SECOND GLYPH "V"\n'
            " 2 1 BY POS ADV -25 END_POS POS END_POS\n"
            "END_ADJUST\n"
            "END_POSITION\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup kern1_target {\n"
            "    enum pos V A -25;\n"
            "} kern1_target;\n"
            "\n"
            "lookup kern1 {\n"
            "    ignore pos A V' A';\n"
            "    pos V' lookup kern1_target A' lookup kern1_target;\n"
            "} kern1;\n",
        )

    def test_position_adjust_single(self):
        fea = self.parse(
            'DEF_LOOKUP "TestLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            "ADJUST_SINGLE"
            ' GLYPH "glyph1" BY POS ADV 0 DX 123 END_POS\n'
            ' GLYPH "glyph2" BY POS ADV 0 DX 456 END_POS\n'
            "END_ADJUST\n"
            "END_POSITION\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup TestLookup {\n"
            "    pos glyph1 <123 0 0 0>;\n"
            "    pos glyph2 <456 0 0 0>;\n"
            "} TestLookup;\n",
        )

    def test_position_adjust_single_in_context(self):
        fea = self.parse(
            'DEF_LOOKUP "TestLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "EXCEPT_CONTEXT\n"
            'LEFT GLYPH "leftGlyph"\n'
            'RIGHT GLYPH "rightGlyph"\n'
            "END_CONTEXT\n"
            "AS_POSITION\n"
            "ADJUST_SINGLE"
            ' GLYPH "glyph1" BY POS ADV 0 DX 123 END_POS\n'
            ' GLYPH "glyph2" BY POS ADV 0 DX 456 END_POS\n'
            "END_ADJUST\n"
            "END_POSITION\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup TestLookup_target {\n"
            "    pos glyph1 <123 0 0 0>;\n"
            "    pos glyph2 <456 0 0 0>;\n"
            "} TestLookup_target;\n"
            "\n"
            "lookup TestLookup {\n"
            "    ignore pos leftGlyph [glyph1 glyph2]' rightGlyph;\n"
            "    pos [glyph1 glyph2]' lookup TestLookup_target;\n"
            "} TestLookup;\n",
        )

    def test_def_anchor(self):
        fea = self.parse(
            'DEF_LOOKUP "TestLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            'ATTACH GLYPH "a"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_ANCHOR "top" ON 120 GLYPH a '
            "COMPONENT 1 AT POS DX 250 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb '
            "COMPONENT 1 AT POS DX 0 DY 450 END_POS END_ANCHOR"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "markClass acutecomb <anchor 0 450> @top;\n"
            "\n"
            "# Lookups\n"
            "lookup TestLookup {\n"
            "    pos base a\n"
            "        <anchor 250 450> mark @top;\n"
            "} TestLookup;\n",
        )

    def test_def_anchor_multi_component(self):
        fea = self.parse(
            'DEF_LOOKUP "TestLookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            'ATTACH GLYPH "f_f"\n'
            'TO GLYPH "acutecomb" AT ANCHOR "top"\n'
            "END_ATTACH\n"
            "END_POSITION\n"
            'DEF_GLYPH "f_f" ID 120 TYPE LIGATURE COMPONENTS 2 END_GLYPH\n'
            'DEF_ANCHOR "top" ON 120 GLYPH f_f '
            "COMPONENT 1 AT POS DX 250 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "top" ON 120 GLYPH f_f '
            "COMPONENT 2 AT POS DX 450 DY 450 END_POS END_ANCHOR\n"
            'DEF_ANCHOR "MARK_top" ON 120 GLYPH acutecomb '
            "COMPONENT 1 AT POS  END_POS END_ANCHOR"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "markClass acutecomb <anchor 0 0> @top;\n"
            "\n"
            "# Lookups\n"
            "lookup TestLookup {\n"
            "    pos ligature f_f\n"
            "            <anchor 250 450> mark @top\n"
            "        ligComponent\n"
            "            <anchor 450 450> mark @top;\n"
            "} TestLookup;\n"
            "\n"
            "@GDEF_ligature = [f_f];\n"
            "table GDEF {\n"
            "    GlyphClassDef , @GDEF_ligature, , ;\n"
            "} GDEF;\n",
        )

    def test_anchor_adjust_device(self):
        fea = self.parse(
            'DEF_ANCHOR "MARK_top" ON 123 GLYPH diacglyph '
            "COMPONENT 1 AT POS DX 0 DY 456 ADJUST_BY 12 AT 34 "
            "ADJUST_BY 56 AT 78 END_POS END_ANCHOR"
        )
        self.assertEqual(
            fea,
            "\n# Mark classes\n"
            "#markClass diacglyph <anchor 0 456 <device NULL>"
            " <device 34 12, 78 56>> @top;",
        )

    def test_use_extension(self):
        fea = self.parse(
            'DEF_LOOKUP "kern1" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR\n"
            "IN_CONTEXT\n"
            "END_CONTEXT\n"
            "AS_POSITION\n"
            "ADJUST_PAIR\n"
            ' FIRST GLYPH "A" FIRST GLYPH "V"\n'
            ' SECOND GLYPH "A" SECOND GLYPH "V"\n'
            " 1 2 BY POS ADV -30 END_POS POS END_POS\n"
            " 2 1 BY POS ADV -25 END_POS POS END_POS\n"
            "END_ADJUST\n"
            "END_POSITION\n"
            "COMPILER_USEEXTENSIONLOOKUPS\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup kern1 useExtension {\n"
            "    enum pos A V -30;\n"
            "    enum pos V A -25;\n"
            "} kern1;\n",
        )

    def test_unsupported_compiler_flags(self):
        with self.assertLogs(level="WARNING") as logs:
            fea = self.parse("CMAP_FORMAT 0 3 4")
            self.assertEqual(fea, "")
        self.assertEqual(
            logs.output,
            [
                "WARNING:fontTools.voltLib.voltToFea:Unsupported setting ignored: CMAP_FORMAT"
            ],
        )

    def test_sanitize_lookup_name(self):
        fea = self.parse(
            'DEF_LOOKUP "Test Lookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR IN_CONTEXT END_CONTEXT\n"
            "AS_POSITION ADJUST_PAIR END_ADJUST END_POSITION\n"
            'DEF_LOOKUP "Test-Lookup" PROCESS_BASE PROCESS_MARKS ALL '
            "DIRECTION LTR IN_CONTEXT END_CONTEXT\n"
            "AS_POSITION ADJUST_PAIR END_ADJUST END_POSITION\n"
        )
        self.assertEqual(
            fea,
            "\n# Lookups\n"
            "lookup Test_Lookup {\n"
            "    \n"
            "} Test_Lookup;\n"
            "\n"
            "lookup Test_Lookup_ {\n"
            "    \n"
            "} Test_Lookup_;\n",
        )

    def test_sanitize_group_name(self):
        fea = self.parse(
            'DEF_GROUP "aaccented glyphs"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" END_ENUM\n'
            "END_GROUP\n"
            'DEF_GROUP "aaccented+glyphs"\n'
            'ENUM GLYPH "aacute" GLYPH "abreve" END_ENUM\n'
            "END_GROUP\n"
        )
        self.assertEqual(
            fea,
            "# Glyph classes\n"
            "@aaccented_glyphs = [aacute abreve];\n"
            "@aaccented_glyphs_ = [aacute abreve];",
        )

    def test_cli_vtp(self):
        vtp = DATADIR / "Nutso.vtp"
        fea = DATADIR / "Nutso.fea"
        self.cli(vtp, fea)

    def test_group_order(self):
        vtp = DATADIR / "NamdhinggoSIL1006.vtp"
        fea = DATADIR / "NamdhinggoSIL1006.fea"
        self.cli(vtp, fea)

    def test_cli_ttf(self):
        ttf = DATADIR / "Nutso.ttf"
        fea = DATADIR / "Nutso.fea"
        self.cli(ttf, fea)

    def test_cli_ttf_no_TSIV(self):
        from fontTools.voltLib.voltToFea import main as cli

        ttf = DATADIR / "Empty.ttf"
        temp = self.temp_path()
        self.assertEqual(1, cli([str(ttf), str(temp)]))

    def cli(self, source, fea):
        from fontTools.voltLib.voltToFea import main as cli

        temp = self.temp_path()
        cli([str(source), str(temp)])
        with temp.open() as f:
            res = f.read()
        with fea.open() as f:
            ref = f.read()
        self.assertEqual(ref, res)

    def parse(self, text):
        return VoltToFea(StringIO(text)).convert()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
