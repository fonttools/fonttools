from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.lexer import IncludingLexer, Lexer
import os
import unittest


def lex(s):
    return [(typ, tok) for (typ, tok, _) in Lexer(s, "test.fea")]


class LexerTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_empty(self):
        self.assertEqual(lex(""), [])
        self.assertEqual(lex(" \t "), [])

    def test_name(self):
        self.assertEqual(lex("a17"), [(Lexer.NAME, "a17")])
        self.assertEqual(lex(".notdef"), [(Lexer.NAME, ".notdef")])
        self.assertEqual(lex("two.oldstyle"), [(Lexer.NAME, "two.oldstyle")])
        self.assertEqual(lex("_"), [(Lexer.NAME, "_")])
        self.assertEqual(lex("\\table"), [(Lexer.NAME, "\\table")])
        self.assertEqual(lex("a+*:^~!"), [(Lexer.NAME, "a+*:^~!")])

    def test_cid(self):
        self.assertEqual(lex("\\0 \\987"), [(Lexer.CID, 0), (Lexer.CID, 987)])

    def test_glyphclass(self):
        self.assertEqual(lex("@Vowel.sc"), [(Lexer.GLYPHCLASS, "Vowel.sc")])
        self.assertRaisesRegex(FeatureLibError,
                               "Expected glyph class", lex, "@(a)")
        self.assertRaisesRegex(FeatureLibError,
                               "Expected glyph class", lex, "@ A")
        self.assertRaisesRegex(FeatureLibError,
                               "not be longer than 63 characters",
                               lex, "@" + ("A" * 64))
        self.assertRaisesRegex(FeatureLibError,
                               "Glyph class names must consist of",
                               lex, "@Ab:c")

    def test_include(self):
        self.assertEqual(lex("include (~/foo/bar baz.fea);"), [
            (Lexer.NAME, "include"),
            (Lexer.FILENAME, "~/foo/bar baz.fea"),
            (Lexer.SYMBOL, ";")
        ])
        self.assertEqual(lex("include # Comment\n    (foo) \n;"), [
            (Lexer.NAME, "include"),
            (Lexer.FILENAME, "foo"),
            (Lexer.SYMBOL, ";")
        ])
        self.assertRaises(FeatureLibError, lex, "include blah")
        self.assertRaises(FeatureLibError, lex, "include (blah")

    def test_number(self):
        self.assertEqual(lex("123 -456"),
                         [(Lexer.NUMBER, 123), (Lexer.NUMBER, -456)])
        self.assertEqual(lex("0xCAFED00D"), [(Lexer.NUMBER, 0xCAFED00D)])
        self.assertEqual(lex("0xcafed00d"), [(Lexer.NUMBER, 0xCAFED00D)])

    def test_float(self):
        self.assertEqual(lex("1.23 -4.5"),
                         [(Lexer.FLOAT, 1.23), (Lexer.FLOAT, -4.5)])

    def test_symbol(self):
        self.assertEqual(lex("a'"), [(Lexer.NAME, "a"), (Lexer.SYMBOL, "'")])
        self.assertEqual(
            lex("foo - -2"),
            [(Lexer.NAME, "foo"), (Lexer.SYMBOL, "-"), (Lexer.NUMBER, -2)])

    def test_comment(self):
        self.assertEqual(lex("# Comment\n#"), [])

    def test_string(self):
        self.assertEqual(lex('"foo" "bar"'),
                         [(Lexer.STRING, "foo"), (Lexer.STRING, "bar")])
        self.assertRaises(FeatureLibError, lambda: lex('"foo\n bar"'))

    def test_bad_character(self):
        self.assertRaises(FeatureLibError, lambda: lex("123 \u0001"))

    def test_newline(self):
        def lines(s):
            return [loc[1] for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(lines("FOO\n\nBAR\nBAZ"), [1, 3, 4])  # Unix
        self.assertEqual(lines("FOO\r\rBAR\rBAZ"), [1, 3, 4])  # Macintosh
        self.assertEqual(lines("FOO\r\n\r\n BAR\r\nBAZ"), [1, 3, 4])  # Windows
        self.assertEqual(lines("FOO\n\rBAR\r\nBAZ"), [1, 3, 4])  # mixed

    def test_location(self):
        def locs(s):
            return ["%s:%d:%d" % loc for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(locs("a b # Comment\n12 @x"), [
            "test.fea:1:1", "test.fea:1:3", "test.fea:2:1",
            "test.fea:2:4"
        ])

    def test_scan_over_(self):
        lexer = Lexer("abbacabba12", "test.fea")
        self.assertEqual(lexer.pos_, 0)
        lexer.scan_over_("xyz")
        self.assertEqual(lexer.pos_, 0)
        lexer.scan_over_("abc")
        self.assertEqual(lexer.pos_, 9)
        lexer.scan_over_("abc")
        self.assertEqual(lexer.pos_, 9)
        lexer.scan_over_("0123456789")
        self.assertEqual(lexer.pos_, 11)

    def test_scan_until_(self):
        lexer = Lexer("foo'bar", "test.fea")
        self.assertEqual(lexer.pos_, 0)
        lexer.scan_until_("'")
        self.assertEqual(lexer.pos_, 3)
        lexer.scan_until_("'")
        self.assertEqual(lexer.pos_, 3)


class IncludingLexerTest(unittest.TestCase):
    @staticmethod
    def getpath(filename):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", filename)

    def test_include(self):
        lexer = IncludingLexer(self.getpath("include4.fea"))
        result = ['%s %s:%d' % (token, os.path.split(loc[0])[1], loc[1])
                  for _, token, loc in lexer]
        self.assertEqual(result, [
            "I4a include4.fea:1",
            "I3a include3.fea:1",
            "I2a include2.fea:1",
            "I1a include1.fea:1",
            "I0 include0.fea:1",
            "I1b include1.fea:3",
            "I2b include2.fea:3",
            "I3b include3.fea:3",
            "I4b include4.fea:3"
        ])

    def test_include_limit(self):
        lexer = IncludingLexer(self.getpath("include6.fea"))
        self.assertRaises(FeatureLibError, lambda: list(lexer))

    def test_include_self(self):
        lexer = IncludingLexer(self.getpath("includeself.fea"))
        self.assertRaises(FeatureLibError, lambda: list(lexer))

    def test_include_missing_file(self):
        lexer = IncludingLexer(self.getpath("includemissingfile.fea"))
        self.assertRaises(FeatureLibError, lambda: list(lexer))


if __name__ == "__main__":
    unittest.main()
