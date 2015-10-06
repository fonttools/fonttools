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
            elif self.is_cur_keyword_("DEF_LOOKUP"):
                statements.append(self.parse_def_lookup_())
            elif self.is_cur_keyword_("END"):
                if self.next_token_type_ is not None:
                    raise VoltLibError("Expected the end of the file",
                                       self.cur_token_location_)
                return self.doc_
            else:
                raise VoltLibError("Expected DEF_GLYPH, DEF_GROUP, "
                                   "DEF_SCRIPT, DEF_LOOKUP",
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

    def parse_def_lookup_(self):
        assert self.is_cur_keyword_("DEF_LOOKUP")
        location = self.cur_token_location_
        name = self.expect_string_()
        base = self.expect_name_()
        assert base in ("PROCESS_BASE", "SKIP_BASE")
        marks = self.expect_name_()
        assert marks in ("PROCESS_MARKS", "SKIP_MARKS")
        if marks == "PROCESS_MARKS":
            pass
        all_flag = False
        if self.next_token_ == "ALL":
            self.expect_keyword_("ALL")
            all_flag = True
        direction = None
        if self.next_token_ == "DIRECTION":
            self.expect_keyword_("DIRECTION")
            direction = self.expect_name_()
            assert direction in ("LTR", "RTL")
        comments = None
        if self.next_token_ == "COMMENTS":
            self.expect_keyword_("COMMENTS")
            comments = self.expect_string_()
        context = None
        if self.next_token_ in ("EXCEPT_CONTEXT", "IN_CONTEXT"):
            context = self.parse_context_()
        as_pos_or_sub = self.expect_name_()
        sub = None
        pos = None
        if as_pos_or_sub == "AS_SUBSTITUTION":
            sub = self.parse_substitution_()
        elif as_pos_or_sub == "AS_POSITION":
            pos = self.parse_positioning_()
        def_lookup = ast.LookupDefinition(location, name, base, marks,
                                          all_flag, direction, comments,
                                          context, sub, pos)
        return def_lookup

    def parse_context_(self):
        except_or_in = self.expect_name_()
        assert except_or_in in ("EXCEPT_CONTEXT", "IN_CONTEXT")
        side = None
        coverage = None
        if self.next_token_ != "END_CONTEXT" :
            side = self.expect_name_()
            assert side in ("LEFT", "RIGHT")
            coverage = self.parse_coverage_()
        self.expect_keyword_("END_CONTEXT")
        return (except_or_in, side)

    def parse_substitution_(self):
        assert self.is_cur_keyword_("AS_SUBSTITUTION")
        location = self.cur_token_location_
        src = []
        dest = []
        while self.next_token_ == "SUB":
            self.expect_keyword_("SUB")
            src.extend(self.parse_coverage_())
            self.expect_keyword_("WITH")
            dest.extend(self.parse_coverage_())
            self.expect_keyword_("END_SUB")
        self.expect_keyword_("END_SUBSTITUTION")
        sub = ast.SubstitutionDefinition(location, src, dest)
        return sub

    def parse_position_(self):
        assert self.is_cur_keyword_("AS_POSITION")
        location = self.cur_token_location_
        raise VoltLibError("AS_POSITION not yet implemented.", location)

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
        location = self.cur_token_location_
        if self.next_token_ == "ENUM":
            self.advance_lexer_()
            return self.parse_enum_()
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
