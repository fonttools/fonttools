from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.builder import Builder, addOpenTypeFeatures
from fontTools.feaLib.builder import LigatureSubstBuilder
from fontTools.feaLib.error import FeatureLibError
from fontTools.ttLib import TTFont
import codecs
import difflib
import os
import shutil
import sys
import tempfile
import unittest


def makeTTFont():
    glyphs = (
        ".notdef space slash fraction "
        "zero one two three four five six seven eight nine "
        "zero.oldstyle one.oldstyle two.oldstyle three.oldstyle "
        "four.oldstyle five.oldstyle six.oldstyle seven.oldstyle "
        "eight.oldstyle nine.oldstyle onehalf "
        "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z "
        "a b c d e f g h i j k l m n o p q r s t u v w x y z "
        "A.sc B.sc C.sc D.sc E.sc F.sc G.sc H.sc I.sc J.sc K.sc L.sc M.sc "
        "N.sc O.sc P.sc Q.sc R.sc S.sc T.sc U.sc V.sc W.sc X.sc Y.sc Z.sc "
        "A.alt1 A.alt2 A.alt3 B.alt1 B.alt2 B.alt3 C.alt1 C.alt2 C.alt3 "
        "d.alt n.end s.end "
        "f_l c_h c_k c_s c_t f_f f_f_i f_f_l f_i o_f_f_i s_t "
        "grave acute dieresis macron circumflex cedilla umlaut ogonek caron "
        "damma hamza sukun kasratan lam_meem_jeem  "
    ).split()
    font = TTFont()
    font.setGlyphOrder(glyphs)
    return font


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
        font.saveXML(path, quiet=True, tables=['GDEF', 'GSUB', 'GPOS'])
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
        font = makeTTFont()
        addOpenTypeFeatures(path, font)
        return font

    def test_alternateSubst(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("GSUB_3.fea"), font)
        self.expect_ttx(font, self.getpath("GSUB_3.ttx"))

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

    def test_multipleSubst(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("GSUB_2.fea"), font)
        self.expect_ttx(font, self.getpath("GSUB_2.ttx"))

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
            r"Already defined position for "
            "pair \[A B\] \[zero one two\] at .*:2:[0-9]+",  # :2: = line 2
            self.build,
            "feature test {\n"
            "    pos [A B] [zero one two] 123;\n"  # line 2
            "    pos [A B] [zero one two] 456;\n"
            "} test;\n")

    def test_reverseChainingSingleSubst(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("GSUB_8.fea"), font)
        self.expect_ttx(font, self.getpath("GSUB_8.ttx"))

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

    def test_GPOS(self):
        for name in "1 2 3 4 5 6 8".split():
            font = makeTTFont()
            addOpenTypeFeatures(self.getpath("GPOS_%s.fea" % name), font)
            self.expect_ttx(font, self.getpath("GPOS_%s.ttx" % name))

    def test_spec(self):
        for name in "4h1 5d1 5d2 5fi1 5h1 6d2 6e 6f 6h_ii".split():
            font = makeTTFont()
            addOpenTypeFeatures(self.getpath("spec%s.fea" % name), font)
            self.expect_ttx(font, self.getpath("spec%s.ttx" % name))

    def test_languagesystem(self):
        builder = Builder(None, makeTTFont())
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
        builder = Builder(None, makeTTFont())
        builder.start_feature(location=None, name='test')
        self.assertEqual(builder.language_systems, {('DFLT', 'dflt')})

    def test_languagesystem_DFLT_dflt_not_first(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "If \"languagesystem DFLT dflt\" is present, "
            "it must be the first of the languagesystem statements",
            self.build, "languagesystem latn TRK; languagesystem DFLT dflt;")

    def test_markClass(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("markClass.fea"), font)
        self.expect_ttx(font, self.getpath("markClass.ttx"))

    def test_markClass_redefine(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Glyph C cannot be both in markClass @MARK1 and @MARK2",
            self.build,
            "markClass [A B C] <anchor 100 50> @MARK1;"
            "markClass [C D E] <anchor 200 80> @MARK2;")

    def test_script(self):
        builder = Builder(None, makeTTFont())
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        self.assertEqual(builder.language_systems,
                         {('DFLT', 'dflt'), ('cyrl', 'dflt')})

    def test_script_in_aalt_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Script statements are not allowed within \"feature aalt\"",
            self.build, "feature aalt { script latn; } aalt;")

    def test_script_in_lookup_block(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Within a named lookup block, it is not allowed "
            "to change the script",
            self.build, "lookup Foo { script latn; } Foo;")

    def test_script_in_size_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Script statements are not allowed within \"feature size\"",
            self.build, "feature size { script latn; } size;")

    def test_language(self):
        builder = Builder(None, makeTTFont())
        builder.add_language_system(None, 'latn', 'FRA ')
        builder.start_feature(location=None, name='test')
        builder.set_script(location=None, script='cyrl')
        builder.set_language(location=None, language='RUS ',
                             include_default=False, required=False)
        self.assertEqual(builder.language_systems, {('cyrl', 'RUS ')})
        builder.set_language(location=None, language='BGR ',
                             include_default=True, required=False)
        self.assertEqual(builder.language_systems,
                         {('latn', 'FRA '), ('cyrl', 'BGR ')})

    def test_language_in_aalt_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Language statements are not allowed within \"feature aalt\"",
            self.build, "feature aalt { language FRA; } aalt;")

    def test_language_in_lookup_block(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Within a named lookup block, it is not allowed "
            "to change the language",
            self.build, "lookup Foo { language RUS; } Foo;")

    def test_language_in_size_feature(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Language statements are not allowed within \"feature size\"",
            self.build, "feature size { language FRA; } size;")

    def test_language_required(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("language_required.fea"), font)
        self.expect_ttx(font, self.getpath("language_required.ttx"))

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
            "    language FRA required;"
            "    substitute [a-z] by [A.sc-Z.sc];"
            "} test;")

    def test_lookup(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("lookup.fea"), font)
        self.expect_ttx(font, self.getpath("lookup.ttx"))

    def test_lookup_already_defined(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Lookup \"foo\" has already been defined",
            self.build, "lookup foo {} foo; lookup foo {} foo;")

    def test_lookup_multiple_flags(self):
        # TODO(sascha): As soon as we have a working implementation
        # of the "lookupflag" statement, test whether the compiler
        # rejects rules of the same lookup type but different flags.
        pass

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

    def test_lookupflag(self):
        font = makeTTFont()
        addOpenTypeFeatures(self.getpath("lookupflag.fea"), font)
        self.expect_ttx(font, self.getpath("lookupflag.ttx"))


class LigatureSubstBuilderTest(unittest.TestCase):
    def test_make_key(self):
        self.assertEqual(LigatureSubstBuilder.make_key(('f', 'f', 'i')),
                         (-3, ('f', 'f', 'i')))


if __name__ == "__main__":
    unittest.main()
