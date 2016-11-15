from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from collections import OrderedDict
import fontTools.voltLib.ast as ast
from fontTools.voltLib.lexer import Lexer
from fontTools.voltLib.error import VoltLibError
from io import open

PARSE_FUNCS = {
    "DEF_GLYPH": "parse_def_glyph_",
    "DEF_GROUP": "parse_def_group_",
    "DEF_SCRIPT": "parse_def_script_",
    "DEF_LOOKUP": "parse_def_lookup_",
    "DEF_ANCHOR": "parse_def_anchor_",
    "GRID_PPEM": "parse_ppem_",
    "PRESENTATION_PPEM": "parse_ppem_",
    "PPOSITIONING_PPEM": "parse_ppem_",
    "COMPILER_USEEXTENSIONLOOKUPS": "parse_compiler_flag_",
    "COMPILER_USEPAIRPOSFORMAT2": "parse_compiler_flag_",
    "CMAP_FORMAT": "parse_cmap_format",
}


class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.VoltFile()
        self.glyphs_ = OrderedSymbolTable()
        self.groups_ = SymbolTable()
        self.anchors_ = {}  # dictionary of SymbolTable() keyed by glyph
        self.scripts_ = SymbolTable()
        self.langs_ = SymbolTable()
        self.lookups_ = SymbolTable()
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
        if self.glyphs_.resolve(name) is not None:
            raise VoltLibError(
                'Glyph "%s" (gid %i) already defined' % (name, gid),
                location
            )
        def_glyph = ast.GlyphDefinition(location, name, gid,
                                        gunicode, gtype, components)
        self.glyphs_.define(name, def_glyph)
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
            raise VoltLibError(
                'Glyph group "%s" already defined, '
                'group names are case insensitive' % name,
                location
            )
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
        if self.scripts_.resolve(tag) is not None:
            raise VoltLibError(
                'Script "%s" already defined, '
                'script tags are case insensitive' % tag,
                location
            )
        self.langs_.enter_scope()
        langs = []
        while self.next_token_ != "END_SCRIPT":
            self.advance_lexer_()
            lang = self.parse_langsys_()
            self.expect_keyword_("END_LANGSYS")
            if self.langs_.resolve(lang.tag) is not None:
                raise VoltLibError(
                    'Language "%s" already defined in script "%s", '
                    'language tags are case insensitive' % (lang.tag, tag),
                    location
                )
            self.langs_.define(lang.tag, lang)
            langs.append(lang)
        self.expect_keyword_("END_SCRIPT")
        self.langs_.exit_scope()
        def_script = ast.ScriptDefinition(location, name, tag, langs)
        self.scripts_.define(tag, def_script)
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
        if not name[0].isalpha():
            raise VoltLibError(
                'Lookup name "%s" must start with a letter' % name,
                location
            )
        if self.lookups_.resolve(name) is not None:
            raise VoltLibError(
                'Lookup "%s" already defined, '
                'lookup names are case insensitive' % name,
                location
            )
        process_base = True
        if self.next_token_ == "PROCESS_BASE":
            self.advance_lexer_()
        elif self.next_token_ == "SKIP_BASE":
            self.advance_lexer_()
            process_base = False
        process_marks = True
        if self.next_token_ == "PROCESS_MARKS":
            self.advance_lexer_()
            if self.next_token_ == "MARK_GLYPH_SET":
                self.advance_lexer_()
                process_marks = self.expect_string_()
            elif self.next_token_type_ == Lexer.STRING:
                process_marks = self.expect_string_()
            elif self.next_token_ == "ALL":
                self.advance_lexer_()
            else:
                raise VoltLibError(
                    "Expected ALL, MARK_GLYPH_SET or an ID. "
                    "Got %s" % (self.next_token_type_),
                    location)
        elif self.next_token_ == "SKIP_MARKS":
            self.advance_lexer_()
            process_marks = False
        direction = None
        if self.next_token_ == "DIRECTION":
            self.expect_keyword_("DIRECTION")
            direction = self.expect_name_()
            assert direction in ("LTR", "RTL")
        reversal = None
        if self.next_token_ == "REVERSAL":
            self.expect_keyword_("REVERSAL")
            reversal = True
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
            sub = self.parse_substitution_(reversal)
        elif as_pos_or_sub == "AS_POSITION":
            pos = self.parse_position_()
        else:
            raise VoltLibError(
                "Expected AS_SUBSTITUTION or AS_POSITION. "
                "Got %s" % (as_pos_or_sub),
                location)
        def_lookup = ast.LookupDefinition(
            location, name, process_base, process_marks, direction, reversal,
            comments, context, sub, pos)
        self.lookups_.define(name, def_lookup)
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

    def parse_substitution_(self, reversal):
        assert self.is_cur_keyword_("AS_SUBSTITUTION")
        location = self.cur_token_location_
        src = []
        dest = []
        if self.next_token_ != "SUB":
            raise VoltLibError("Expected SUB", location)
        while self.next_token_ == "SUB":
            self.expect_keyword_("SUB")
            src.append(self.parse_coverage_())
            self.expect_keyword_("WITH")
            dest.append(self.parse_coverage_())
            self.expect_keyword_("END_SUB")
        self.expect_keyword_("END_SUBSTITUTION")
        max_src = max([len(cov) for cov in src])
        max_dest = max([len(cov) for cov in dest])
        # many to many or mixed is invalid
        if ((max_src > 1 and max_dest > 1) or
                (reversal and (max_src > 1 or max_dest > 1))):
            raise VoltLibError(
                "Invalid substitution type",
                location)
        mapping = OrderedDict(zip(tuple(src), tuple(dest)))
        if max_src == 1 and max_dest == 1:
            if reversal:
                sub = ast.SubstitutionReverseChainingSingleDefinition(
                    location, mapping)
            else:
                sub = ast.SubstitutionSingleDefinition(location, mapping)
        elif max_src == 1 and max_dest > 1:
            sub = ast.SubstitutionMultipleDefinition(location, mapping)
        elif max_src > 1 and max_dest == 1:
            sub = ast.SubstitutionLigatureDefinition(location, mapping)
        return sub

    def parse_position_(self):
        assert self.is_cur_keyword_("AS_POSITION")
        location = self.cur_token_location_
        pos_type = self.expect_name_()
        if pos_type not in (
                "ATTACH", "ATTACH_CURSIVE", "ADJUST_PAIR", "ADJUST_SINGLE"):
            raise VoltLibError(
                "Expected ATTACH, ATTACH_CURSIVE, ADJUST_PAIR, ADJUST_SINGLE",
                location)
        if pos_type == "ATTACH":
            position = self.parse_attach_()
        elif pos_type == "ATTACH_CURSIVE":
            position = self.parse_attach_cursive_()
        elif pos_type == "ADJUST_PAIR":
            position = self.parse_adjust_pair_()
        elif pos_type == "ADJUST_SINGLE":
            position = self.parse_adjust_single_()
        self.expect_keyword_("END_POSITION")
        return position

    def parse_attach_(self):
        assert self.is_cur_keyword_("ATTACH")
        location = self.cur_token_location_
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
        position = ast.PositionAttachDefinition(
            location, coverage, coverage_to)
        return position

    def parse_attach_cursive_(self):
        assert self.is_cur_keyword_("ATTACH_CURSIVE")
        location = self.cur_token_location_
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
        return position

    def parse_adjust_pair_(self):
        assert self.is_cur_keyword_("ADJUST_PAIR")
        location = self.cur_token_location_
        coverages_1 = []
        coverages_2 = []
        adjust_pair = {}
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
            adjust_pair[(id_1, id_2)] = (pos_1, pos_2)
        self.expect_keyword_("END_ADJUST")
        position = ast.PositionAdjustPairDefinition(
            location, coverages_1, coverages_2, adjust_pair)
        return position

    def parse_adjust_single_(self):
        assert self.is_cur_keyword_("ADJUST_SINGLE")
        location = self.cur_token_location_
        adjust_single = []
        while self.next_token_ != "END_ADJUST":
            coverages = self.parse_coverage_()
            self.expect_keyword_("BY")
            pos = self.parse_pos_()
            adjust_single.append((coverages, pos))
        self.expect_keyword_("END_ADJUST")
        position = ast.PositionAdjustSingleDefinition(
            location, adjust_single)
        return position

    def parse_def_anchor_(self):
        assert self.is_cur_keyword_("DEF_ANCHOR")
        location = self.cur_token_location_
        name = self.expect_string_()
        self.expect_keyword_("ON")
        gid = self.expect_number_()
        self.expect_keyword_("GLYPH")
        glyph_name = self.expect_name_()
        # check for duplicate anchor names on this glyph
        if (glyph_name in self.anchors_
                and self.anchors_[glyph_name].resolve(name) is not None):
            raise VoltLibError(
                'Anchor "%s" already defined, '
                'anchor names are case insensitive' % name,
                location
            )
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
        if glyph_name not in self.anchors_:
            self.anchors_[glyph_name] = SymbolTable()
        self.anchors_[glyph_name].define(name, anchor)
        return anchor

    def parse_adjust_by_(self):
        self.advance_lexer_()
        assert self.is_cur_keyword_("ADJUST_BY")
        adjustment = self.expect_number_()
        self.expect_keyword_("AT")
        size = self.expect_number_()
        return adjustment, size

    def parse_pos_(self):
        # VOLT syntax doesn't seem to take device Y advance
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
                adjustment, size = self.parse_adjust_by_()
                adv_adjust_by[size] = adjustment
        if self.next_token_ == "DX":
            self.advance_lexer_()
            dx = self.expect_number_()
            while self.next_token_ == "ADJUST_BY":
                adjustment, size = self.parse_adjust_by_()
                dx_adjust_by[size] = adjustment
        if self.next_token_ == "DY":
            self.advance_lexer_()
            dy = self.expect_number_()
            while self.next_token_ == "ADJUST_BY":
                adjustment, size = self.parse_adjust_by_()
                dy_adjust_by[size] = adjustment
        self.expect_keyword_("END_POS")
        return (adv, dx, dy, adv_adjust_by, dx_adjust_by, dy_adjust_by)

    def parse_unicode_values_(self):
        location = self.cur_token_location_
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
        location = self.cur_token_location_
        enum = self.parse_coverage_()
        self.expect_keyword_("END_ENUM")
        return enum

    def parse_coverage_(self):
        coverage = []
        location = self.cur_token_location_
        while self.next_token_ in ("GLYPH", "GROUP", "RANGE", "ENUM"):
            if self.next_token_ == "ENUM":
                self.advance_lexer_()
                enum = self.parse_enum_()
                coverage.append(enum)
            elif self.next_token_ == "GLYPH":
                self.expect_keyword_("GLYPH")
                name = self.expect_string_()
                coverage.append(name)
            elif self.next_token_ == "GROUP":
                self.expect_keyword_("GROUP")
                name = self.expect_string_()
                # resolved_group = self.groups_.resolve(name)
                group = (name,)
                coverage.append(group)
                # if resolved_group is not None:
                #     coverage.extend(resolved_group.enum)
                # # TODO: check that group exists after all groups are defined
                # else:
                #     group = (name,)
                #     coverage.append(group)
                #     # raise VoltLibError(
                #     #     'Glyph group "%s" is not defined' % name,
                #     #     location)
            elif self.next_token_ == "RANGE":
                self.expect_keyword_("RANGE")
                start = self.expect_string_()
                self.expect_keyword_("TO")
                end = self.expect_string_()
                coverage.append((start, end))
        return tuple(coverage)

    def resolve_group(self, group_name):
        return self.groups_.resolve(group_name)

    def glyph_range(self, start, end):
        rng = self.glyphs_.range(start, end)
        return frozenset(rng)

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


class SymbolTable(object):
    def __init__(self):
        self.scopes_ = [{}]

    def enter_scope(self):
        self.scopes_.append({})

    def exit_scope(self):
        self.scopes_.pop()

    def define(self, name, item):
        self.scopes_[-1][name] = item

    def resolve(self, name, case_insensitive=True):
        for scope in reversed(self.scopes_):
            item = scope.get(name)
            if item:
                return item
        if case_insensitive:
            for key in scope:
                if key.lower() == name.lower():
                    return scope[key]
        return None


class OrderedSymbolTable(SymbolTable):
    def __init__(self):
        self.scopes_ = [OrderedDict()]

    def enter_scope(self):
        self.scopes_.append(OrderedDict())

    def resolve(self, name, case_insensitive=False):
        SymbolTable.resolve(self, name, case_insensitive=case_insensitive)

    def range(self, start, end):
        for scope in reversed(self.scopes_):
            if start in scope and end in scope:
                start_idx = list(scope.keys()).index(start)
                end_idx = list(scope.keys()).index(end)
                return list(scope.keys())[start_idx:end_idx + 1]
        return None
