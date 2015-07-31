from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.lexer import Lexer, LexerError
import unittest


def lex(s):
    return [(typ, tok) for (typ, tok, _) in Lexer(s, "test.fea")]


class LexerTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(lex(""), [])
        self.assertEqual(lex(" \t "), [])

    def test_name(self):
        self.assertEqual(lex("a17"), [(Lexer.NAME, "a17")])
        self.assertEqual(lex(".notdef"), [(Lexer.NAME, ".notdef")])
        self.assertEqual(lex("two.oldstyle"), [(Lexer.NAME, "two.oldstyle")])
        self.assertEqual(lex("_"), [(Lexer.NAME, "_")])
        self.assertEqual(lex("\\table"), [(Lexer.NAME, "\\table")])

    def test_cid(self):
        self.assertEqual(lex("\\0 \\987"), [(Lexer.CID, 0), (Lexer.CID, 987)])

    def test_number(self):
        self.assertEqual(lex("123 -456"),
                         [(Lexer.NUMBER, 123), (Lexer.NUMBER, -456)])

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
        self.assertRaises(LexerError, lambda: lex('"foo\n bar"'))

    def test_bad_character(self):
        self.assertRaises(LexerError, lambda: lex("123 \u0001"))

    def test_newline(self):
        lines = lambda s: [loc[1] for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(lines("FOO\n\nBAR\nBAZ"), [1, 3, 4])  # Unix
        self.assertEqual(lines("FOO\r\rBAR\rBAZ"), [1, 3, 4])  # Macintosh
        self.assertEqual(lines("FOO\r\n\r\n BAR\r\nBAZ"), [1, 3, 4])  # Windows
        self.assertEqual(lines("FOO\n\rBAR\r\nBAZ"), [1, 3, 4])  # mixed

    def test_location(self):
        locs = lambda s: ["%s:%d:%d" % loc
                          for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(locs("a b # Comment\n12 @x"), [
            "test.fea:1:1", "test.fea:1:3", "test.fea:2:1",
            "test.fea:2:4", "test.fea:2:5"
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


if __name__ == "__main__":
    unittest.main()
