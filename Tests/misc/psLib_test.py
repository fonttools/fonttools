import time

from fontTools.misc.psLib import PSTokenizer, suckfont
import pytest


def tokenize(buf):
    tokenizer = PSTokenizer(buf)
    tokens = []
    while True:
        tokentype, token = tokenizer.getnexttoken()
        if not token:
            break
        tokens.append((tokentype, token))
    tokenizer.close()
    return tokens


class PSStringTokenTest:
    def test_plain_string(self):
        assert tokenize(b"(hello)") == [("do_string", "(hello)")]

    def test_nested_parens(self):
        assert tokenize(b"(a(b)c)") == [("do_string", "(a(b)c)")]

    @pytest.mark.parametrize(
        "buf",
        [
            b"(a\\(b)",  # escaped open paren
            b"(a\\)b)",  # escaped close paren
            b"(Copyright \\(c\\) 2000)",
        ],
    )
    def test_escaped_parens(self, buf):
        # An escaped "(" or ")" is part of the string, it does not open or
        # close it. The whole literal is returned as a single string token.
        assert tokenize(buf) == [("do_string", buf.decode("ascii"))]

    def test_unterminated_string_is_rejected_quickly(self):
        # A string that is never closed used to make the tokenizer regex
        # backtrack catastrophically; make sure it fails fast instead.
        buf = b"(" + b"[]" * 25 + b" never closed"
        start = time.time()
        with pytest.raises(Exception):
            tokenize(buf)
        assert time.time() - start < 2.0


class SuckfontTest:
    def test_escaped_paren_in_font(self):
        # An unbalanced escaped paren, e.g. "\(" with no matching literal ")",
        # is a valid PostScript string but used to make the tokenizer raise
        # "bad string"; suckfont should now consume it.
        data = b"%!FontType1\n/Foo (a\\(b) def\n"
        font = suckfont(data, "ascii")
        assert isinstance(font, dict)
