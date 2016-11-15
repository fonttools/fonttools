from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.feaLib.builder import Builder, addOpenTypeFeatures
from fontTools.feaLib.builder import LigatureSubstBuilder
from fontTools.feaLib.error import FeatureLibError
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
import difflib
import os
import shutil
import sys
import tempfile
import unittest


def makeTTFont():
    glyphs = """
        .notdef space slash fraction semicolon period comma ampersand
        quotedblleft quotedblright quoteleft quoteright
        zero one two three four five six seven eight nine
        zero.oldstyle one.oldstyle two.oldstyle three.oldstyle
        four.oldstyle five.oldstyle six.oldstyle seven.oldstyle
        eight.oldstyle nine.oldstyle onequarter onehalf threequarters
        onesuperior twosuperior threesuperior ordfeminine ordmasculine
        A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
        a b c d e f g h i j k l m n o p q r s t u v w x y z
        A.sc B.sc C.sc D.sc E.sc F.sc G.sc H.sc I.sc J.sc K.sc L.sc M.sc
        N.sc O.sc P.sc Q.sc R.sc S.sc T.sc U.sc V.sc W.sc X.sc Y.sc Z.sc
        A.alt1 A.alt2 A.alt3 B.alt1 B.alt2 B.alt3 C.alt1 C.alt2 C.alt3
        a.alt1 a.alt2 a.alt3 a.end b.alt c.mid d.alt d.mid
        e.begin e.mid e.end m.begin n.end s.end z.end
        Eng Eng.alt1 Eng.alt2 Eng.alt3
        A.swash B.swash C.swash D.swash E.swash F.swash G.swash H.swash
        I.swash J.swash K.swash L.swash M.swash N.swash O.swash P.swash
        Q.swash R.swash S.swash T.swash U.swash V.swash W.swash X.swash
        Y.swash Z.swash
        f_l c_h c_k c_s c_t f_f f_f_i f_f_l f_i o_f_f_i s_t f_i.begin
        a_n_d T_h T_h.swash germandbls ydieresis yacute breve
        grave acute dieresis macron circumflex cedilla umlaut ogonek caron
        damma hamza sukun kasratan lam_meem_jeem noon.final noon.initial
        by feature lookup sub table
    """.split()
    font = TTFont()
    font.setGlyphOrder(glyphs)
    return font


class BuilderTest(unittest.TestCase):
    # Feature files in testdata/*.fea; output gets compared to testdata/*.ttx.
    TEST_FEATURE_FILES = """
        Attach enum markClass language_required
        GlyphClassDef LigatureCaretByIndex LigatureCaretByPos
        lookup lookupflag feature_aalt ignore_pos
        GPOS_1 GPOS_1_zero GPOS_2 GPOS_2b GPOS_3 GPOS_4 GPOS_5 GPOS_6 GPOS_8
        GSUB_2 GSUB_3 GSUB_6 GSUB_8
        spec4h1 spec4h2 spec5d1 spec5d2 spec5fi1 spec5fi2 spec5fi3 spec5fi4
        spec5f_ii_1 spec5f_ii_2 spec5f_ii_3 spec5f_ii_4
        spec5h1 spec6b_ii spec6d2 spec6e spec6f
        spec6h_ii spec6h_iii_1 spec6h_iii_3d spec8a spec8b spec8c
        spec9a spec9b spec9c1 spec9c2 spec9c3 spec9d spec9e spec9f spec9g
        spec10
        bug453 bug457 bug463 bug501 bug502 bug504 bug505 bug506 bug509
        bug512 bug568
        name size size2 multiple_feature_blocks
    """.split()

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
        with open(path, "r", encoding="utf-8") as ttx:
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
        font.saveXML(path, tables=['head', 'name', 'BASE', 'GDEF', 'GSUB',
                                   'GPOS', 'OS/2', 'hhea', 'vhea'])
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                    expected, actual, fromfile=path, tofile=expected_ttx):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def build(self, featureFile):
        path = self.temp_path(suffix=".fea")
        with open(path, "w", encoding="utf-8") as outfile:
            outfile.write(featureFile)
        font = makeTTFont()
        addOpenTypeFeatures(font, path)
        return font

    def check_feature_file(self, name):
        font = makeTTFont()
        addOpenTypeFeatures(font, self.getpath("%s.fea" % name))
        self.expect_ttx(font, self.getpath("%s.ttx" % name))
        # Make sure we can produce binary OpenType tables, not just XML.
        for tag in ('GDEF', 'GSUB', 'GPOS'):
            if tag in font:
                font[tag].compile(font)

    def test_alternateSubst_multipleSubstitutionsForSameGlyph(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Already defined alternates for glyph \"A\"",
            self.build,
            "feature test {"
            "    sub A from [A.alt1 A.alt2];"
            "    sub B from [B.alt1 B.alt2 B.alt3];"
            "    sub A from [A.alt1 A.alt2];"
            "} test;")

    def test_multipleSubst_multipleSubstitutionsForSameGlyph(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Already defined substitution for glyph \"f_f_i\"",
            self.build,
            "feature test {"
            "    sub f_f_i by f f i;"
            "    sub c_t by c t;"
            "    sub f_f_i by f f i;"
            "} test;")

    def test_pairPos_redefinition(self):
        self.assertRaisesRegex(
            FeatureLibError,
            r"Already defined position for pair A B "
            "at .*:2:[0-9]+",  # :2: = line 2
            self.build,
            "feature test {\n"
            "    pos A B 123;\n"  # line 2
            "    pos A B 456;\n"
            "} test;\n")

    def test_singleSubst_multipleSubstitutionsForSameGlyph(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'Already defined rule for replacing glyph "e" by "E.sc"',
            self.build,
            "feature test {"
            "    sub [a-z] by [A.sc-Z.sc];"
            "    sub e by e.fina;"
            "} test;")

    def test_singlePos_redefinition(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Already defined different position for glyph \"A\"",
            self.build, "feature test { pos A 123; pos A 456; } test;")

    def test_feature_outside_aalt(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'Feature references are only allowed inside "feature aalt"',
            self.build, "feature test { feature test; } test;")

    def test_feature_undefinedReference(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Feature none has not been defined',
            self.build, "feature aalt { feature none; } aalt;")

    def test_GlyphClassDef_conflictingClasses(self):
        self.assertRaisesRegex(
            FeatureLibError, "Glyph X was assigned to a different class",
            self.build,
            "table GDEF {"
            "    GlyphClassDef [a b], [X], , ;"
            "    GlyphClassDef [a b X], , , ;"
            "} GDEF;")

    def test_languagesystem(self):
        builder = Builder(makeTTFont(), (None, None))
        builder.add_language_system(None, 'latn', 'FRA')
        builder.add_language_system(None, 'cyrl', 'RUS')
        builder.start_feature(location=None, name='test')
        self.assertEqual(builder.language_systems,
                         {('latn', 'FRA'), ('cyrl', 'RUS')})

    def test_languagesystem_duplicate(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"languagesystem cyrl RUS" has already been specified',
            self.build, "languagesystem cyrl RUS; languagesystem cyrl RUS;")

    def test_languagesystem_none_specified(self):
        builder = Builder(makeTTFont(), (None, None))
        builder.start_feature(location=None, name='test')
        self.assertEqual(builder.language_systems, {('DFLT', 'dflt')})

    def test_languagesystem_DFLT_dflt_not_first(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "If \"languagesystem DFLT dflt\" is present, "
            "it must be the first of the languagesystem statements",
            self.build, "languagesystem latn TRK; languagesystem DFLT dflt;")

    def test_script(self):
        builder = Builder(makeTTFont(), (None, None))
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        self.assertEqual(builder.language_systems, {('cyrl', 'dflt')})

    def test_script_in_aalt_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Script statements are not allowed within \"feature aalt\"",
            self.build, "feature aalt { script latn; } aalt;")

    def test_script_in_size_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Script statements are not allowed within \"feature size\"",
            self.build, "feature size { script latn; } size;")

    def test_language(self):
        builder = Builder(makeTTFont(), (None, None))
        builder.add_language_system(None, 'latn', 'FRA ')
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        builder.set_language(location=None, language='RUS ',
                             include_default=False, required=False)
        self.assertEqual(builder.language_systems, {('cyrl', 'RUS ')})
        builder.set_language(location=None, language='BGR ',
                             include_default=True, required=False)
        self.assertEqual(builder.language_systems,
                         {('cyrl', 'BGR ')})
        builder.start_feature(location=None, name='test2')
        self.assertRaisesRegex(
            FeatureLibError,
            "Need non-DFLT script when using non-dflt language "
            "\(was: \"FRA \"\)",
            builder.set_language, None, 'FRA ', True, False)

    def test_language_in_aalt_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Language statements are not allowed within \"feature aalt\"",
            self.build, "feature aalt { language FRA; } aalt;")

    def test_language_in_size_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Language statements are not allowed within \"feature size\"",
            self.build, "feature size { language FRA; } size;")

    def test_language_required_duplicate(self):
        self.assertRaisesRegex(
            FeatureLibError,
            r"Language FRA \(script latn\) has already specified "
            "feature scmp as its required feature",
            self.build,
            "feature scmp {"
            "    script latn;"
            "    language FRA required;"
            "    language DEU required;"
            "    substitute [a-z] by [A.sc-Z.sc];"
            "} scmp;"
            "feature test {"
            "    script latn;"
            "    language FRA required;"
            "    substitute [a-z] by [A.sc-Z.sc];"
            "} test;")

    def test_lookup_already_defined(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Lookup \"foo\" has already been defined",
            self.build, "lookup foo {} foo; lookup foo {} foo;")

    def test_lookup_multiple_flags(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Within a named lookup block, all rules must be "
            "of the same lookup type and flag",
            self.build,
            "lookup foo {"
            "    lookupflag 1;"
            "    sub f i by f_i;"
            "    lookupflag 2;"
            "    sub f f i by f_f_i;"
            "} foo;")

    def test_lookup_multiple_types(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Within a named lookup block, all rules must be "
            "of the same lookup type and flag",
            self.build,
            "lookup foo {"
            "    sub f f i by f_f_i;"
            "    sub A from [A.alt1 A.alt2];"
            "} foo;")

    def test_lookup_inside_feature_aalt(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Lookup blocks cannot be placed inside 'aalt' features",
            self.build, "feature aalt {lookup L {} L;} aalt;")


def generate_feature_file_test(name):
    return lambda self: self.check_feature_file(name)

for name in BuilderTest.TEST_FEATURE_FILES:
    setattr(BuilderTest, "test_FeatureFile_%s" % name,
            generate_feature_file_test(name))

if __name__ == "__main__":
    unittest.main()
