from __future__ import print_function, division, absolute_import
import fontTools.voltLib.ast as ast
import fontTools.feaLib.parser as parser
from fontTools.voltLib.lexer import Lexer
from fontTools.voltLib.error import VoltLibError
import codecs

class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.VoltFile()
        self.groups_ = SymbolTable()
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
            elif self.is_cur_keyword_("DEF_GROUP"):
                statements.append(self.parse_def_group_())
            elif self.is_cur_keyword_("DEF_SCRIPT"):
                statements.append(self.parse_def_script_())
            elif self.is_cur_keyword_("END"):
                if self.next_token_type_ is not None:
                    raise VoltLibError("Expected the end of the file",
                                       self.cur_token_location_)
                return self.doc_
            else:
                raise VoltLibError("Expected DEF_GLYPH, DEF_GROUP, DEF_SCRIPT",
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
            gunicode = self.parse_unicode_values_()
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

    def parse_def_group_(self):
        assert self.is_cur_keyword_("DEF_GROUP")
        location = self.cur_token_location_
        name = self.expect_string_()
        enum = None
        if self.next_token_ == "ENUM":
            self.expect_keyword_("ENUM")
            enum = self.parse_enum_()
        self.expect_keyword_("END_GROUP")
        if self.groups_.resolve(name) is not None:
            raise VoltLibError('Glyph group "%s" already defined' % name,
                               location)
        def_group = ast.GroupDefinition(location, name, enum)
        self.groups_.define(name, def_group)
        return def_group

    def parse_def_script_(self):
        assert self.is_cur_keyword_("DEF_SCRIPT")
        location = self.cur_token_location_
        self.expect_keyword_("NAME")
        name = self.expect_string_()
        self.expect_keyword_("TAG")
        tag = self.expect_string_()
        langs = []
        while self.next_token_ != "END_SCRIPT":
            self.advance_lexer_()
            lang = self.parse_langsys_()
            self.expect_keyword_("END_LANGSYS")
            langs.append(lang)
        self.expect_keyword_("END_SCRIPT")
        def_script = ast.ScriptDefinition(location, name, tag, langs)
        return def_script

    def parse_langsys_(self):
        assert self.is_cur_keyword_("DEF_LANGSYS")
        location = self.cur_token_location_
        self.expect_keyword_("NAME")
        name = self.expect_string_()
        self.expect_keyword_("TAG")
        tag = self.expect_string_()
        features = []
        while self.next_token_ != "END_LANGSYS":
            self.advance_lexer_()
            feature = self.parse_feature_()
            self.expect_keyword_("END_FEATURE")
            features.append(feature)
        def_langsys = ast.LangSysDefinition(location, name, tag, features)
        return def_langsys

    def parse_feature_(self):
        assert self.is_cur_keyword_("DEF_FEATURE")
        location = self.cur_token_location_
        self.expect_keyword_("NAME")
        name = self.expect_string_()
        self.expect_keyword_("TAG")
        tag = self.expect_string_()
        lookups = []
        while self.next_token_ != "END_FEATURE":
            # self.advance_lexer_()
            self.expect_keyword_("LOOKUP")
            lookup = self.expect_string_()
            lookups.append(lookup)
        feature = ast.FeatureDefinition(location, name, tag, lookups)
        return feature

    def parse_unicode_values_(self):
        location = self.cur_token_location_
        unicode_values = self.expect_string_().split(',')
        return [int(uni[2:], 16) for uni in unicode_values]

    def parse_enum_(self):
        assert self.is_cur_keyword_("ENUM")
        location = self.cur_token_location_
        enum = self.parse_coverage_()
        self.expect_keyword_("END_ENUM")
        return enum

    def parse_coverage_(self):
        coverage = []
        while self.next_token_ in ("GLYPH", "GROUP", "RANGE"):
            if self.next_token_ == "GLYPH":
                self.expect_keyword_("GLYPH")
                name = self.expect_string_()
                coverage.append(name)
            elif self.next_token_ == "GROUP":
                self.expect_keyword_("GROUP")
                name = self.expect_string_()
                group = self.groups_.resolve(name)
                if group is None:
                    raise VoltLibError('Glyph group "%s" is not defined' % name,
                                       location)
                coverage.extend(group.enum)
            elif self.next_token_ == "RANGE":
                self.expect_keyword_("RANGE")
                start, end = self.expect_string_(), self.expect_string_()
                coverage.append((start, end))
        return coverage

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

class SymbolTable(parser.SymbolTable):
    def __init__(self):
        parser.SymbolTable.__init__(self)
