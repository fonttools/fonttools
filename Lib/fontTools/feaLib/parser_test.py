from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser, SymbolTable
from fontTools.misc.py23 import *
import fontTools.feaLib.ast as ast
import codecs
import os
import shutil
import sys
import tempfile
import unittest


class ParserTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_anchordef(self):
        [foo] = self.parse("anchorDef 123 456 foo;").statements
        self.assertEqual(type(foo), ast.AnchorDefinition)
        self.assertEqual(foo.name, "foo")
        self.assertEqual(foo.x, 123)
        self.assertEqual(foo.y, 456)
        self.assertEqual(foo.contourpoint, None)

    def test_anchordef_contourpoint(self):
        [foo] = self.parse("anchorDef 123 456 contourpoint 5 foo;").statements
        self.assertEqual(type(foo), ast.AnchorDefinition)
        self.assertEqual(foo.name, "foo")
        self.assertEqual(foo.x, 123)
        self.assertEqual(foo.y, 456)
        self.assertEqual(foo.contourpoint, 5)

    def test_feature_block(self):
        [liga] = self.parse("feature liga {} liga;").statements
        self.assertEqual(liga.name, "liga")
        self.assertFalse(liga.use_extension)

    def test_feature_block_useExtension(self):
        [liga] = self.parse("feature liga useExtension {} liga;").statements
        self.assertEqual(liga.name, "liga")
        self.assertTrue(liga.use_extension)

    def test_glyphclass(self):
        [gc] = self.parse("@dash = [endash emdash figuredash];").statements
        self.assertEqual(gc.name, "dash")
        self.assertEqual(gc.glyphs, {"endash", "emdash", "figuredash"})

    def test_glyphclass_bad(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Expected glyph name, glyph range, or glyph class reference",
            self.parse, "@bad = [a 123];")

    def test_glyphclass_duplicate(self):
        self.assertRaisesRegex(
            FeatureLibError, "Glyph class @dup already defined",
            self.parse, "@dup = [a b]; @dup = [x];")

    def test_glyphclass_empty(self):
        [gc] = self.parse("@empty_set = [];").statements
        self.assertEqual(gc.name, "empty_set")
        self.assertEqual(gc.glyphs, set())

    def test_glyphclass_equality(self):
        [foo, bar] = self.parse("@foo = [a b]; @bar = @foo;").statements
        self.assertEqual(foo.glyphs, {"a", "b"})
        self.assertEqual(bar.glyphs, {"a", "b"})

    def test_glyphclass_range_uppercase(self):
        [gc] = self.parse("@swashes = [X.swash-Z.swash];").statements
        self.assertEqual(gc.name, "swashes")
        self.assertEqual(gc.glyphs, {"X.swash", "Y.swash", "Z.swash"})

    def test_glyphclass_range_lowercase(self):
        [gc] = self.parse("@defg.sc = [d.sc-g.sc];").statements
        self.assertEqual(gc.name, "defg.sc")
        self.assertEqual(gc.glyphs, {"d.sc", "e.sc", "f.sc", "g.sc"})

    def test_glyphclass_range_digit1(self):
        [gc] = self.parse("@range = [foo.2-foo.5];").statements
        self.assertEqual(gc.glyphs, {"foo.2", "foo.3", "foo.4", "foo.5"})

    def test_glyphclass_range_digit2(self):
        [gc] = self.parse("@range = [foo.09-foo.11];").statements
        self.assertEqual(gc.glyphs, {"foo.09", "foo.10", "foo.11"})

    def test_glyphclass_range_digit3(self):
        [gc] = self.parse("@range = [foo.123-foo.125];").statements
        self.assertEqual(gc.glyphs, {"foo.123", "foo.124", "foo.125"})

    def test_glyphclass_range_bad(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Bad range: \"a\" and \"foobar\" should have the same length",
            self.parse, "@bad = [a-foobar];")
        self.assertRaisesRegex(
            FeatureLibError, "Bad range: \"A.swash-z.swash\"",
            self.parse, "@bad = [A.swash-z.swash];")
        self.assertRaisesRegex(
            FeatureLibError, "Start of range must be smaller than its end",
            self.parse, "@bad = [B.swash-A.swash];")
        self.assertRaisesRegex(
            FeatureLibError, "Bad range: \"foo.1234-foo.9876\"",
            self.parse, "@bad = [foo.1234-foo.9876];")

    def test_glyphclass_range_mixed(self):
        [gc] = self.parse("@range = [a foo.09-foo.11 X.sc-Z.sc];").statements
        self.assertEqual(gc.glyphs, {
            "a", "foo.09", "foo.10", "foo.11", "X.sc", "Y.sc", "Z.sc"
        })

    def test_glyphclass_reference(self):
        [vowels_lc, vowels_uc, vowels] = self.parse(
            "@Vowels.lc = [a e i o u]; @Vowels.uc = [A E I O U];"
            "@Vowels = [@Vowels.lc @Vowels.uc y Y];").statements
        self.assertEqual(vowels_lc.glyphs, set(list("aeiou")))
        self.assertEqual(vowels_uc.glyphs, set(list("AEIOU")))
        self.assertEqual(vowels.glyphs, set(list("aeiouyAEIOUY")))
        self.assertRaisesRegex(
            FeatureLibError, "Unknown glyph class @unknown",
            self.parse, "@bad = [@unknown];")

    def test_glyphclass_scoping(self):
        [foo, liga, smcp] = self.parse(
            "@foo = [a b];"
            "feature liga { @bar = [@foo l]; } liga;"
            "feature smcp { @bar = [@foo s]; } smcp;"
        ).statements
        self.assertEqual(foo.glyphs, {"a", "b"})
        self.assertEqual(liga.statements[0].glyphs, {"a", "b", "l"})
        self.assertEqual(smcp.statements[0].glyphs, {"a", "b", "s"})

    def test_ignore_sub(self):
        doc = self.parse("feature test {ignore sub e t' c;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.IgnoreSubstitutionRule)
        self.assertEqual(s.prefix, [{"e"}])
        self.assertEqual(s.glyphs, [{"t"}])
        self.assertEqual(s.suffix, [{"c"}])

    def test_ignore_substitute(self):
        doc = self.parse(
            "feature test {"
            "    ignore substitute f [a e] d' [a u]' [e y];"
            "} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.IgnoreSubstitutionRule)
        self.assertEqual(s.prefix, [{"f"}, {"a", "e"}])
        self.assertEqual(s.glyphs, [{"d"}, {"a", "u"}])
        self.assertEqual(s.suffix, [{"e", "y"}])

    def test_language(self):
        doc = self.parse("feature test {language DEU;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU")
        self.assertTrue(s.include_default)
        self.assertFalse(s.required)

    def test_language_exclude_dflt(self):
        doc = self.parse("feature test {language DEU exclude_dflt;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU")
        self.assertFalse(s.include_default)
        self.assertFalse(s.required)

    def test_language_exclude_dflt_required(self):
        doc = self.parse("feature test {"
                         "  language DEU exclude_dflt required;"
                         "} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU")
        self.assertFalse(s.include_default)
        self.assertTrue(s.required)

    def test_language_include_dflt(self):
        doc = self.parse("feature test {language DEU include_dflt;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU")
        self.assertTrue(s.include_default)
        self.assertFalse(s.required)

    def test_language_include_dflt_required(self):
        doc = self.parse("feature test {"
                         "  language DEU include_dflt required;"
                         "} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU")
        self.assertTrue(s.include_default)
        self.assertTrue(s.required)

    def test_lookup_block(self):
        [lookup] = self.parse("lookup Ligatures {} Ligatures;").statements
        self.assertEqual(lookup.name, "Ligatures")
        self.assertFalse(lookup.use_extension)

    def test_lookup_block_useExtension(self):
        [lookup] = self.parse("lookup Foo useExtension {} Foo;").statements
        self.assertEqual(lookup.name, "Foo")
        self.assertTrue(lookup.use_extension)

    def test_lookup_block_name_mismatch(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Expected "Foo"',
            self.parse, "lookup Foo {} Bar;")

    def test_lookup_block_with_horizontal_valueRecordDef(self):
        doc = self.parse("feature liga {"
                         "  lookup look {"
                         "    valueRecordDef 123 foo;"
                         "  } look;"
                         "} liga;")
        [liga] = doc.statements
        [look] = liga.statements
        [foo] = look.statements
        self.assertEqual(foo.value.xAdvance, 123)
        self.assertEqual(foo.value.yAdvance, 0)

    def test_lookup_block_with_vertical_valueRecordDef(self):
        doc = self.parse("feature vkrn {"
                         "  lookup look {"
                         "    valueRecordDef 123 foo;"
                         "  } look;"
                         "} vkrn;")
        [vkrn] = doc.statements
        [look] = vkrn.statements
        [foo] = look.statements
        self.assertEqual(foo.value.xAdvance, 0)
        self.assertEqual(foo.value.yAdvance, 123)

    def test_lookup_reference(self):
        [foo, bar] = self.parse("lookup Foo {} Foo;"
                                "feature Bar {lookup Foo;} Bar;").statements
        [ref] = bar.statements
        self.assertEqual(type(ref), ast.LookupReferenceStatement)
        self.assertEqual(ref.lookup, foo)

    def test_lookup_reference_unknown(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Unknown lookup "Huh"',
            self.parse, "feature liga {lookup Huh;} liga;")

    def test_script(self):
        doc = self.parse("feature test {script cyrl;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.ScriptStatement)
        self.assertEqual(s.script, "cyrl")

    def test_substitute_single_format_a(self):  # GSUB LookupType 1
        doc = self.parse("feature smcp {substitute a by a.sc;} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(sub.old_prefix, [])
        self.assertEqual(sub.old, [{"a"}])
        self.assertEqual(sub.old_suffix, [])
        self.assertEqual(sub.new, [{"a.sc"}])
        self.assertEqual(sub.lookups, [None])

    def test_substitute_single_format_b(self):  # GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute [one.fitted one.oldstyle] by one;"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(sub.old_prefix, [])
        self.assertEqual(sub.old, [{"one.fitted", "one.oldstyle"}])
        self.assertEqual(sub.old_suffix, [])
        self.assertEqual(sub.new, [{"one"}])
        self.assertEqual(sub.lookups, [None])

    def test_substitute_single_format_c(self):  # GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute [a-d] by [A.sc-D.sc];"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(sub.old_prefix, [])
        self.assertEqual(sub.old, [{"a", "b", "c", "d"}])
        self.assertEqual(sub.old_suffix, [])
        self.assertEqual(sub.new, [{"A.sc", "B.sc", "C.sc", "D.sc"}])
        self.assertEqual(sub.lookups, [None])

    def test_substitute_multiple(self):  # GSUB LookupType 2
        doc = self.parse("lookup Look {substitute f_f_i by f f i;} Look;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(type(sub), ast.SubstitutionRule)
        self.assertEqual(sub.old_prefix, [])
        self.assertEqual(sub.old, [{"f_f_i"}])
        self.assertEqual(sub.old_suffix, [])
        self.assertEqual(sub.new, [{"f"}, {"f"}, {"i"}])
        self.assertEqual(sub.lookups, [None])

    def test_substitute_from(self):  # GSUB LookupType 3
        doc = self.parse("feature test {"
                         "  substitute a from [a.1 a.2 a.3];"
                         "} test;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(type(sub), ast.AlternateSubstitution)
        self.assertEqual(sub.glyph, "a")
        self.assertEqual(sub.from_class, {"a.1", "a.2", "a.3"})

    def test_substitute_from_glyphclass(self):  # GSUB LookupType 3
        doc = self.parse("feature test {"
                         "  @Ampersands = [ampersand.1 ampersand.2];"
                         "  substitute ampersand from @Ampersands;"
                         "} test;")
        [glyphclass, sub] = doc.statements[0].statements
        self.assertEqual(type(sub), ast.AlternateSubstitution)
        self.assertEqual(sub.glyph, "ampersand")
        self.assertEqual(sub.from_class, {"ampersand.1", "ampersand.2"})

    def test_substitute_ligature(self):  # GSUB LookupType 4
        doc = self.parse("feature liga {substitute f f i by f_f_i;} liga;")
        sub = doc.statements[0].statements[0]
        self.assertEqual(sub.old_prefix, [])
        self.assertEqual(sub.old, [{"f"}, {"f"}, {"i"}])
        self.assertEqual(sub.old_suffix, [])
        self.assertEqual(sub.new, [{"f_f_i"}])
        self.assertEqual(sub.lookups, [None, None, None])

    def test_substitute_lookups(self):
        doc = Parser(self.getpath("spec5fi.fea")).parse()
        [ligs, sub, feature] = doc.statements
        self.assertEqual(feature.statements[0].lookups, [ligs, None, sub])
        self.assertEqual(feature.statements[1].lookups, [ligs, None, sub])

    def test_substitute_missing_by(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'Expected "by", "from" or explicit lookup references',
            self.parse, "feature liga {substitute f f i;} liga;")

    def test_subtable(self):
        doc = self.parse("feature test {subtable;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.SubtableStatement)

    def test_valuerecord_format_a_horizontal(self):
        doc = self.parse("feature liga {valueRecordDef 123 foo;} liga;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 0)
        self.assertEqual(value.yPlacement, 0)
        self.assertEqual(value.xAdvance, 123)
        self.assertEqual(value.yAdvance, 0)

    def test_valuerecord_format_a_vertical(self):
        doc = self.parse("feature vkrn {valueRecordDef 123 foo;} vkrn;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 0)
        self.assertEqual(value.yPlacement, 0)
        self.assertEqual(value.xAdvance, 0)
        self.assertEqual(value.yAdvance, 123)

    def test_valuerecord_format_b(self):
        doc = self.parse("feature liga {valueRecordDef <1 2 3 4> foo;} liga;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 1)
        self.assertEqual(value.yPlacement, 2)
        self.assertEqual(value.xAdvance, 3)
        self.assertEqual(value.yAdvance, 4)

    def test_valuerecord_named(self):
        doc = self.parse("valueRecordDef <1 2 3 4> foo;"
                         "feature liga {valueRecordDef <foo> bar;} liga;")
        value = doc.statements[1].statements[0].value
        self.assertEqual(value.xPlacement, 1)
        self.assertEqual(value.yPlacement, 2)
        self.assertEqual(value.xAdvance, 3)
        self.assertEqual(value.yAdvance, 4)

    def test_valuerecord_named_unknown(self):
        self.assertRaisesRegex(
            FeatureLibError, "Unknown valueRecordDef \"unknown\"",
            self.parse, "valueRecordDef <unknown> foo;")

    def test_valuerecord_scoping(self):
        [foo, liga, smcp] = self.parse(
            "valueRecordDef 789 foo;"
            "feature liga {valueRecordDef <foo> bar;} liga;"
            "feature smcp {valueRecordDef <foo> bar;} smcp;"
        ).statements
        self.assertEqual(foo.value.xAdvance, 789)
        self.assertEqual(liga.statements[0].value.xAdvance, 789)
        self.assertEqual(smcp.statements[0].value.xAdvance, 789)

    def test_languagesystem(self):
        [langsys] = self.parse("languagesystem latn DEU;").statements
        self.assertEqual(langsys.script, "latn")
        self.assertEqual(langsys.language, "DEU ")
        self.assertRaisesRegex(
            FeatureLibError, "Expected ';'",
            self.parse, "languagesystem latn DEU")
        self.assertRaisesRegex(
            FeatureLibError, "longer than 4 characters",
            self.parse, "languagesystem foobar DEU")
        self.assertRaisesRegex(
            FeatureLibError, "longer than 4 characters",
            self.parse, "languagesystem latn FOOBAR")

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

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", testfile)


class SymbolTableTest(unittest.TestCase):
    def test_scopes(self):
        symtab = SymbolTable()
        symtab.define("foo", 23)
        self.assertEqual(symtab.resolve("foo"), 23)
        symtab.enter_scope()
        self.assertEqual(symtab.resolve("foo"), 23)
        symtab.define("foo", 42)
        self.assertEqual(symtab.resolve("foo"), 42)
        symtab.exit_scope()
        self.assertEqual(symtab.resolve("foo"), 23)

    def test_resolve_undefined(self):
        self.assertEqual(SymbolTable().resolve("abc"), None)


if __name__ == "__main__":
    unittest.main()
