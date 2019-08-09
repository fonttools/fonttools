from fontTools.voltLib.error import VoltLibError
from fontTools.voltLib.lexer import Lexer
import unittest


def lex(s):
    return [(typ, tok) for (typ, tok, _) in Lexer(s, "test.vtp")]


class LexerTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def test_empty(self):
        self.assertEqual(lex(""), [])
        self.assertEqual(lex("\t"), [])

    def test_string(self):
        self.assertEqual(lex('"foo" "bar"'),
                         [(Lexer.STRING, "foo"), (Lexer.STRING, "bar")])
        self.assertRaises(VoltLibError, lambda: lex('"foo\n bar"'))

    def test_name(self):
        self.assertEqual(lex('DEF_FOO bar.alt1'),
                         [(Lexer.NAME, "DEF_FOO"), (Lexer.NAME, "bar.alt1")])

    def test_number(self):
        self.assertEqual(lex("123 -456"),
                         [(Lexer.NUMBER, 123), (Lexer.NUMBER, -456)])

if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
