from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.lexer import Lexer, IncludingLexer
import fontTools.feaLib.ast as ast
import os
import re


class Parser(object):
    def __init__(self, path):
        self.doc_ = ast.FeatureFile()
        self.anchors_ = SymbolTable()
        self.glyphclasses_ = SymbolTable()
        self.lookups_ = SymbolTable()
        self.valuerecords_ = SymbolTable()
        self.symbol_tables_ = {
            self.anchors_, self.glyphclasses_,
            self.lookups_, self.valuerecords_
        }
        self.next_token_type_, self.next_token_ = (None, None)
        self.next_token_location_ = None
        self.lexer_ = IncludingLexer(path)
        self.advance_lexer_()

    def parse(self):
        statements = self.doc_.statements
        while self.next_token_type_ is not None:
            self.advance_lexer_()
            if self.cur_token_type_ is Lexer.GLYPHCLASS:
                statements.append(self.parse_glyphclass_definition_())
            elif self.is_cur_keyword_("anchorDef"):
                statements.append(self.parse_anchordef_())
            elif self.is_cur_keyword_("languagesystem"):
                statements.append(self.parse_languagesystem_())
            elif self.is_cur_keyword_("lookup"):
                statements.append(self.parse_lookup_(vertical=False))
            elif self.is_cur_keyword_("feature"):
                statements.append(self.parse_feature_block_())
            elif self.is_cur_keyword_("valueRecordDef"):
                statements.append(
                    self.parse_valuerecord_definition_(vertical=False))
            else:
                raise FeatureLibError("Expected feature, languagesystem, "
                                      "lookup, or glyph class definition",
                                      self.cur_token_location_)
        return self.doc_

    def parse_anchordef_(self):
        assert self.is_cur_keyword_("anchorDef")
        location = self.cur_token_location_
        x, y = self.expect_number_(), self.expect_number_()
        contourpoint = None
        if self.next_token_ == "contourpoint":
            self.expect_keyword_("contourpoint")
            contourpoint = self.expect_number_()
        name = self.expect_name_()
        self.expect_symbol_(";")
        anchordef = ast.AnchorDefinition(location, name, x, y, contourpoint)
        self.anchors_.define(name, anchordef)
        return anchordef

    def parse_glyphclass_definition_(self):
        location, name = self.cur_token_location_, self.cur_token_
        self.expect_symbol_("=")
        glyphs = self.parse_glyphclass_(accept_glyphname=False)
        self.expect_symbol_(";")
        if self.glyphclasses_.resolve(name) is not None:
            raise FeatureLibError("Glyph class @%s already defined" % name,
                                  location)
        glyphclass = ast.GlyphClassDefinition(location, name, glyphs)
        self.glyphclasses_.define(name, glyphclass)
        return glyphclass

    def parse_glyphclass_(self, accept_glyphname):
        result = set()
        if accept_glyphname and self.next_token_type_ is Lexer.NAME:
            result.add(self.expect_name_())
            return result
        if self.next_token_type_ is Lexer.GLYPHCLASS:
            self.advance_lexer_()
            gc = self.glyphclasses_.resolve(self.cur_token_)
            if gc is None:
                raise FeatureLibError(
                    "Unknown glyph class @%s" % self.cur_token_,
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
                gc = self.glyphclasses_.resolve(self.cur_token_)
                if gc is None:
                    raise FeatureLibError(
                        "Unknown glyph class @%s" % self.cur_token_,
                        self.cur_token_location_)
                result.update(gc.glyphs)
            else:
                raise FeatureLibError(
                    "Expected glyph name, glyph range, "
                    "or glyph class reference",
                    self.cur_token_location_)
        self.expect_symbol_("]")
        return result

    def parse_glyph_pattern_(self):
        prefix, glyphs, lookups, suffix = ([], [], [], [])
        while self.next_token_ not in {"by", "from", ";"}:
            gc = self.parse_glyphclass_(accept_glyphname=True)
            marked = False
            if self.next_token_ == "'":
                self.expect_symbol_("'")
                marked = True
            if marked:
                glyphs.append(gc)
            elif glyphs:
                suffix.append(gc)
            else:
                prefix.append(gc)

            lookup = None
            if self.next_token_ == "lookup":
                self.expect_keyword_("lookup")
                if not marked:
                    raise FeatureLibError(
                        "Lookups can only follow marked glyphs",
                        self.cur_token_location_)
                lookup_name = self.expect_name_()
                lookup = self.lookups_.resolve(lookup_name)
                if lookup is None:
                    raise FeatureLibError(
                        'Unknown lookup "%s"' % lookup_name,
                        self.cur_token_location_)
            if marked:
                lookups.append(lookup)

        if not glyphs and not suffix:  # eg., "sub f f i by"
            assert lookups == []
            return ([], prefix, [None] * len(prefix), [])
        else:
            return (prefix, glyphs, lookups, suffix)

    def parse_ignore_(self):
        assert self.is_cur_keyword_("ignore")
        location = self.cur_token_location_
        self.advance_lexer_()
        if self.cur_token_ in ["substitute", "sub"]:
            prefix, glyphs, lookups, suffix = self.parse_glyph_pattern_()
            self.expect_symbol_(";")
            return ast.IgnoreSubstitutionRule(location, prefix, glyphs, suffix)
        raise FeatureLibError(
            "Expected \"substitute\"", self.next_token_location_)

    def parse_language_(self):
        assert self.is_cur_keyword_("language")
        location = self.cur_token_location_
        language = self.expect_language_tag_()
        include_default, required = (True, False)
        if self.next_token_ in {"exclude_dflt", "include_dflt"}:
            include_default = (self.expect_name_() == "include_dflt")
        if self.next_token_ == "required":
            self.expect_keyword_("required")
            required = True
        self.expect_symbol_(";")
        return ast.LanguageStatement(location, language,
                                     include_default, required)

    def parse_lookup_(self, vertical):
        assert self.is_cur_keyword_("lookup")
        location, name = self.cur_token_location_, self.expect_name_()

        if self.next_token_ == ";":
            lookup = self.lookups_.resolve(name)
            if lookup is None:
                raise FeatureLibError("Unknown lookup \"%s\"" % name,
                                      self.cur_token_location_)
            self.expect_symbol_(";")
            return ast.LookupReferenceStatement(location, lookup)

        use_extension = False
        if self.next_token_ == "useExtension":
            self.expect_keyword_("useExtension")
            use_extension = True

        block = ast.LookupBlock(location, name, use_extension)
        self.parse_block_(block, vertical)
        self.lookups_.define(name, block)
        return block

    def parse_script_(self):
        assert self.is_cur_keyword_("script")
        location, script = self.cur_token_location_, self.expect_script_tag_()
        self.expect_symbol_(";")
        return ast.ScriptStatement(location, script)

    def parse_substitute_(self):
        assert self.cur_token_ in {"substitute", "sub"}
        location = self.cur_token_location_
        old_prefix, old, lookups, old_suffix = self.parse_glyph_pattern_()

        new = []
        if self.next_token_ == "by":
            keyword = self.expect_keyword_("by")
            while self.next_token_ != ";":
                new.append(self.parse_glyphclass_(accept_glyphname=True))
        elif self.next_token_ == "from":
            keyword = self.expect_keyword_("from")
            new = [self.parse_glyphclass_(accept_glyphname=False)]
        else:
            keyword = None
        self.expect_symbol_(";")
        if len(new) is 0 and not any(lookups):
            raise FeatureLibError(
                'Expected "by", "from" or explicit lookup references',
                self.cur_token_location_)

        # GSUB lookup type 3: Alternate substitution.
        # Format: "substitute a from [a.1 a.2 a.3];"
        if keyword == "from":
            if len(old) != 1 or len(old[0]) != 1:
                raise FeatureLibError(
                    'Expected a single glyph before "from"',
                    location)
            if len(new) != 1:
                raise FeatureLibError(
                    'Expected a single glyphclass after "from"',
                    location)
            return ast.AlternateSubstitution(location, list(old[0])[0], new[0])

        num_lookups = len([l for l in lookups if l is not None])

        # GSUB lookup type 1: Single substitution.
        # Format A: "substitute a by a.sc;"
        # Format B: "substitute [one.fitted one.oldstyle] by one;"
        # Format C: "substitute [a-d] by [A.sc-D.sc];"
        if (len(old_prefix) == 0 and len(old_suffix) == 0 and
                len(old) == 1 and len(new) == 1 and num_lookups == 0):
            glyphs, replacements = sorted(list(old[0])), sorted(list(new[0]))
            if len(replacements) == 1:
                replacements = replacements * len(glyphs)
            if len(glyphs) != len(replacements):
                raise FeatureLibError(
                    'Expected a glyph class with %d elements after "by", '
                    'but found a glyph class with %d elements' %
                    (len(glyphs), len(replacements)), location)
            return ast.SingleSubstitution(location,
                                          dict(zip(glyphs, replacements)))

        # GSUB lookup type 2: Multiple substitution.
        # Format: "substitute f_f_i by f f i;"
        if (len(old_prefix) == 0 and len(old_suffix) == 0 and
                len(old) == 1 and len(old[0]) == 1 and
                len(new) > 1 and max([len(n) for n in new]) == 1 and
                num_lookups == 0):
            return ast.MultipleSubstitution(location, tuple(old[0])[0],
                                            tuple([list(n)[0] for n in new]))

        # GSUB lookup type 4: Ligature substitution.
        # Format: "substitute f f i by f_f_i;"
        if (len(old_prefix) == 0 and len(old_suffix) == 0 and
                len(old) > 1 and len(new) == 1 and len(new[0]) == 1 and
                num_lookups == 0):
            return ast.LigatureSubstitution(location, old, list(new[0])[0])

        rule = ast.SubstitutionRule(location, old, new)
        rule.old_prefix, rule.old_suffix = old_prefix, old_suffix
        rule.lookups = lookups
        return rule

    def parse_subtable_(self):
        assert self.is_cur_keyword_("subtable")
        location = self.cur_token_location_
        self.expect_symbol_(";")
        return ast.SubtableStatement(location)

    def parse_valuerecord_(self, vertical):
        if self.next_token_type_ is Lexer.NUMBER:
            number, location = self.expect_number_(), self.cur_token_location_
            if vertical:
                val = ast.ValueRecord(location, 0, 0, 0, number)
            else:
                val = ast.ValueRecord(location, 0, 0, number, 0)
            return val
        self.expect_symbol_("<")
        location = self.cur_token_location_
        if self.next_token_type_ is Lexer.NAME:
            name = self.expect_name_()
            vrd = self.valuerecords_.resolve(name)
            if vrd is None:
                raise FeatureLibError("Unknown valueRecordDef \"%s\"" % name,
                                      self.cur_token_location_)
            value = vrd.value
            xPlacement, yPlacement = (value.xPlacement, value.yPlacement)
            xAdvance, yAdvance = (value.xAdvance, value.yAdvance)
        else:
            xPlacement, yPlacement, xAdvance, yAdvance = (
                self.expect_number_(), self.expect_number_(),
                self.expect_number_(), self.expect_number_())
        self.expect_symbol_(">")
        return ast.ValueRecord(
            location, xPlacement, yPlacement, xAdvance, yAdvance)

    def parse_valuerecord_definition_(self, vertical):
        assert self.is_cur_keyword_("valueRecordDef")
        location = self.cur_token_location_
        value = self.parse_valuerecord_(vertical)
        name = self.expect_name_()
        self.expect_symbol_(";")
        vrd = ast.ValueRecordDefinition(location, name, value)
        self.valuerecords_.define(name, vrd)
        return vrd

    def parse_languagesystem_(self):
        assert self.cur_token_ == "languagesystem"
        location = self.cur_token_location_
        script = self.expect_script_tag_()
        language = self.expect_language_tag_()
        self.expect_symbol_(";")
        if script == "DFLT" and language != "dflt":
            raise FeatureLibError(
                'For script "DFLT", the language must be "dflt"',
                self.cur_token_location_)
        return ast.LanguageSystemStatement(location, script, language)

    def parse_feature_block_(self):
        assert self.cur_token_ == "feature"
        location = self.cur_token_location_
        tag = self.expect_tag_()
        vertical = (tag == "vkrn")

        use_extension = False
        if self.next_token_ == "useExtension":
            self.expect_keyword_("useExtension")
            use_extension = True

        block = ast.FeatureBlock(location, tag, use_extension)
        self.parse_block_(block, vertical)
        return block

    def parse_block_(self, block, vertical):
        self.expect_symbol_("{")
        for symtab in self.symbol_tables_:
            symtab.enter_scope()

        statements = block.statements
        while self.next_token_ != "}":
            self.advance_lexer_()
            if self.cur_token_type_ is Lexer.GLYPHCLASS:
                statements.append(self.parse_glyphclass_definition_())
            elif self.is_cur_keyword_("anchorDef"):
                statements.append(self.parse_anchordef_())
            elif self.is_cur_keyword_("ignore"):
                statements.append(self.parse_ignore_())
            elif self.is_cur_keyword_("language"):
                statements.append(self.parse_language_())
            elif self.is_cur_keyword_("lookup"):
                statements.append(self.parse_lookup_(vertical))
            elif self.is_cur_keyword_("script"):
                statements.append(self.parse_script_())
            elif (self.is_cur_keyword_("substitute") or
                  self.is_cur_keyword_("sub")):
                statements.append(self.parse_substitute_())
            elif self.is_cur_keyword_("subtable"):
                statements.append(self.parse_subtable_())
            elif self.is_cur_keyword_("valueRecordDef"):
                statements.append(self.parse_valuerecord_definition_(vertical))
            else:
                raise FeatureLibError(
                    "Expected glyph class definition or statement",
                    self.cur_token_location_)

        self.expect_symbol_("}")
        for symtab in self.symbol_tables_:
            symtab.exit_scope()

        name = self.expect_name_()
        if name != block.name.strip():
            raise FeatureLibError("Expected \"%s\"" % block.name.strip(),
                                  self.cur_token_location_)
        self.expect_symbol_(";")

    def is_cur_keyword_(self, k):
        return (self.cur_token_type_ is Lexer.NAME) and (self.cur_token_ == k)

    def expect_tag_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is not Lexer.NAME:
            raise FeatureLibError("Expected a tag", self.cur_token_location_)
        if len(self.cur_token_) > 4:
            raise FeatureLibError("Tags can not be longer than 4 characters",
                                  self.cur_token_location_)
        return (self.cur_token_ + "    ")[:4]

    def expect_script_tag_(self):
        tag = self.expect_tag_()
        if tag == "dflt":
            raise FeatureLibError(
                '"dflt" is not a valid script tag; use "DFLT" instead',
                self.cur_token_location_)
        return tag

    def expect_language_tag_(self):
        tag = self.expect_tag_()
        if tag == "DFLT":
            raise FeatureLibError(
                '"DFLT" is not a valid language tag; use "dflt" instead',
                self.cur_token_location_)
        return tag

    def expect_symbol_(self, symbol):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.SYMBOL and self.cur_token_ == symbol:
            return symbol
        raise FeatureLibError("Expected '%s'" % symbol,
                              self.cur_token_location_)

    def expect_keyword_(self, keyword):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME and self.cur_token_ == keyword:
            return self.cur_token_
        raise FeatureLibError("Expected \"%s\"" % keyword,
                              self.cur_token_location_)

    def expect_name_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME:
            return self.cur_token_
        raise FeatureLibError("Expected a name", self.cur_token_location_)

    def expect_number_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NUMBER:
            return self.cur_token_
        raise FeatureLibError("Expected a number", self.cur_token_location_)

    def advance_lexer_(self):
        self.cur_token_type_, self.cur_token_, self.cur_token_location_ = (
            self.next_token_type_, self.next_token_, self.next_token_location_)
        try:
            (self.next_token_type_, self.next_token_,
             self.next_token_location_) = self.lexer_.next()
        except StopIteration:
            self.next_token_type_, self.next_token_ = (None, None)

    @staticmethod
    def reverse_string_(s):
        """'abc' --> 'cba'"""
        return ''.join(reversed(list(s)))

    def make_glyph_range_(self, location, start, limit):
        """("a.sc", "d.sc") --> {"a.sc", "b.sc", "c.sc", "d.sc"}"""
        result = set()
        if len(start) != len(limit):
            raise FeatureLibError(
                "Bad range: \"%s\" and \"%s\" should have the same length" %
                (start, limit), location)

        rev = self.reverse_string_
        prefix = os.path.commonprefix([start, limit])
        suffix = rev(os.path.commonprefix([rev(start), rev(limit)]))
        if len(suffix) > 0:
            start_range = start[len(prefix):-len(suffix)]
            limit_range = limit[len(prefix):-len(suffix)]
        else:
            start_range = start[len(prefix):]
            limit_range = limit[len(prefix):]

        if start_range >= limit_range:
            raise FeatureLibError(
                "Start of range must be smaller than its end",
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

        raise FeatureLibError("Bad range: \"%s-%s\"" % (start, limit),
                              location)


class SymbolTable(object):
    def __init__(self):
        self.scopes_ = [{}]

    def enter_scope(self):
        self.scopes_.append({})

    def exit_scope(self):
        self.scopes_.pop()

    def define(self, name, item):
        self.scopes_[-1][name] = item

    def resolve(self, name):
        for scope in reversed(self.scopes_):
            item = scope.get(name)
            if item:
                return item
        return None
