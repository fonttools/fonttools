from fontTools.misc.py23 import *
from fontTools.feaLib.error import FeatureLibError, IncludedFeaNotFound
from fontTools.feaLib.lexer import IncludingLexer, Lexer
import os
import shutil
import tempfile
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
        self.assertEqual(lex("with-dash"), [(Lexer.NAME, "with-dash")])

    def test_cid(self):
        self.assertEqual(lex("\\0 \\987"), [(Lexer.CID, 0), (Lexer.CID, 987)])

    def test_glyphclass(self):
        self.assertEqual(lex("@Vowel.sc"), [(Lexer.GLYPHCLASS, "Vowel.sc")])
        self.assertEqual(lex("@Vowel-sc"), [(Lexer.GLYPHCLASS, "Vowel-sc")])
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
            (Lexer.COMMENT, "# Comment"),
            (Lexer.FILENAME, "foo"),
            (Lexer.SYMBOL, ";")
        ])
        self.assertRaises(FeatureLibError, lex, "include blah")
        self.assertRaises(FeatureLibError, lex, "include (blah")

    def test_number(self):
        self.assertEqual(lex("123 -456"),
                         [(Lexer.NUMBER, 123), (Lexer.NUMBER, -456)])
        self.assertEqual(lex("0xCAFED00D"), [(Lexer.HEXADECIMAL, 0xCAFED00D)])
        self.assertEqual(lex("0xcafed00d"), [(Lexer.HEXADECIMAL, 0xCAFED00D)])
        self.assertEqual(lex("010"), [(Lexer.OCTAL, 0o10)])

    def test_float(self):
        self.assertEqual(lex("1.23 -4.5"),
                         [(Lexer.FLOAT, 1.23), (Lexer.FLOAT, -4.5)])

    def test_symbol(self):
        self.assertEqual(lex("a'"), [(Lexer.NAME, "a"), (Lexer.SYMBOL, "'")])
        self.assertEqual(lex("-A-B"),
                         [(Lexer.SYMBOL, "-"), (Lexer.NAME, "A-B")])
        self.assertEqual(
            lex("foo - -2"),
            [(Lexer.NAME, "foo"), (Lexer.SYMBOL, "-"), (Lexer.NUMBER, -2)])

    def test_comment(self):
        self.assertEqual(lex("# Comment\n#"),
                         [(Lexer.COMMENT, "# Comment"), (Lexer.COMMENT, "#")])

    def test_string(self):
        self.assertEqual(lex('"foo" "bar"'),
                         [(Lexer.STRING, "foo"), (Lexer.STRING, "bar")])
        self.assertEqual(lex('"foo \nbar\r baz \r\nqux\n\n "'),
                         [(Lexer.STRING, "foo bar baz qux ")])
        # The lexer should preserve escape sequences because they have
        # different interpretations depending on context. For better
        # or for worse, that is how the OpenType Feature File Syntax
        # has been specified; see section 9.e (name table) for examples.
        self.assertEqual(lex(r'"M\00fcller-Lanc\00e9"'),  # 'nameid 9'
                         [(Lexer.STRING, r"M\00fcller-Lanc\00e9")])
        self.assertEqual(lex(r'"M\9fller-Lanc\8e"'),  # 'nameid 9 1'
                         [(Lexer.STRING, r"M\9fller-Lanc\8e")])
        self.assertRaises(FeatureLibError, lex, '"foo\n bar')

    def test_bad_character(self):
        self.assertRaises(FeatureLibError, lambda: lex("123 \u0001"))

    def test_newline(self):
        def lines(s):
            return [loc.line for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(lines("FOO\n\nBAR\nBAZ"), [1, 3, 4])  # Unix
        self.assertEqual(lines("FOO\r\rBAR\rBAZ"), [1, 3, 4])  # Macintosh
        self.assertEqual(lines("FOO\r\n\r\n BAR\r\nBAZ"), [1, 3, 4])  # Windows
        self.assertEqual(lines("FOO\n\rBAR\r\nBAZ"), [1, 3, 4])  # mixed

    def test_location(self):
        def locs(s):
            return [str(loc) for (_, _, loc) in Lexer(s, "test.fea")]
        self.assertEqual(locs("a b # Comment\n12 @x"), [
            "test.fea:1:1", "test.fea:1:3", "test.fea:1:5", "test.fea:2:1",
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
        return os.path.join(path, "data", filename)

    def test_include(self):
        lexer = IncludingLexer(self.getpath("include/include4.fea"))
        result = ['%s %s:%d' % (token, os.path.split(loc.file)[1], loc.line)
                  for _, token, loc in lexer]
        self.assertEqual(result, [
            "I4a include4.fea:1",
            "I3a include3.fea:1",
            "I2a include2.fea:1",
            "I1a include1.fea:1",
            "I0 include0.fea:1",
            "I1b include1.fea:3",
            "; include2.fea:2",
            "I2b include2.fea:3",
            "; include3.fea:2",
            "I3b include3.fea:3",
            "; include4.fea:2",
            "I4b include4.fea:3"
        ])

    def test_include_limit(self):
        lexer = IncludingLexer(self.getpath("include/include6.fea"))
        self.assertRaises(FeatureLibError, lambda: list(lexer))

    def test_include_self(self):
        lexer = IncludingLexer(self.getpath("include/includeself.fea"))
        self.assertRaises(FeatureLibError, lambda: list(lexer))

    def test_include_missing_file(self):
        lexer = IncludingLexer(self.getpath("include/includemissingfile.fea"))
        self.assertRaisesRegex(IncludedFeaNotFound,
                               "includemissingfile.fea:1:8: The following feature file "
                               "should be included but cannot be found: "
                               "missingfile.fea",
                               lambda: list(lexer))

    def test_featurefilepath_None(self):
        lexer = IncludingLexer(UnicodeIO("# foobar"))
        self.assertIsNone(lexer.featurefilepath)
        files = set(loc.file for _, _, loc in lexer)
        self.assertIn("<features>", files)

    def test_include_absolute_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as included:
            included.write(tobytes("""
                feature kern {
                    pos A B -40;
                } kern;
                """, encoding="utf-8"))
        including = UnicodeIO("include(%s);" % included.name)
        try:
            lexer = IncludingLexer(including)
            files = set(loc.file for _, _, loc in lexer)
            self.assertIn(included.name, files)
        finally:
            os.remove(included.name)

    def test_include_relative_to_cwd(self):
        # save current working directory, to be restored later
        cwd = os.getcwd()
        tmpdir = tempfile.mkdtemp()
        try:
            # create new feature file in a temporary directory
            with open(os.path.join(tmpdir, "included.fea"), "w",
                      encoding="utf-8") as included:
                included.write("""
                    feature kern {
                        pos A B -40;
                    } kern;
                    """)
            # change current folder to the temporary dir
            os.chdir(tmpdir)
            # instantiate a new lexer that includes the above file
            # using a relative path; the IncludingLexer does not
            # itself have a path, because it was initialized from
            # an in-memory stream, so it will use the current working
            # directory to resolve relative include statements
            lexer = IncludingLexer(UnicodeIO("include(included.fea);"))
            files = set(os.path.realpath(loc.file) for _, _, loc in lexer)
            expected = os.path.realpath(included.name)
            self.assertIn(expected, files)
        finally:
            # remove temporary folder and restore previous working directory
            os.chdir(cwd)
            shutil.rmtree(tmpdir)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
