from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser, SymbolTable
from fontTools.misc.py23 import *
import fontTools.feaLib.ast as ast
import os
import shutil
import sys
import tempfile
import unittest


def glyphstr(glyphs):
    def f(x):
        if len(x) == 1:
            return list(x)[0]
        else:
            return '[%s]' % ' '.join(sorted(list(x)))
    return ' '.join([f(g.glyphSet()) for g in glyphs])


class ParserTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_anchor_format_a(self):
        doc = self.parse(
            "feature test {"
            "    pos cursive A <anchor 120 -20> <anchor NULL>;"
            "} test;")
        anchor = doc.statements[0].statements[0].entryAnchor
        self.assertEqual(type(anchor), ast.Anchor)
        self.assertEqual(anchor.x, 120)
        self.assertEqual(anchor.y, -20)
        self.assertIsNone(anchor.contourpoint)
        self.assertIsNone(anchor.xDeviceTable)
        self.assertIsNone(anchor.yDeviceTable)

    def test_anchor_format_b(self):
        doc = self.parse(
            "feature test {"
            "    pos cursive A <anchor 120 -20 contourpoint 5> <anchor NULL>;"
            "} test;")
        anchor = doc.statements[0].statements[0].entryAnchor
        self.assertEqual(type(anchor), ast.Anchor)
        self.assertEqual(anchor.x, 120)
        self.assertEqual(anchor.y, -20)
        self.assertEqual(anchor.contourpoint, 5)
        self.assertIsNone(anchor.xDeviceTable)
        self.assertIsNone(anchor.yDeviceTable)

    def test_anchor_format_c(self):
        doc = self.parse(
            "feature test {"
            "    pos cursive A "
            "        <anchor 120 -20 <device 11 111, 12 112> <device NULL>>"
            "        <anchor NULL>;"
            "} test;")
        anchor = doc.statements[0].statements[0].entryAnchor
        self.assertEqual(type(anchor), ast.Anchor)
        self.assertEqual(anchor.x, 120)
        self.assertEqual(anchor.y, -20)
        self.assertIsNone(anchor.contourpoint)
        self.assertEqual(anchor.xDeviceTable, ((11, 111), (12, 112)))
        self.assertIsNone(anchor.yDeviceTable)

    def test_anchor_format_d(self):
        doc = self.parse(
            "feature test {"
            "    pos cursive A <anchor 120 -20> <anchor NULL>;"
            "} test;")
        anchor = doc.statements[0].statements[0].exitAnchor
        self.assertIsNone(anchor)

    def test_anchor_format_e(self):
        doc = self.parse(
            "feature test {"
            "    anchorDef 120 -20 contourpoint 7 Foo;"
            "    pos cursive A <anchor Foo> <anchor NULL>;"
            "} test;")
        anchor = doc.statements[0].statements[1].entryAnchor
        self.assertEqual(type(anchor), ast.Anchor)
        self.assertEqual(anchor.x, 120)
        self.assertEqual(anchor.y, -20)
        self.assertEqual(anchor.contourpoint, 7)
        self.assertIsNone(anchor.xDeviceTable)
        self.assertIsNone(anchor.yDeviceTable)

    def test_anchor_format_e_undefined(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Unknown anchor "UnknownName"', self.parse,
            "feature test {"
            "    position cursive A <anchor UnknownName> <anchor NULL>;"
            "} test;")

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

    def test_attach(self):
        doc = self.parse("table GDEF {Attach [a e] 2;} GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.AttachStatement)
        self.assertEqual(glyphstr([s.glyphs]), "[a e]")
        self.assertEqual(s.contourPoints, {2})

    def test_feature_block(self):
        [liga] = self.parse("feature liga {} liga;").statements
        self.assertEqual(liga.name, "liga")
        self.assertFalse(liga.use_extension)

    def test_feature_block_useExtension(self):
        [liga] = self.parse("feature liga useExtension {} liga;").statements
        self.assertEqual(liga.name, "liga")
        self.assertTrue(liga.use_extension)

    def test_feature_reference(self):
        doc = self.parse("feature aalt { feature salt; } aalt;")
        ref = doc.statements[0].statements[0]
        self.assertIsInstance(ref, ast.FeatureReferenceStatement)
        self.assertEqual(ref.featureName, "salt")

    def test_FontRevision(self):
        doc = self.parse("table head {FontRevision 2.5;} head;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.FontRevisionStatement)
        self.assertEqual(s.revision, 2.5)

    def test_FontRevision_negative(self):
        self.assertRaisesRegex(
            FeatureLibError, "Font revision numbers must be positive",
            self.parse, "table head {FontRevision -17.2;} head;")

    def test_glyphclass(self):
        [gc] = self.parse("@dash = [endash emdash figuredash];").statements
        self.assertEqual(gc.name, "dash")
        self.assertEqual(gc.glyphs, {"endash", "emdash", "figuredash"})

    def test_glyphclass_glyphNameTooLong(self):
        self.assertRaisesRegex(
            FeatureLibError, "must not be longer than 63 characters",
            self.parse, "@GlyphClass = [%s];" % ("G" * 64))

    def test_glyphclass_bad(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Expected glyph name, glyph range, or glyph class reference",
            self.parse, "@bad = [a 123];")

    def test_glyphclass_duplicate(self):
        # makeotf accepts this, so we should too
        ab, xy = self.parse("@dup = [a b]; @dup = [x y];").statements
        self.assertEqual(glyphstr([ab]), "[a b]")
        self.assertEqual(glyphstr([xy]), "[x y]")

    def test_glyphclass_empty(self):
        [gc] = self.parse("@empty_set = [];").statements
        self.assertEqual(gc.name, "empty_set")
        self.assertEqual(gc.glyphs, set())

    def test_glyphclass_equality(self):
        [foo, bar] = self.parse("@foo = [a b]; @bar = @foo;").statements
        self.assertEqual(foo.glyphs, {"a", "b"})
        self.assertEqual(bar.glyphs, {"a", "b"})

    def test_glyphclass_from_markClass(self):
        doc = self.parse(
            "markClass [acute grave] <anchor 500 800> @TOP_MARKS;"
            "markClass cedilla <anchor 500 -100> @BOTTOM_MARKS;"
            "@MARKS = [@TOP_MARKS @BOTTOM_MARKS ogonek];"
            "@ALL = @MARKS;")
        self.assertEqual(doc.statements[-1].glyphSet(),
                         {"acute", "cedilla", "grave", "ogonek"})

    def test_glyphclass_range_cid(self):
        [gc] = self.parse(r"@GlyphClass = [\999-\1001];").statements
        self.assertEqual(gc.name, "GlyphClass")
        self.assertEqual(gc.glyphs, {"cid00999", "cid01000", "cid01001"})

    def test_glyphclass_range_cid_bad(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Bad range: start should be less than limit",
            self.parse, r"@bad = [\998-\995];")

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

    def test_glyphclass_scoping_bug496(self):
        # https://github.com/behdad/fonttools/issues/496
        f1, f2 = self.parse(
            "feature F1 { lookup L { @GLYPHCLASS = [A B C];} L; } F1;"
            "feature F2 { sub @GLYPHCLASS by D; } F2;"
        ).statements
        self.assertEqual(set(f2.statements[0].mapping.keys()), {"A", "B", "C"})

    def test_GlyphClassDef(self):
        doc = self.parse("table GDEF {GlyphClassDef [b],[l],[m],[C c];} GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.GlyphClassDefStatement)
        self.assertEqual(glyphstr([s.baseGlyphs]), "b")
        self.assertEqual(glyphstr([s.ligatureGlyphs]), "l")
        self.assertEqual(glyphstr([s.markGlyphs]), "m")
        self.assertEqual(glyphstr([s.componentGlyphs]), "[C c]")

    def test_GlyphClassDef_noCLassesSpecified(self):
        doc = self.parse("table GDEF {GlyphClassDef ,,,;} GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsNone(s.baseGlyphs)
        self.assertIsNone(s.ligatureGlyphs)
        self.assertIsNone(s.markGlyphs)
        self.assertIsNone(s.componentGlyphs)

    def test_ignore_pos(self):
        doc = self.parse("feature test {ignore pos e t' c, q u' u' x;} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.IgnorePosStatement)
        [(pref1, glyphs1, suff1), (pref2, glyphs2, suff2)] = sub.chainContexts
        self.assertEqual(glyphstr(pref1), "e")
        self.assertEqual(glyphstr(glyphs1), "t")
        self.assertEqual(glyphstr(suff1), "c")
        self.assertEqual(glyphstr(pref2), "q")
        self.assertEqual(glyphstr(glyphs2), "u u")
        self.assertEqual(glyphstr(suff2), "x")

    def test_ignore_position(self):
        doc = self.parse(
            "feature test {"
            "    ignore position f [a e] d' [a u]' [e y];"
            "} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.IgnorePosStatement)
        [(prefix, glyphs, suffix)] = sub.chainContexts
        self.assertEqual(glyphstr(prefix), "f [a e]")
        self.assertEqual(glyphstr(glyphs), "d [a u]")
        self.assertEqual(glyphstr(suffix), "[e y]")

    def test_ignore_position_with_lookup(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'No lookups can be specified for "ignore pos"',
            self.parse,
            "lookup L { pos [A A.sc] -100; } L;"
            "feature test { ignore pos f' i', A' lookup L; } test;")

    def test_ignore_sub(self):
        doc = self.parse("feature test {ignore sub e t' c, q u' u' x;} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.IgnoreSubstStatement)
        [(pref1, glyphs1, suff1), (pref2, glyphs2, suff2)] = sub.chainContexts
        self.assertEqual(glyphstr(pref1), "e")
        self.assertEqual(glyphstr(glyphs1), "t")
        self.assertEqual(glyphstr(suff1), "c")
        self.assertEqual(glyphstr(pref2), "q")
        self.assertEqual(glyphstr(glyphs2), "u u")
        self.assertEqual(glyphstr(suff2), "x")

    def test_ignore_substitute(self):
        doc = self.parse(
            "feature test {"
            "    ignore substitute f [a e] d' [a u]' [e y];"
            "} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.IgnoreSubstStatement)
        [(prefix, glyphs, suffix)] = sub.chainContexts
        self.assertEqual(glyphstr(prefix), "f [a e]")
        self.assertEqual(glyphstr(glyphs), "d [a u]")
        self.assertEqual(glyphstr(suffix), "[e y]")

    def test_ignore_substitute_with_lookup(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'No lookups can be specified for "ignore sub"',
            self.parse,
            "lookup L { sub [A A.sc] by a; } L;"
            "feature test { ignore sub f' i', A' lookup L; } test;")

    def test_language(self):
        doc = self.parse("feature test {language DEU;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU ")
        self.assertTrue(s.include_default)
        self.assertFalse(s.required)

    def test_language_exclude_dflt(self):
        doc = self.parse("feature test {language DEU exclude_dflt;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU ")
        self.assertFalse(s.include_default)
        self.assertFalse(s.required)

    def test_language_exclude_dflt_required(self):
        doc = self.parse("feature test {"
                         "  language DEU exclude_dflt required;"
                         "} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU ")
        self.assertFalse(s.include_default)
        self.assertTrue(s.required)

    def test_language_include_dflt(self):
        doc = self.parse("feature test {language DEU include_dflt;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU ")
        self.assertTrue(s.include_default)
        self.assertFalse(s.required)

    def test_language_include_dflt_required(self):
        doc = self.parse("feature test {"
                         "  language DEU include_dflt required;"
                         "} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.LanguageStatement)
        self.assertEqual(s.language, "DEU ")
        self.assertTrue(s.include_default)
        self.assertTrue(s.required)

    def test_language_DFLT(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"DFLT" is not a valid language tag; use "dflt" instead',
            self.parse, "feature test { language DFLT; } test;")

    def test_ligatureCaretByIndex_glyphClass(self):
        doc = self.parse("table GDEF{LigatureCaretByIndex [c_t f_i] 2;}GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.LigatureCaretByIndexStatement)
        self.assertEqual(glyphstr([s.glyphs]), "[c_t f_i]")
        self.assertEqual(s.carets, {2})

    def test_ligatureCaretByIndex_singleGlyph(self):
        doc = self.parse("table GDEF{LigatureCaretByIndex f_f_i 3 7;}GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.LigatureCaretByIndexStatement)
        self.assertEqual(glyphstr([s.glyphs]), "f_f_i")
        self.assertEqual(s.carets, {3, 7})

    def test_ligatureCaretByPos_glyphClass(self):
        doc = self.parse("table GDEF {LigatureCaretByPos [c_t f_i] 7;} GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.LigatureCaretByPosStatement)
        self.assertEqual(glyphstr([s.glyphs]), "[c_t f_i]")
        self.assertEqual(s.carets, {7})

    def test_ligatureCaretByPos_singleGlyph(self):
        doc = self.parse("table GDEF {LigatureCaretByPos f_i 400 380;} GDEF;")
        s = doc.statements[0].statements[0]
        self.assertIsInstance(s, ast.LigatureCaretByPosStatement)
        self.assertEqual(glyphstr([s.glyphs]), "f_i")
        self.assertEqual(s.carets, {380, 400})

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

    def test_lookup_reference_to_lookup_inside_feature(self):
        [qux, bar] = self.parse("feature Qux {lookup Foo {} Foo;} Qux;"
                                "feature Bar {lookup Foo;} Bar;").statements
        [foo] = qux.statements
        [ref] = bar.statements
        self.assertIsInstance(ref, ast.LookupReferenceStatement)
        self.assertEqual(ref.lookup, foo)

    def test_lookup_reference_unknown(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Unknown lookup "Huh"',
            self.parse, "feature liga {lookup Huh;} liga;")

    def parse_lookupflag_(self, s):
        return self.parse("lookup L {%s} L;" % s).statements[0].statements[-1]

    def test_lookupflag_format_A(self):
        flag = self.parse_lookupflag_("lookupflag RightToLeft IgnoreMarks;")
        self.assertIsInstance(flag, ast.LookupFlagStatement)
        self.assertEqual(flag.value, 9)
        self.assertIsNone(flag.markAttachment)
        self.assertIsNone(flag.markFilteringSet)

    def test_lookupflag_format_A_MarkAttachmentType(self):
        flag = self.parse_lookupflag_(
            "@TOP_MARKS = [acute grave macron];"
            "lookupflag RightToLeft MarkAttachmentType @TOP_MARKS;")
        self.assertIsInstance(flag, ast.LookupFlagStatement)
        self.assertEqual(flag.value, 1)
        self.assertIsInstance(flag.markAttachment, ast.GlyphClassName)
        self.assertEqual(flag.markAttachment.glyphSet(),
                         {"acute", "grave", "macron"})
        self.assertIsNone(flag.markFilteringSet)

    def test_lookupflag_format_A_UseMarkFilteringSet(self):
        flag = self.parse_lookupflag_(
            "@BOTTOM_MARKS = [cedilla ogonek];"
            "lookupflag UseMarkFilteringSet @BOTTOM_MARKS IgnoreLigatures;")
        self.assertIsInstance(flag, ast.LookupFlagStatement)
        self.assertEqual(flag.value, 4)
        self.assertIsNone(flag.markAttachment)
        self.assertIsInstance(flag.markFilteringSet, ast.GlyphClassName)
        self.assertEqual(flag.markFilteringSet.glyphSet(),
                         {"cedilla", "ogonek"})

    def test_lookupflag_format_B(self):
        flag = self.parse_lookupflag_("lookupflag 7;")
        self.assertIsInstance(flag, ast.LookupFlagStatement)
        self.assertEqual(flag.value, 7)
        self.assertIsNone(flag.markAttachment)
        self.assertIsNone(flag.markFilteringSet)

    def test_lookupflag_repeated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'RightToLeft can be specified only once',
            self.parse,
            "feature test {lookupflag RightToLeft RightToLeft;} test;")

    def test_lookupflag_unrecognized(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"IgnoreCookies" is not a recognized lookupflag',
            self.parse, "feature test {lookupflag IgnoreCookies;} test;")

    def test_gpos_type_1_glyph(self):
        doc = self.parse("feature kern {pos one <1 2 3 4>;} kern;")
        pos = doc.statements[0].statements[0]
        self.assertIsInstance(pos, ast.SinglePosStatement)
        [(glyphs, value)] = pos.pos
        self.assertEqual(glyphstr([glyphs]), "one")
        self.assertEqual(value.makeString(vertical=False), "<1 2 3 4>")

    def test_gpos_type_1_glyphclass_horizontal(self):
        doc = self.parse("feature kern {pos [one two] -300;} kern;")
        pos = doc.statements[0].statements[0]
        self.assertIsInstance(pos, ast.SinglePosStatement)
        [(glyphs, value)] = pos.pos
        self.assertEqual(glyphstr([glyphs]), "[one two]")
        self.assertEqual(value.makeString(vertical=False), "-300")

    def test_gpos_type_1_glyphclass_vertical(self):
        doc = self.parse("feature vkrn {pos [one two] -300;} vkrn;")
        pos = doc.statements[0].statements[0]
        self.assertIsInstance(pos, ast.SinglePosStatement)
        [(glyphs, value)] = pos.pos
        self.assertEqual(glyphstr([glyphs]), "[one two]")
        self.assertEqual(value.makeString(vertical=True), "-300")

    def test_gpos_type_1_multiple(self):
        doc = self.parse("feature f {pos one'1 two'2 [five six]'56;} f;")
        pos = doc.statements[0].statements[0]
        self.assertIsInstance(pos, ast.SinglePosStatement)
        [(glyphs1, val1), (glyphs2, val2), (glyphs3, val3)] = pos.pos
        self.assertEqual(glyphstr([glyphs1]), "one")
        self.assertEqual(val1.makeString(vertical=False), "1")
        self.assertEqual(glyphstr([glyphs2]), "two")
        self.assertEqual(val2.makeString(vertical=False), "2")
        self.assertEqual(glyphstr([glyphs3]), "[five six]")
        self.assertEqual(val3.makeString(vertical=False), "56")
        self.assertEqual(pos.prefix, [])
        self.assertEqual(pos.suffix, [])

    def test_gpos_type_1_enumerated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is only allowed with pair positionings',
            self.parse, "feature test {enum pos T 100;} test;")
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is only allowed with pair positionings',
            self.parse, "feature test {enumerate pos T 100;} test;")

    def test_gpos_type_1_chained(self):
        doc = self.parse("feature kern {pos [A B] [T Y]' 20 comma;} kern;")
        pos = doc.statements[0].statements[0]
        self.assertIsInstance(pos, ast.SinglePosStatement)
        [(glyphs, value)] = pos.pos
        self.assertEqual(glyphstr([glyphs]), "[T Y]")
        self.assertEqual(value.makeString(vertical=False), "20")
        self.assertEqual(glyphstr(pos.prefix), "[A B]")
        self.assertEqual(glyphstr(pos.suffix), "comma")

    def test_gpos_type_2_format_a(self):
        doc = self.parse("feature kern {"
                         "    pos [T V] -60 [a b c] <1 2 3 4>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.PairPosStatement)
        self.assertFalse(pos.enumerated)
        self.assertEqual(glyphstr([pos.glyphs1]), "[T V]")
        self.assertEqual(pos.valuerecord1.makeString(vertical=False), "-60")
        self.assertEqual(glyphstr([pos.glyphs2]), "[a b c]")
        self.assertEqual(pos.valuerecord2.makeString(vertical=False),
                         "<1 2 3 4>")

    def test_gpos_type_2_format_a_enumerated(self):
        doc = self.parse("feature kern {"
                         "    enum pos [T V] -60 [a b c] <1 2 3 4>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.PairPosStatement)
        self.assertTrue(pos.enumerated)
        self.assertEqual(glyphstr([pos.glyphs1]), "[T V]")
        self.assertEqual(pos.valuerecord1.makeString(vertical=False), "-60")
        self.assertEqual(glyphstr([pos.glyphs2]), "[a b c]")
        self.assertEqual(pos.valuerecord2.makeString(vertical=False),
                         "<1 2 3 4>")

    def test_gpos_type_2_format_a_with_null(self):
        doc = self.parse("feature kern {"
                         "    pos [T V] <1 2 3 4> [a b c] <NULL>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.PairPosStatement)
        self.assertFalse(pos.enumerated)
        self.assertEqual(glyphstr([pos.glyphs1]), "[T V]")
        self.assertEqual(pos.valuerecord1.makeString(vertical=False),
                         "<1 2 3 4>")
        self.assertEqual(glyphstr([pos.glyphs2]), "[a b c]")
        self.assertIsNone(pos.valuerecord2)

    def test_gpos_type_2_format_b(self):
        doc = self.parse("feature kern {"
                         "    pos [T V] [a b c] <1 2 3 4>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.PairPosStatement)
        self.assertFalse(pos.enumerated)
        self.assertEqual(glyphstr([pos.glyphs1]), "[T V]")
        self.assertEqual(pos.valuerecord1.makeString(vertical=False),
                         "<1 2 3 4>")
        self.assertEqual(glyphstr([pos.glyphs2]), "[a b c]")
        self.assertIsNone(pos.valuerecord2)

    def test_gpos_type_2_format_b_enumerated(self):
        doc = self.parse("feature kern {"
                         "    enumerate position [T V] [a b c] <1 2 3 4>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.PairPosStatement)
        self.assertTrue(pos.enumerated)
        self.assertEqual(glyphstr([pos.glyphs1]), "[T V]")
        self.assertEqual(pos.valuerecord1.makeString(vertical=False),
                         "<1 2 3 4>")
        self.assertEqual(glyphstr([pos.glyphs2]), "[a b c]")
        self.assertIsNone(pos.valuerecord2)

    def test_gpos_type_3(self):
        doc = self.parse("feature kern {"
                         "    position cursive A <anchor 12 -2> <anchor 2 3>;"
                         "} kern;")
        pos = doc.statements[0].statements[0]
        self.assertEqual(type(pos), ast.CursivePosStatement)
        self.assertEqual(pos.glyphclass, {"A"})
        self.assertEqual((pos.entryAnchor.x, pos.entryAnchor.y), (12, -2))
        self.assertEqual((pos.exitAnchor.x, pos.exitAnchor.y), (2, 3))

    def test_gpos_type_3_enumerated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is not allowed with cursive attachment positioning',
            self.parse,
            "feature kern {"
            "    enumerate position cursive A <anchor 12 -2> <anchor 2 3>;"
            "} kern;")

    def test_gpos_type_4(self):
        doc = self.parse(
            "markClass [acute grave] <anchor 150 -10> @TOP_MARKS;"
            "markClass [dieresis umlaut] <anchor 300 -10> @TOP_MARKS;"
            "markClass [cedilla] <anchor 300 600> @BOTTOM_MARKS;"
            "feature test {"
            "    position base [a e o u] "
            "        <anchor 250 450> mark @TOP_MARKS "
            "        <anchor 210 -10> mark @BOTTOM_MARKS;"
            "} test;")
        pos = doc.statements[-1].statements[0]
        self.assertEqual(type(pos), ast.MarkBasePosStatement)
        self.assertEqual(pos.base, {"a", "e", "o", "u"})
        (a1, m1), (a2, m2) = pos.marks
        self.assertEqual((a1.x, a1.y, m1.name), (250, 450, "TOP_MARKS"))
        self.assertEqual((a2.x, a2.y, m2.name), (210, -10, "BOTTOM_MARKS"))

    def test_gpos_type_4_enumerated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is not allowed with '
            'mark-to-base attachment positioning',
            self.parse,
            "feature kern {"
            "    markClass cedilla <anchor 300 600> @BOTTOM_MARKS;"
            "    enumerate position base A <anchor 12 -2> mark @BOTTOM_MARKS;"
            "} kern;")

    def test_gpos_type_4_not_markClass(self):
        self.assertRaisesRegex(
            FeatureLibError, "@MARKS is not a markClass", self.parse,
            "@MARKS = [acute grave];"
            "feature test {"
            "    position base [a e o u] <anchor 250 450> mark @MARKS;"
            "} test;")

    def test_gpos_type_5(self):
        doc = self.parse(
            "markClass [grave acute] <anchor 150 500> @TOP_MARKS;"
            "markClass [cedilla] <anchor 300 -100> @BOTTOM_MARKS;"
            "feature test {"
            "    position "
            "        ligature [a_f_f_i o_f_f_i] "
            "            <anchor 50 600> mark @TOP_MARKS "
            "            <anchor 50 -10> mark @BOTTOM_MARKS "
            "        ligComponent "
            "            <anchor 30 800> mark @TOP_MARKS "
            "        ligComponent "
            "            <anchor NULL> "
            "        ligComponent "
            "            <anchor 30 -10> mark @BOTTOM_MARKS;"
            "} test;")
        pos = doc.statements[-1].statements[0]
        self.assertEqual(type(pos), ast.MarkLigPosStatement)
        self.assertEqual(pos.ligatures, {"a_f_f_i", "o_f_f_i"})
        [(a11, m11), (a12, m12)], [(a2, m2)], [], [(a4, m4)] = pos.marks
        self.assertEqual((a11.x, a11.y, m11.name), (50, 600, "TOP_MARKS"))
        self.assertEqual((a12.x, a12.y, m12.name), (50, -10, "BOTTOM_MARKS"))
        self.assertEqual((a2.x, a2.y, m2.name), (30, 800, "TOP_MARKS"))
        self.assertEqual((a4.x, a4.y, m4.name), (30, -10, "BOTTOM_MARKS"))

    def test_gpos_type_5_enumerated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is not allowed with '
            'mark-to-ligature attachment positioning',
            self.parse,
            "feature test {"
            "    markClass cedilla <anchor 300 600> @MARKS;"
            "    enumerate position "
            "        ligature f_i <anchor 100 0> mark @MARKS"
            "        ligComponent <anchor NULL>;"
            "} test;")

    def test_gpos_type_5_not_markClass(self):
        self.assertRaisesRegex(
            FeatureLibError, "@MARKS is not a markClass", self.parse,
            "@MARKS = [acute grave];"
            "feature test {"
            "    position ligature f_i <anchor 250 450> mark @MARKS;"
            "} test;")

    def test_gpos_type_6(self):
        doc = self.parse(
            "markClass damma <anchor 189 -103> @MARK_CLASS_1;"
            "feature test {"
            "    position mark hamza <anchor 221 301> mark @MARK_CLASS_1;"
            "} test;")
        pos = doc.statements[-1].statements[0]
        self.assertEqual(type(pos), ast.MarkMarkPosStatement)
        self.assertEqual(pos.baseMarks, {"hamza"})
        [(a1, m1)] = pos.marks
        self.assertEqual((a1.x, a1.y, m1.name), (221, 301, "MARK_CLASS_1"))

    def test_gpos_type_6_enumerated(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"enumerate" is not allowed with '
            'mark-to-mark attachment positioning',
            self.parse,
            "markClass damma <anchor 189 -103> @MARK_CLASS_1;"
            "feature test {"
            "    enum pos mark hamza <anchor 221 301> mark @MARK_CLASS_1;"
            "} test;")

    def test_gpos_type_6_not_markClass(self):
        self.assertRaisesRegex(
            FeatureLibError, "@MARKS is not a markClass", self.parse,
            "@MARKS = [acute grave];"
            "feature test {"
            "    position mark cedilla <anchor 250 450> mark @MARKS;"
            "} test;")

    def test_gpos_type_8(self):
        doc = self.parse(
            "lookup L1 {pos one 100;} L1; lookup L2 {pos two 200;} L2;"
            "feature test {"
            "    pos [A a] [B b] I' lookup L1 [N n]' lookup L2 P' [Y y] [Z z];"
            "} test;")
        lookup1, lookup2 = doc.statements[0:2]
        pos = doc.statements[-1].statements[0]
        self.assertEqual(type(pos), ast.ChainContextPosStatement)
        self.assertEqual(glyphstr(pos.prefix), "[A a] [B b]")
        self.assertEqual(glyphstr(pos.glyphs), "I [N n] P")
        self.assertEqual(glyphstr(pos.suffix), "[Y y] [Z z]")
        self.assertEqual(pos.lookups, [lookup1, lookup2, None])

    def test_gpos_type_8_lookup_with_values(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'If "lookup" is present, no values must be specified',
            self.parse,
            "lookup L1 {pos one 100;} L1;"
            "feature test {"
            "    pos A' lookup L1 B' 20;"
            "} test;")

    def test_markClass(self):
        doc = self.parse("markClass [acute grave] <anchor 350 3> @MARKS;")
        mc = doc.statements[0]
        self.assertIsInstance(mc, ast.MarkClassDefinition)
        self.assertEqual(mc.markClass.name, "MARKS")
        self.assertEqual(mc.glyphSet(), {"acute", "grave"})
        self.assertEqual((mc.anchor.x, mc.anchor.y), (350, 3))

    def test_rsub_format_a(self):
        doc = self.parse("feature test {rsub a [b B] c' d [e E] by C;} test;")
        rsub = doc.statements[0].statements[0]
        self.assertEqual(type(rsub), ast.ReverseChainSingleSubstStatement)
        self.assertEqual(glyphstr(rsub.old_prefix), "a [B b]")
        self.assertEqual(rsub.mapping, {"c": "C"})
        self.assertEqual(glyphstr(rsub.old_suffix), "d [E e]")

    def test_rsub_format_a_cid(self):
        doc = self.parse(r"feature test {rsub \1 [\2 \3] \4' \5 by \6;} test;")
        rsub = doc.statements[0].statements[0]
        self.assertEqual(type(rsub), ast.ReverseChainSingleSubstStatement)
        self.assertEqual(glyphstr(rsub.old_prefix),
                         "cid00001 [cid00002 cid00003]")
        self.assertEqual(rsub.mapping, {"cid00004": "cid00006"})
        self.assertEqual(glyphstr(rsub.old_suffix), "cid00005")

    def test_rsub_format_b(self):
        doc = self.parse(
            "feature smcp {"
            "    reversesub A B [one.fitted one.oldstyle]' C [d D] by one;"
            "} smcp;")
        rsub = doc.statements[0].statements[0]
        self.assertEqual(type(rsub), ast.ReverseChainSingleSubstStatement)
        self.assertEqual(glyphstr(rsub.old_prefix), "A B")
        self.assertEqual(glyphstr(rsub.old_suffix), "C [D d]")
        self.assertEqual(rsub.mapping, {
            "one.fitted": "one",
            "one.oldstyle": "one"
        })

    def test_rsub_format_c(self):
        doc = self.parse(
            "feature test {"
            "    reversesub BACK TRACK [a-d]' LOOK AHEAD by [A.sc-D.sc];"
            "} test;")
        rsub = doc.statements[0].statements[0]
        self.assertEqual(type(rsub), ast.ReverseChainSingleSubstStatement)
        self.assertEqual(glyphstr(rsub.old_prefix), "BACK TRACK")
        self.assertEqual(glyphstr(rsub.old_suffix), "LOOK AHEAD")
        self.assertEqual(rsub.mapping, {
            "a": "A.sc",
            "b": "B.sc",
            "c": "C.sc",
            "d": "D.sc"
        })

    def test_rsub_from(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'Reverse chaining substitutions do not support "from"',
            self.parse, "feature test {rsub a from [a.1 a.2 a.3];} test;")

    def test_rsub_nonsingle(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "In reverse chaining single substitutions, only a single glyph "
            "or glyph class can be replaced",
            self.parse, "feature test {rsub c d by c_d;} test;")

    def test_rsub_multiple_replacement_glyphs(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'In reverse chaining single substitutions, the replacement '
            '\(after "by"\) must be a single glyph or glyph class',
            self.parse, "feature test {rsub f_i by f i;} test;")

    def test_script(self):
        doc = self.parse("feature test {script cyrl;} test;")
        s = doc.statements[0].statements[0]
        self.assertEqual(type(s), ast.ScriptStatement)
        self.assertEqual(s.script, "cyrl")

    def test_script_dflt(self):
        self.assertRaisesRegex(
            FeatureLibError,
            '"dflt" is not a valid script tag; use "DFLT" instead',
            self.parse, "feature test {script dflt;} test;")

    def test_sub_single_format_a(self):  # GSUB LookupType 1
        doc = self.parse("feature smcp {substitute a by a.sc;} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(sub.mapping, {"a": "a.sc"})
        self.assertEqual(glyphstr(sub.suffix), "")

    def test_sub_single_format_a_chained(self):  # chain to GSUB LookupType 1
        doc = self.parse("feature test {sub [A a] d' [C] by d.alt;} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(sub.mapping, {"d": "d.alt"})
        self.assertEqual(glyphstr(sub.prefix), "[A a]")
        self.assertEqual(glyphstr(sub.suffix), "C")

    def test_sub_single_format_a_cid(self):  # GSUB LookupType 1
        doc = self.parse(r"feature smcp {substitute \12345 by \78987;} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(sub.mapping, {"cid12345": "cid78987"})
        self.assertEqual(glyphstr(sub.suffix), "")

    def test_sub_single_format_b(self):  # GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute [one.fitted one.oldstyle] by one;"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(sub.mapping, {
            "one.fitted": "one",
            "one.oldstyle": "one"
        })
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr(sub.suffix), "")

    def test_sub_single_format_b_chained(self):  # chain to GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute PRE FIX [one.fitted one.oldstyle]' SUF FIX by one;"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(sub.mapping, {
            "one.fitted": "one",
            "one.oldstyle": "one"
        })
        self.assertEqual(glyphstr(sub.prefix), "PRE FIX")
        self.assertEqual(glyphstr(sub.suffix), "SUF FIX")

    def test_sub_single_format_c(self):  # GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute [a-d] by [A.sc-D.sc];"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(sub.mapping, {
            "a": "A.sc",
            "b": "B.sc",
            "c": "C.sc",
            "d": "D.sc"
        })
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr(sub.suffix), "")

    def test_sub_single_format_c_chained(self):  # chain to GSUB LookupType 1
        doc = self.parse(
            "feature smcp {"
            "    substitute [a-d]' X Y [Z z] by [A.sc-D.sc];"
            "} smcp;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.SingleSubstStatement)
        self.assertEqual(sub.mapping, {
            "a": "A.sc",
            "b": "B.sc",
            "c": "C.sc",
            "d": "D.sc"
        })
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr(sub.suffix), "X Y [Z z]")

    def test_sub_single_format_c_different_num_elements(self):
        self.assertRaisesRegex(
            FeatureLibError,
            'Expected a glyph class with 4 elements after "by", '
            'but found a glyph class with 26 elements',
            self.parse, "feature smcp {sub [a-d] by [A.sc-Z.sc];} smcp;")

    def test_sub_with_values(self):
        self.assertRaisesRegex(
            FeatureLibError,
            "Substitution statements cannot contain values",
            self.parse, "feature smcp {sub A' 20 by A.sc;} smcp;")

    def test_substitute_multiple(self):  # GSUB LookupType 2
        doc = self.parse("lookup Look {substitute f_f_i by f f i;} Look;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.MultipleSubstStatement)
        self.assertEqual(sub.glyph, "f_f_i")
        self.assertEqual(sub.replacement, ("f", "f", "i"))

    def test_substitute_multiple_chained(self):  # chain to GSUB LookupType 2
        doc = self.parse("lookup L {sub [A-C] f_f_i' [X-Z] by f f i;} L;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.MultipleSubstStatement)
        self.assertEqual(sub.glyph, "f_f_i")
        self.assertEqual(sub.replacement, ("f", "f", "i"))

    def test_substitute_from(self):  # GSUB LookupType 3
        doc = self.parse("feature test {"
                         "  substitute a from [a.1 a.2 a.3];"
                         "} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.AlternateSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr([sub.glyph]), "a")
        self.assertEqual(glyphstr(sub.suffix), "")
        self.assertEqual(glyphstr([sub.replacement]), "[a.1 a.2 a.3]")

    def test_substitute_from_chained(self):  # chain to GSUB LookupType 3
        doc = self.parse("feature test {"
                         "  substitute A B a' [Y y] Z from [a.1 a.2 a.3];"
                         "} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.AlternateSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "A B")
        self.assertEqual(glyphstr([sub.glyph]), "a")
        self.assertEqual(glyphstr(sub.suffix), "[Y y] Z")
        self.assertEqual(glyphstr([sub.replacement]), "[a.1 a.2 a.3]")

    def test_substitute_from_cid(self):  # GSUB LookupType 3
        doc = self.parse(r"feature test {"
                         r"  substitute \7 from [\111 \222];"
                         r"} test;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.AlternateSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr([sub.glyph]), "cid00007")
        self.assertEqual(glyphstr(sub.suffix), "")
        self.assertEqual(glyphstr([sub.replacement]), "[cid00111 cid00222]")

    def test_substitute_from_glyphclass(self):  # GSUB LookupType 3
        doc = self.parse("feature test {"
                         "  @Ampersands = [ampersand.1 ampersand.2];"
                         "  substitute ampersand from @Ampersands;"
                         "} test;")
        [glyphclass, sub] = doc.statements[0].statements
        self.assertIsInstance(sub, ast.AlternateSubstStatement)
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr([sub.glyph]), "ampersand")
        self.assertEqual(glyphstr(sub.suffix), "")
        self.assertEqual(glyphstr([sub.replacement]),
                         "[ampersand.1 ampersand.2]")

    def test_substitute_ligature(self):  # GSUB LookupType 4
        doc = self.parse("feature liga {substitute f f i by f_f_i;} liga;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.LigatureSubstStatement)
        self.assertEqual(glyphstr(sub.glyphs), "f f i")
        self.assertEqual(sub.replacement, "f_f_i")
        self.assertEqual(glyphstr(sub.prefix), "")
        self.assertEqual(glyphstr(sub.suffix), "")

    def test_substitute_ligature_chained(self):  # chain to GSUB LookupType 4
        doc = self.parse("feature F {substitute A B f' i' Z by f_i;} F;")
        sub = doc.statements[0].statements[0]
        self.assertIsInstance(sub, ast.LigatureSubstStatement)
        self.assertEqual(glyphstr(sub.glyphs), "f i")
        self.assertEqual(sub.replacement, "f_i")
        self.assertEqual(glyphstr(sub.prefix), "A B")
        self.assertEqual(glyphstr(sub.suffix), "Z")

    def test_substitute_lookups(self):  # GSUB LookupType 6
        doc = Parser(self.getpath("spec5fi1.fea")).parse()
        [langsys, ligs, sub, feature] = doc.statements
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

    def test_table_badEnd(self):
        self.assertRaisesRegex(
            FeatureLibError, 'Expected "GDEF"', self.parse,
            "table GDEF {LigatureCaretByPos f_i 400;} ABCD;")

    def test_table_unsupported(self):
        self.assertRaisesRegex(
            FeatureLibError, '"table Foo" is not supported', self.parse,
            "table Foo {LigatureCaretByPos f_i 400;} Foo;")

    def test_valuerecord_format_a_horizontal(self):
        doc = self.parse("feature liga {valueRecordDef 123 foo;} liga;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 0)
        self.assertEqual(value.yPlacement, 0)
        self.assertEqual(value.xAdvance, 123)
        self.assertEqual(value.yAdvance, 0)
        self.assertIsNone(value.xPlaDevice)
        self.assertIsNone(value.yPlaDevice)
        self.assertIsNone(value.xAdvDevice)
        self.assertIsNone(value.yAdvDevice)

    def test_valuerecord_format_a_vertical(self):
        doc = self.parse("feature vkrn {valueRecordDef 123 foo;} vkrn;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 0)
        self.assertEqual(value.yPlacement, 0)
        self.assertEqual(value.xAdvance, 0)
        self.assertEqual(value.yAdvance, 123)
        self.assertIsNone(value.xPlaDevice)
        self.assertIsNone(value.yPlaDevice)
        self.assertIsNone(value.xAdvDevice)
        self.assertIsNone(value.yAdvDevice)

    def test_valuerecord_format_a_vertical_contexts_(self):
        for tag in "vkrn vpal vhal valt".split():
            doc = self.parse(
                "feature %s {valueRecordDef 77 foo;} %s;" % (tag, tag))
            value = doc.statements[0].statements[0].value
            if value.yAdvance != 77:
                self.fail(msg="feature %s should be a vertical context "
                          "for ValueRecord format A" % tag)

    def test_valuerecord_format_b(self):
        doc = self.parse("feature liga {valueRecordDef <1 2 3 4> foo;} liga;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 1)
        self.assertEqual(value.yPlacement, 2)
        self.assertEqual(value.xAdvance, 3)
        self.assertEqual(value.yAdvance, 4)
        self.assertIsNone(value.xPlaDevice)
        self.assertIsNone(value.yPlaDevice)
        self.assertIsNone(value.xAdvDevice)
        self.assertIsNone(value.yAdvDevice)

    def test_valuerecord_format_c(self):
        doc = self.parse(
            "feature liga {"
            "    valueRecordDef <"
            "        1 2 3 4"
            "        <device 8 88>"
            "        <device 11 111, 12 112>"
            "        <device NULL>"
            "        <device 33 -113, 44 -114, 55 115>"
            "    > foo;"
            "} liga;")
        value = doc.statements[0].statements[0].value
        self.assertEqual(value.xPlacement, 1)
        self.assertEqual(value.yPlacement, 2)
        self.assertEqual(value.xAdvance, 3)
        self.assertEqual(value.yAdvance, 4)
        self.assertEqual(value.xPlaDevice, ((8, 88),))
        self.assertEqual(value.yPlaDevice, ((11, 111), (12, 112)))
        self.assertIsNone(value.xAdvDevice)
        self.assertEqual(value.yAdvDevice, ((33, -113), (44, -114), (55, 115)))

    def test_valuerecord_format_d(self):
        doc = self.parse("feature test {valueRecordDef <NULL> foo;} test;")
        value = doc.statements[0].statements[0].value
        self.assertIsNone(value)

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

    def test_valuerecord_device_value_out_of_range(self):
        self.assertRaisesRegex(
            FeatureLibError, r"Device value out of valid range \(-128..127\)",
            self.parse,
            "valueRecordDef <1 2 3 4 <device NULL> <device NULL> "
            "<device NULL> <device 11 128>> foo;")

    def test_languagesystem(self):
        [langsys] = self.parse("languagesystem latn DEU;").statements
        self.assertEqual(langsys.script, "latn")
        self.assertEqual(langsys.language, "DEU ")
        self.assertRaisesRegex(
            FeatureLibError,
            'For script "DFLT", the language must be "dflt"',
            self.parse, "languagesystem DFLT DEU;")
        self.assertRaisesRegex(
            FeatureLibError,
            '"dflt" is not a valid script tag; use "DFLT" instead',
            self.parse, "languagesystem dflt dflt;")
        self.assertRaisesRegex(
            FeatureLibError,
            '"DFLT" is not a valid language tag; use "dflt" instead',
            self.parse, "languagesystem latn DFLT;")
        self.assertRaisesRegex(
            FeatureLibError, "Expected ';'",
            self.parse, "languagesystem latn DEU")
        self.assertRaisesRegex(
            FeatureLibError, "longer than 4 characters",
            self.parse, "languagesystem foobar DEU;")
        self.assertRaisesRegex(
            FeatureLibError, "longer than 4 characters",
            self.parse, "languagesystem latn FOOBAR;")

    def test_empty_statement_ignored(self):
        doc = self.parse("feature test {;} test;")
        self.assertFalse(doc.statements[0].statements)

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
        with open(path, "w", encoding="utf-8") as outfile:
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
