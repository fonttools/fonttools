from __future__ import print_function, division, absolute_import
import fontTools.voltLib.ast as ast
from fontTools.voltLib.lexer import Lexer
from fontTools.voltLib.error import VoltLibError
import codecs

class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.VoltFile()
        self.next_token_type_, self.next_token_ = (None, None)
        self.next_token_location_ = None
        try:
            with codecs.open(path, "rb", "utf-8") as f:
                self.lexer_ = Lexer(f.read(), path)
        except IOError as err:
            raise VoltLibError(str(err), location)
        self.advance_lexer_()

    def parse(self):
        statements = self.doc_.statements
        while self.next_token_type_ is not None:
            self.advance_lexer_()
            if self.is_cur_keyword_("DEF_GLYPH"):
                statements.append(self.parse_def_glyph_())
            elif self.is_cur_keyword_("END"):
                if self.next_token_type_ is not None:
                    raise VoltLibError("Expected the end of the file",
                                       self.cur_token_location_)
                return self.doc_
            else:
                raise VoltLibError("Expected DEF_GLYPH",
                                   self.cur_token_location_)
        return self.doc_

    def parse_def_glyph_(self):
        assert self.is_cur_keyword_("DEF_GLYPH")
        location = self.cur_token_location_
        name = self.expect_string_()
        self.expect_keyword_("ID")
        gid = self.expect_number_()
        if gid < 0:
            raise VoltLibError("Invalid glyph ID", self.cur_token_location_)
        gunicode = None
        if self.next_token_ == "UNICODE":
            self.expect_keyword_("UNICODE")
            gunicode = [self.expect_number_()]
            if gunicode[0] < 0:
                raise VoltLibError("Invalid glyph UNICODE",
                                   self.cur_token_location_)
        elif self.next_token_ == "UNICODEVALUES":
            self.expect_keyword_("UNICODEVALUES")
            gunicode = self.parse_unicode_values()
        # Apparently TYPE is optional
        gtype = None
        if self.next_token_ == "TYPE":
            self.expect_keyword_("TYPE")
            gtype = self.expect_name_()
            assert gtype in ("BASE", "LIGATURE", "MARK")
        components = None
        if gtype == "LIGATURE":
            self.expect_keyword_("COMPONENTS")
            components = self.expect_number_()
        self.expect_keyword_("END_GLYPH")
        def_glyph = ast.GlyphDefinition(location, name, gid,
                                        gunicode, gtype, components)
        return def_glyph

    def parse_unicode_values(self):
        location = self.cur_token_location_
        unicode_values = self.expect_string_().split(',')
        return [int(uni[2:], 16) for uni in unicode_values]

    def is_cur_keyword_(self, k):
        return (self.cur_token_type_ is Lexer.NAME) and (self.cur_token_ == k)

    def expect_string_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is not Lexer.STRING:
            raise VoltLibError("Expected a string", self.cur_token_location_)
        return self.cur_token_

    def expect_keyword_(self, keyword):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME and self.cur_token_ == keyword:
            return self.cur_token_
        raise VoltLibError("Expected \"%s\"" % keyword,
                              self.cur_token_location_)

    def expect_name_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME:
            return self.cur_token_
        raise VoltLibError("Expected a name", self.cur_token_location_)

    def expect_number_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is not Lexer.NUMBER:
            raise VoltLibError("Expected a number", self.cur_token_location_)
        return self.cur_token_

    def advance_lexer_(self):
        self.cur_token_type_, self.cur_token_, self.cur_token_location_ = (
            self.next_token_type_, self.next_token_, self.next_token_location_)
        try:
            (self.next_token_type_, self.next_token_,
             self.next_token_location_) = self.lexer_.next()
        except StopIteration:
            self.next_token_type_, self.next_token_ = (None, None)
