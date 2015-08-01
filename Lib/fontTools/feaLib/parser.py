from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.lexer import Lexer, IncludingLexer
import fontTools.feaLib.ast as ast
import os
import re


class ParserError(Exception):
    def __init__(self, message, location):
        Exception.__init__(self, message)
        self.location = location

    def __str__(self):
        message = Exception.__str__(self)
        if self.location:
            path, line, column = self.location
            return "%s:%d:%d: %s" % (path, line, column, message)
        else:
            return message


class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.FeatureFile()
        self.glyphclasses_ = [{}]

        self.next_token_type_, self.next_token_ = (None, None)
        self.next_token_location_ = None
        self.lexer_ = IncludingLexer(path)
        self.advance_lexer_()

    def parse(self):
        while self.next_token_type_ is not None:
            self.advance_lexer_()
            if self.cur_token_type_ is Lexer.GLYPHCLASS:
                glyphclass = self.parse_glyphclass_definition_()
                self.doc_.statements.append(glyphclass)
            elif self.is_cur_keyword_("languagesystem"):
                self.parse_languagesystem_()
            elif self.is_cur_keyword_("feature"):
                self.parse_feature_block_()
            else:
                raise ParserError("Expected languagesystem, feature, or "
                                  "glyph class definition",
                                  self.cur_token_location_)
        return self.doc_

    def resolve_glyphclass_(self, name):
        for symtab in reversed(self.glyphclasses_):
            gc = symtab.get(name)
            if gc:
                return gc
        return None

    def parse_glyphclass_definition_(self):
        location, name = self.cur_token_location_, self.cur_token_
        self.expect_symbol_("=")
        glyphs = self.parse_glyphclass_reference_()
        self.expect_symbol_(";")
        if self.resolve_glyphclass_(name) is not None:
            raise ParserError("Glyph class @%s already defined" % name,
                              location)
        glyphclass = ast.GlyphClassDefinition(location, name, glyphs)
        self.glyphclasses_[-1][name] = glyphclass
        return glyphclass

    def parse_glyphclass_reference_(self):
        result = set()
        if self.next_token_type_ is Lexer.GLYPHCLASS:
            self.advance_lexer_()
            gc = self.resolve_glyphclass_(self.cur_token_)
            if gc is None:
                raise ParserError("Unknown glyph class @%s" % self.cur_token_,
                                  self.cur_token_location_)
            result.update(gc.glyphs)
            return result

        self.expect_symbol_("[")
        while self.next_token_ != "]":
            self.advance_lexer_()
            if self.cur_token_type_ is Lexer.NAME:
                if self.next_token_ == "-":
                    range_location_ = self.cur_token_location_
                    range_start = self.cur_token_
                    self.expect_symbol_("-")
                    range_end = self.expect_name_()
                    result.update(self.make_glyph_range_(range_location_,
                                                         range_start,
                                                         range_end))
                else:
                    result.add(self.cur_token_)
            elif self.cur_token_type_ is Lexer.GLYPHCLASS:
                gc = self.resolve_glyphclass_(self.cur_token_)
                if gc is None:
                    raise ParserError(
                        "Unknown glyph class @%s" % self.cur_token_,
                        self.cur_token_location_)
                result.update(gc.glyphs)
            else:
                raise ParserError("Expected glyph name, range, or reference",
                                  self.cur_token_location_)
        self.expect_symbol_("]")
        return result

    def parse_languagesystem_(self):
        assert self.cur_token_ == "languagesystem"
        location = self.cur_token_location_
        script, language = self.expect_tag_(), self.expect_tag_()
        self.expect_symbol_(";")
        langsys = ast.LanguageSystemStatement(location, script, language)
        self.doc_.statements.append(langsys)

    def parse_feature_block_(self):
        assert self.cur_token_ == "feature"
        location = self.cur_token_location_
        tag = self.expect_tag_()
        self.expect_symbol_("{")
        self.glyphclasses_.append({})
        block = ast.FeatureBlock(location, tag)
        self.doc_.statements.append(block)

        while self.next_token_ != "}":
            self.advance_lexer_()
            if self.cur_token_type_ is Lexer.GLYPHCLASS:
                block.statements.append(self.parse_glyphclass_definition_())
            else:
                raise ParserError("Expected glyph class definition",
                                  self.cur_token_location_)

        self.expect_symbol_("}")
        self.glyphclasses_.pop()
        endtag = self.expect_tag_()
        if tag != endtag:
            raise ParserError("Expected \"%s\"" % tag.strip(),
                              self.cur_token_location_)
        self.expect_symbol_(";")

    def is_cur_keyword_(self, k):
        return (self.cur_token_type_ is Lexer.NAME) and (self.cur_token_ == k)

    def expect_tag_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is not Lexer.NAME:
            raise ParserError("Expected a tag", self.cur_token_location_)
        if len(self.cur_token_) > 4:
            raise ParserError("Tags can not be longer than 4 characters",
                              self.cur_token_location_)
        return (self.cur_token_ + "    ")[:4]

    def expect_symbol_(self, symbol):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.SYMBOL and self.cur_token_ == symbol:
            return symbol
        raise ParserError("Expected '%s'" % symbol, self.cur_token_location_)

    def expect_name_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME:
            return self.cur_token_
        raise ParserError("Expected a name", self.cur_token_location_)

    def advance_lexer_(self):
        self.cur_token_type_, self.cur_token_, self.cur_token_location_ = (
            self.next_token_type_, self.next_token_, self.next_token_location_)
        try:
            (self.next_token_type_, self.next_token_,
             self.next_token_location_) = self.lexer_.next()
        except StopIteration:
            self.next_token_type_, self.next_token_ = (None, None)

    def make_glyph_range_(self, location, start, limit):
        """("a.sc", "d.sc") --> {"a.sc", "b.sc", "c.sc", "d.sc"}"""
        result = set()
        if len(start) != len(limit):
            raise ParserError(
                "Bad range: \"%s\" and \"%s\" should have the same length" %
                (start, limit), location)
        rev = lambda s: ''.join(reversed(list(s)))  # string reversal
        prefix = os.path.commonprefix([start, limit])
        suffix = rev(os.path.commonprefix([rev(start), rev(limit)]))
        if len(suffix) > 0:
            start_range = start[len(prefix):-len(suffix)]
            limit_range = limit[len(prefix):-len(suffix)]
        else:
            start_range = start[len(prefix):]
            limit_range = limit[len(prefix):]

        if start_range >= limit_range:
            raise ParserError("Start of range must be smaller than its end",
                              location)

        uppercase = re.compile(r'^[A-Z]$')
        if uppercase.match(start_range) and uppercase.match(limit_range):
            for c in range(ord(start_range), ord(limit_range) + 1):
                result.add("%s%c%s" % (prefix, c, suffix))
            return result

        lowercase = re.compile(r'^[a-z]$')
        if lowercase.match(start_range) and lowercase.match(limit_range):
            for c in range(ord(start_range), ord(limit_range) + 1):
                result.add("%s%c%s" % (prefix, c, suffix))
            return result

        digits = re.compile(r'^[0-9]{1,3}$')
        if digits.match(start_range) and digits.match(limit_range):
            for i in range(int(start_range, 10), int(limit_range, 10) + 1):
                number = ("000" + str(i))[-len(start_range):]
                result.add("%s%s%s" % (prefix, number, suffix))
            return result

        raise ParserError("Bad range: \"%s-%s\"" % (start, limit), location)
