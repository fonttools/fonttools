from __future__ import (
    print_function, division, absolute_import, unicode_literals)
import fontTools.voltLib.ast as ast
import fontTools.feaLib.parser as parser
from fontTools.voltLib.lexer import Lexer
from fontTools.voltLib.error import VoltLibError
from io import open

PARSE_FUNCS = {
    "DEF_GLYPH":         "parse_def_glyph_",
    "DEF_GROUP":         "parse_def_group_",
    "DEF_SCRIPT":        "parse_def_script_",
    "DEF_LOOKUP":        "parse_def_lookup_",
    "DEF_ANCHOR":        "parse_def_anchor_",
    "GRID_PPEM":         "parse_ppem_",
    "PRESENTATION_PPEM": "parse_ppem_",
    "PPOSITIONING_PPEM": "parse_ppem_",
    "COMPILER_USEEXTENSIONLOOKUPS": "parse_compiler_flag_",
    "COMPILER_USEPAIRPOSFORMAT2":   "parse_compiler_flag_",
    "CMAP_FORMAT":       "parse_cmap_format",
}


class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.VoltFile()
        self.groups_ = SymbolTable()
        self.anchors_ = SymbolTable()
        self.next_token_type_, self.next_token_ = (None, None)
        self.next_token_location_ = None
        with open(path, "r") as f:
            self.lexer_ = Lexer(f.read(), path)
        self.advance_lexer_()

    def parse(self):
        statements = self.doc_.statements
        while self.next_token_type_ is not None:
            self.advance_lexer_()
            if self.cur_token_ in PARSE_FUNCS.keys():
                func = getattr(self, PARSE_FUNCS[self.cur_token_])
                statements.append(func())
            elif self.is_cur_keyword_("END"):
                if self.next_token_type_ is not None:
                    raise VoltLibError("Expected the end of the file",
                                       self.cur_token_location_)
                return self.doc_
            else:
                raise VoltLibError(
                    "Expected " + ", ".join(sorted(PARSE_FUNCS.keys())),
                    self.cur_token_location_)
        self.groups_.expand()
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
        gtype = None
        if self.next_token_ == "TYPE":
            self.expect_keyword_("TYPE")
            gtype = self.expect_name_()
            assert gtype in ("BASE", "LIGATURE", "MARK")
        components = None
        if self.next_token_ == "COMPONENTS":
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
        name = None
        if self.next_token_ == "NAME":
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
        name = None
        if self.next_token_ == "NAME":
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
            if self.next_token_type_ == Lexer.STRING:
                process_marks = self.expect_string_()
            else:
                process_marks = self.expect_name_()
        else:
            process_marks = None
        all_flag = False
        # ALL or id
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
        context = []
        while self.next_token_ in ("EXCEPT_CONTEXT", "IN_CONTEXT"):
            context = self.parse_context_()
        as_pos_or_sub = self.expect_name_()
        sub = None
        pos = None
        if as_pos_or_sub == "AS_SUBSTITUTION":
            sub = self.parse_substitution_()
        elif as_pos_or_sub == "AS_POSITION":
            pos = self.parse_position_()
        def_lookup = ast.LookupDefinition(
            location, name, base, marks, process_marks, all_flag, direction,
            comments, context, sub, pos)
        return def_lookup

    def parse_context_(self):
        location = self.cur_token_location_
        contexts = []
        while self.next_token_ in ("EXCEPT_CONTEXT", "IN_CONTEXT"):
            side = None
            coverage = None
            ex_or_in = self.expect_name_()
            # side_contexts = [] # XXX
            if self.next_token_ != "END_CONTEXT":
                left = []
                right = []
                while self.next_token_ in ("LEFT", "RIGHT"):
                    side = self.expect_name_()
                    coverage = self.parse_coverage_()
                    if side == "LEFT":
                        left.append(coverage)
                    else:
                        right.append(coverage)
                self.expect_keyword_("END_CONTEXT")
                context = ast.ContextDefinition(location, ex_or_in, left,
                                                right)
                contexts.append(context)
            else:
                self.expect_keyword_("END_CONTEXT")
        return contexts

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
        pos_type = self.expect_name_()
        assert pos_type in ("ATTACH", "ATTACH_CURSIVE", "ADJUST_PAIR",
                            "ADJUST_SINGLE")
        if pos_type == "ATTACH":
            coverage = self.parse_coverage_()
            coverage_to = []
            self.expect_keyword_("TO")
            while self.next_token_ != "END_ATTACH":
                cov = self.parse_coverage_()
                self.expect_keyword_("AT")
                self.expect_keyword_("ANCHOR")
                anchor_name = self.expect_string_()
                coverage_to.append((cov, anchor_name))
            self.expect_keyword_("END_ATTACH")
            position = ast.PositionAttachDefinition(location, coverage,
                                                    coverage_to)
        elif pos_type == "ATTACH_CURSIVE":
            coverages_exit = []
            coverages_enter = []
            while self.next_token_ != "ENTER":
                self.expect_keyword_("EXIT")
                coverages_exit.append(self.parse_coverage_())
            while self.next_token_ != "END_ATTACH":
                self.expect_keyword_("ENTER")
                coverages_enter.append(self.parse_coverage_())
            self.expect_keyword_("END_ATTACH")
            position = ast.PositionAttachCursiveDefinition(
                location, coverages_exit, coverages_enter)
        elif pos_type == "ADJUST_PAIR":
            coverages_1 = []
            coverages_2 = []
            adjust = {}
            while self.next_token_ == "FIRST":
                self.advance_lexer_()
                coverage_1 = self.parse_coverage_()
                coverages_1.append(coverage_1)
            while self.next_token_ == "SECOND":
                self.advance_lexer_()
                coverage_2 = self.parse_coverage_()
                coverages_2.append(coverage_2)
            while self.next_token_ != "END_ADJUST":
                id_1 = self.expect_number_()
                id_2 = self.expect_number_()
                self.expect_keyword_("BY")
                pos_1 = self.parse_pos_()
                pos_2 = self.parse_pos_()
                adjust[(id_1, id_2)] = (pos_1, pos_2)
            self.expect_keyword_("END_ADJUST")
            position = ast.PositionAdjustPairDefinition(location, coverages_1,
                                                        coverages_2, adjust)
        elif pos_type == "ADJUST_SINGLE":
            coverages = self.parse_coverage_()
            self.expect_keyword_("BY")
            pos = self.parse_pos_()
            position = ast.PositionAdjustSingleDefinition(location, coverages,
                                                          pos)
            self.expect_keyword_("END_ADJUST")
        self.expect_keyword_("END_POSITION")
        return position

    def parse_def_anchor_(self):
        assert self.is_cur_keyword_("DEF_ANCHOR")
        location = self.cur_token_location_
        name = self.expect_string_()
        self.expect_keyword_("ON")
        gid = self.expect_number_()
        self.expect_keyword_("GLYPH")
        glyph_name = self.expect_name_()
        self.expect_keyword_("COMPONENT")
        component = self.expect_number_()
        if self.next_token_ == "LOCKED":
            locked = True
            self.advance_lexer_()
        else:
            locked = False
        self.expect_keyword_("AT")
        pos = self.parse_pos_()
        self.expect_keyword_("END_ANCHOR")
        anchor = ast.AnchorDefinition(location, name, gid, glyph_name,
                                      component, locked, pos)
        return anchor

    def parse_pos_(self):
        self.advance_lexer_()
        location = self.cur_token_location_
        assert self.is_cur_keyword_("POS"), location
        adv = None
        dx = None
        dy = None
        adv_adjust_by = {}
        dx_adjust_by = {}
        dy_adjust_by = {}
        if self.next_token_ == "ADV":
            self.advance_lexer_()
            adv = self.expect_number_()
            while self.next_token_ == "ADJUST_BY":
                adjustment = self.expect_number_()
                size = self.expect_number_()
                adv_adjust_by[size] = adjustment
        if self.next_token_ == "DX":
            self.advance_lexer_()
            dx = self.expect_number_()
            while self.next_token_ == "ADJUST_BY":
                adjustment = self.expect_number_()
                size = self.expect_number_()
                dx_adjust_by[size] = adjustment
        if self.next_token_ == "DY":
            self.advance_lexer_()
            dy = self.expect_number_()
            while self.next_token_ == "ADJUST_BY":
                adjustment = self.expect_number_()
                size = self.expect_number_()
                dy_adjust_by[size] = adjustment
        self.expect_keyword_("END_POS")
        return (adv, dx, dy, adv_adjust_by, dx_adjust_by, dy_adjust_by)

    def parse_unicode_values_(self):
        location = self.cur_token_location_
        # TODO use location
        try:
            unicode_values = self.expect_string_().split(",")
            unicode_values = [
                int(uni[2:], 16)
                for uni in unicode_values if uni != ""]
        except ValueError as err:
            raise VoltLibError(str(err), location)
        return unicode_values if unicode_values != [] else None

    def parse_enum_(self):
        assert self.is_cur_keyword_("ENUM")
        # location = self.cur_token_location_
        # TODO use location
        enum = self.parse_coverage_()
        self.expect_keyword_("END_ENUM")
        return enum

    def parse_coverage_(self):
        coverage = []
        # XXX use location
        location = self.cur_token_location_
        while self.next_token_ in ("GLYPH", "GROUP", "RANGE", "ENUM"):
            if self.next_token_ == "ENUM":
                self.advance_lexer_()
                enum = self.parse_enum_()
                # print(enum)
                coverage.append(enum)
            elif self.next_token_ == "GLYPH":
                self.expect_keyword_("GLYPH")
                name = self.expect_string_()
                coverage.append(name)
            elif self.next_token_ == "GROUP":
                self.expect_keyword_("GROUP")
                name = self.expect_string_()
                group = self.groups_.resolve(name)
                if group is None:
                    raise VoltLibError(
                        'Glyph group "%s" is not defined' % name,
                        location)
                coverage.extend(group.enum)
            elif self.next_token_ == "RANGE":
                self.expect_keyword_("RANGE")
                start, end = self.expect_string_(), self.expect_string_()
                coverage.append((start, end))
        return coverage

    def parse_ppem_(self):
        location = self.cur_token_location_
        ppem_name = self.cur_token_
        value = self.expect_number_()
        setting = ast.SettingDefinition(location, ppem_name, value)
        return setting

    def parse_compiler_flag_(self):
        location = self.cur_token_location_
        flag_name = self.cur_token_
        value = True
        setting = ast.SettingDefinition(location, flag_name, value)
        return setting

    def parse_cmap_format(self):
        location = self.cur_token_location_
        name = self.cur_token_
        value = (self.expect_number_(), self.expect_number_(),
                 self.expect_number_())
        setting = ast.SettingDefinition(location, name, value)
        return setting

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

    # TODO also expand ranges
    def expand(self):
        for scope in self.scopes_:
            for v in scope.values():
                removed = 0
                for i, element in enumerate(list(v.enum)):
                    if isinstance(element, tuple) and len(element) == 1:
                        name = element[0]
                        resolved_group = self.resolve(name)
                        if resolved_group is None:
                            raise VoltLibError(
                                'Group "%s" is used but undefined.' % (name),
                                None)
                        v.enum.remove(element)
                        i -= removed
                        v.enum = v.enum[:i] + resolved_group.enum + v.enum[i:]
                        removed += len(resolved_group.enum)
