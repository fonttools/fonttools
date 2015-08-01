from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.features import Features
from fontTools.feaLib.lexer import Lexer, IncludingLexer


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
        self.doc_ = Features()

        self.next_token_type_, self.next_token_ = (None, None)
        self.next_token_location_ = None
        self.lexer_ = IncludingLexer(path)
        self.advance_lexer_()

    def parse(self):
        while self.next_token_type_ is not None:
            keyword = self.expect_keyword_({"feature", "languagesystem"})
            if keyword == "languagesystem":
                self.parse_languagesystem_()
            elif keyword == "feature":
                break  # TODO: Implement
        return self.doc_

    def parse_languagesystem_(self):
        script, language = self.expect_tag_(), self.expect_tag_()
        self.expect_symbol_(";")
        langsys = self.doc_.language_system.setdefault(script, set())
        langsys.add(language)

    def expect_keyword_(self, keywords):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME and self.cur_token_ in keywords:
            return self.cur_token_
        s = ", ".join(sorted(list(keywords)))
        raise ParserError("Expected one of %s" % s,
                          self.cur_token_location_)

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

    def advance_lexer_(self):
        self.cur_token_type_, self.cur_token_, self.cur_token_location_ = (
            self.next_token_type_, self.next_token_, self.next_token_location_)
        try:
            (self.next_token_type_, self.next_token_,
             self.next_token_location_) = self.lexer_.next()
        except StopIteration:
            self.next_token_type_, self.next_token_ = (None, None)
