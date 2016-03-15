from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.lexer import Lexer, IncludingLexer
from fontTools.misc.py23 import *
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
            self.anchors_, self.valuerecords_
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
            elif self.is_cur_keyword_("markClass"):
                statements.append(self.parse_markClass_())
            elif self.is_cur_keyword_("feature"):
                statements.append(self.parse_feature_block_())
            elif self.is_cur_keyword_("table"):
                statements.append(self.parse_table_())
            elif self.is_cur_keyword_("valueRecordDef"):
                statements.append(
                    self.parse_valuerecord_definition_(vertical=False))
            else:
                raise FeatureLibError(
                    "Expected feature, languagesystem, lookup, markClass, "
                    "table, or glyph class definition",
                    self.cur_token_location_)
        return self.doc_

    def parse_anchor_(self):
        self.expect_symbol_("<")
        self.expect_keyword_("anchor")
        location = self.cur_token_location_

        if self.next_token_ == "NULL":
            self.expect_keyword_("NULL")
            self.expect_symbol_(">")
            return None

        if self.next_token_type_ == Lexer.NAME:
            name = self.expect_name_()
            anchordef = self.anchors_.resolve(name)
            if anchordef is None:
                raise FeatureLibError(
                    'Unknown anchor "%s"' % name,
                    self.cur_token_location_)
            self.expect_symbol_(">")
            return ast.Anchor(location, anchordef.x, anchordef.y,
                              anchordef.contourpoint,
                              xDeviceTable=None, yDeviceTable=None)

        x, y = self.expect_number_(), self.expect_number_()

        contourpoint = None
        if self.next_token_ == "contourpoint":
            self.expect_keyword_("contourpoint")
            contourpoint = self.expect_number_()

        if self.next_token_ == "<":
            xDeviceTable = self.parse_device_()
            yDeviceTable = self.parse_device_()
        else:
            xDeviceTable, yDeviceTable = None, None

        self.expect_symbol_(">")
        return ast.Anchor(location, x, y, contourpoint,
                          xDeviceTable, yDeviceTable)

    def parse_anchor_marks_(self):
        """Parses a sequence of [<anchor> mark @MARKCLASS]*."""
        anchorMarks = []  # [(ast.Anchor, markClassName)*]
        while self.next_token_ == "<":
            anchor = self.parse_anchor_()
            if anchor is None and self.next_token_ != "mark":
                continue  # <anchor NULL> without mark, eg. in GPOS type 5
            self.expect_keyword_("mark")
            markClass = self.expect_markClass_reference_()
            anchorMarks.append((anchor, markClass))
        return anchorMarks

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

    def parse_attach_(self):
        assert self.is_cur_keyword_("Attach")
        location = self.cur_token_location_
        glyphs = self.parse_glyphclass_(accept_glyphname=True)
        contourPoints = {self.expect_number_()}
        while self.next_token_ != ";":
            contourPoints.add(self.expect_number_())
        self.expect_symbol_(";")
        return ast.AttachStatement(location, glyphs, contourPoints)

    def parse_enumerate_(self, vertical):
        assert self.cur_token_ in {"enumerate", "enum"}
        self.advance_lexer_()
        return self.parse_position_(enumerated=True, vertical=vertical)

    def parse_GlyphClassDef_(self):
        """Parses 'GlyphClassDef @BASE, @LIGATURES, @MARKS, @COMPONENTS;'"""
        assert self.is_cur_keyword_("GlyphClassDef")
        location = self.cur_token_location_
        if self.next_token_ != ",":
            baseGlyphs = self.parse_glyphclass_(accept_glyphname=False)
        else:
            baseGlyphs = None
        self.expect_symbol_(",")
        if self.next_token_ != ",":
            ligatureGlyphs = self.parse_glyphclass_(accept_glyphname=False)
        else:
            ligatureGlyphs = None
        self.expect_symbol_(",")
        if self.next_token_ != ",":
            markGlyphs = self.parse_glyphclass_(accept_glyphname=False)
        else:
            markGlyphs = None
        self.expect_symbol_(",")
        if self.next_token_ != ";":
            componentGlyphs = self.parse_glyphclass_(accept_glyphname=False)
        else:
            componentGlyphs = None
        self.expect_symbol_(";")
        return ast.GlyphClassDefStatement(location, baseGlyphs, markGlyphs,
                                          ligatureGlyphs, componentGlyphs)

    def parse_glyphclass_definition_(self):
        """Parses glyph class definitions such as '@UPPERCASE = [A-Z];'"""
        location, name = self.cur_token_location_, self.cur_token_
        self.expect_symbol_("=")
        glyphs = self.parse_glyphclass_(accept_glyphname=False).glyphSet()
        self.expect_symbol_(";")
        glyphclass = ast.GlyphClassDefinition(location, name, glyphs)
        self.glyphclasses_.define(name, glyphclass)
        return glyphclass

    def parse_glyphclass_(self, accept_glyphname):
        if (accept_glyphname and
                self.next_token_type_ in (Lexer.NAME, Lexer.CID)):
            glyph = self.expect_glyph_()
            return ast.GlyphName(self.cur_token_location_, glyph)
        if self.next_token_type_ is Lexer.GLYPHCLASS:
            self.advance_lexer_()
            gc = self.glyphclasses_.resolve(self.cur_token_)
            if gc is None:
                raise FeatureLibError(
                    "Unknown glyph class @%s" % self.cur_token_,
                    self.cur_token_location_)
            if isinstance(gc, ast.MarkClass):
                return ast.MarkClassName(self.cur_token_location_, gc)
            else:
                return ast.GlyphClassName(self.cur_token_location_, gc)

        self.expect_symbol_("[")
        glyphs = set()
        location = self.cur_token_location_
        while self.next_token_ != "]":
            if self.next_token_type_ is Lexer.NAME:
                glyph = self.expect_glyph_()
                if self.next_token_ == "-":
                    range_location = self.cur_token_location_
                    range_start = glyph
                    self.expect_symbol_("-")
                    range_end = self.expect_glyph_()
                    glyphs.update(self.make_glyph_range_(range_location,
                                                         range_start,
                                                         range_end))
                else:
                    glyphs.add(glyph)
            elif self.next_token_type_ is Lexer.CID:
                glyph = self.expect_glyph_()
                if self.next_token_ == "-":
                    range_location = self.cur_token_location_
                    range_start = self.cur_token_
                    self.expect_symbol_("-")
                    range_end = self.expect_cid_()
                    glyphs.update(self.make_cid_range_(range_location,
                                                       range_start, range_end))
                else:
                    glyphs.add("cid%05d" % self.cur_token_)
            elif self.next_token_type_ is Lexer.GLYPHCLASS:
                self.advance_lexer_()
                gc = self.glyphclasses_.resolve(self.cur_token_)
                if gc is None:
                    raise FeatureLibError(
                        "Unknown glyph class @%s" % self.cur_token_,
                        self.cur_token_location_)
                glyphs.update(gc.glyphSet())
            else:
                raise FeatureLibError(
                    "Expected glyph name, glyph range, "
                    "or glyph class reference",
                    self.next_token_location_)
        self.expect_symbol_("]")
        return ast.GlyphClass(location, glyphs)

    def parse_class_name_(self):
        name = self.expect_class_name_()
        gc = self.glyphclasses_.resolve(name)
        if gc is None:
            raise FeatureLibError(
                "Unknown glyph class @%s" % name,
                self.cur_token_location_)
        if isinstance(gc, ast.MarkClass):
            return ast.MarkClassName(self.cur_token_location_, gc)
        else:
            return ast.GlyphClassName(self.cur_token_location_, gc)

    def parse_glyph_pattern_(self, vertical):
        prefix, glyphs, lookups, values, suffix = ([], [], [], [], [])
        hasMarks = False
        while self.next_token_ not in {"by", "from", ";", ","}:
            gc = self.parse_glyphclass_(accept_glyphname=True)
            marked = False
            if self.next_token_ == "'":
                self.expect_symbol_("'")
                hasMarks = marked = True
            if marked:
                glyphs.append(gc)
            elif glyphs:
                suffix.append(gc)
            else:
                prefix.append(gc)

            if self.is_next_value_():
                values.append(self.parse_valuerecord_(vertical))
            else:
                values.append(None)

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
            return ([], prefix, [None] * len(prefix), values, [], hasMarks)
        else:
            assert not any(values[:len(prefix)]), values
            values = values[len(prefix):][:len(glyphs)]
            return (prefix, glyphs, lookups, values, suffix, hasMarks)

    def parse_chain_context_(self):
        location = self.cur_token_location_
        prefix, glyphs, lookups, values, suffix, hasMarks = \
            self.parse_glyph_pattern_(vertical=False)
        chainContext = [(prefix, glyphs, suffix)]
        hasLookups = any(lookups)
        while self.next_token_ == ",":
            self.expect_symbol_(",")
            prefix, glyphs, lookups, values, suffix, hasMarks = \
                self.parse_glyph_pattern_(vertical=False)
            chainContext.append((prefix, glyphs, suffix))
            hasLookups = hasLookups or any(lookups)
        self.expect_symbol_(";")
        return chainContext, hasLookups

    def parse_ignore_(self):
        assert self.is_cur_keyword_("ignore")
        location = self.cur_token_location_
        self.advance_lexer_()
        if self.cur_token_ in ["substitute", "sub"]:
            chainContext, hasLookups = self.parse_chain_context_()
            if hasLookups:
                raise FeatureLibError(
                    "No lookups can be specified for \"ignore sub\"",
                    location)
            return ast.IgnoreSubstStatement(location, chainContext)
        if self.cur_token_ in ["position", "pos"]:
            chainContext, hasLookups = self.parse_chain_context_()
            if hasLookups:
                raise FeatureLibError(
                    "No lookups can be specified for \"ignore pos\"",
                    location)
            return ast.IgnorePosStatement(location, chainContext)
        raise FeatureLibError(
            "Expected \"substitute\" or \"position\"",
            self.cur_token_location_)

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

    def parse_ligatureCaretByIndex_(self):
        assert self.is_cur_keyword_("LigatureCaretByIndex")
        location = self.cur_token_location_
        glyphs = self.parse_glyphclass_(accept_glyphname=True)
        carets = {self.expect_number_()}
        while self.next_token_ != ";":
            carets.add(self.expect_number_())
        self.expect_symbol_(";")
        return ast.LigatureCaretByIndexStatement(location, glyphs, carets)

    def parse_ligatureCaretByPos_(self):
        assert self.is_cur_keyword_("LigatureCaretByPos")
        location = self.cur_token_location_
        glyphs = self.parse_glyphclass_(accept_glyphname=True)
        carets = {self.expect_number_()}
        while self.next_token_ != ";":
            carets.add(self.expect_number_())
        self.expect_symbol_(";")
        return ast.LigatureCaretByPosStatement(location, glyphs, carets)

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

    def parse_lookupflag_(self):
        assert self.is_cur_keyword_("lookupflag")
        location = self.cur_token_location_

        # format B: "lookupflag 6;"
        if self.next_token_type_ == Lexer.NUMBER:
            value = self.expect_number_()
            self.expect_symbol_(";")
            return ast.LookupFlagStatement(location, value, None, None)

        # format A: "lookupflag RightToLeft MarkAttachmentType @M;"
        value, markAttachment, markFilteringSet = 0, None, None
        flags = {
            "RightToLeft": 1, "IgnoreBaseGlyphs": 2,
            "IgnoreLigatures": 4, "IgnoreMarks": 8
        }
        seen = set()
        while self.next_token_ != ";":
            if self.next_token_ in seen:
                raise FeatureLibError(
                    "%s can be specified only once" % self.next_token_,
                    self.next_token_location_)
            seen.add(self.next_token_)
            if self.next_token_ == "MarkAttachmentType":
                self.expect_keyword_("MarkAttachmentType")
                markAttachment = self.parse_class_name_()
            elif self.next_token_ == "UseMarkFilteringSet":
                self.expect_keyword_("UseMarkFilteringSet")
                markFilteringSet = self.parse_class_name_()
            elif self.next_token_ in flags:
                value = value | flags[self.expect_name_()]
            else:
                raise FeatureLibError(
                    '"%s" is not a recognized lookupflag' % self.next_token_,
                    self.next_token_location_)
        self.expect_symbol_(";")
        return ast.LookupFlagStatement(location, value,
                                       markAttachment, markFilteringSet)

    def parse_markClass_(self):
        assert self.is_cur_keyword_("markClass")
        location = self.cur_token_location_
        glyphs = self.parse_glyphclass_(accept_glyphname=True)
        anchor = self.parse_anchor_()
        name = self.expect_class_name_()
        self.expect_symbol_(";")
        markClass = self.doc_.markClasses.get(name)
        if markClass is None:
            markClass = ast.MarkClass(name)
            self.doc_.markClasses[name] = markClass
            self.glyphclasses_.define(name, markClass)
        mcdef = ast.MarkClassDefinition(location, markClass, anchor, glyphs)
        markClass.addDefinition(mcdef)
        return mcdef

    def parse_position_(self, enumerated, vertical):
        assert self.cur_token_ in {"position", "pos"}
        if self.next_token_ == "cursive":  # GPOS type 3
            return self.parse_position_cursive_(enumerated, vertical)
        elif self.next_token_ == "base":   # GPOS type 4
            return self.parse_position_base_(enumerated, vertical)
        elif self.next_token_ == "ligature":   # GPOS type 5
            return self.parse_position_ligature_(enumerated, vertical)
        elif self.next_token_ == "mark":   # GPOS type 6
            return self.parse_position_mark_(enumerated, vertical)

        location = self.cur_token_location_
        prefix, glyphs, lookups, values, suffix, hasMarks = \
            self.parse_glyph_pattern_(vertical)
        self.expect_symbol_(";")

        if any(lookups):
            # GPOS type 8: Chaining contextual positioning; explicit lookups
            if any(values):
                raise FeatureLibError(
                    "If \"lookup\" is present, no values must be specified",
                    location)
            return ast.ChainContextPosStatement(
                location, prefix, glyphs, suffix, lookups)

        # Pair positioning, format A: "pos V 10 A -10;"
        # Pair positioning, format B: "pos V A -20;"
        if not prefix and not suffix and len(glyphs) == 2 and not hasMarks:
            if values[0] is None:  # Format B: "pos V A -20;"
                values.reverse()
            return ast.PairPosStatement(
                location, enumerated,
                glyphs[0], values[0], glyphs[1], values[1])

        if enumerated:
            raise FeatureLibError(
                '"enumerate" is only allowed with pair positionings', location)
        return ast.SinglePosStatement(location, list(zip(glyphs, values)),
                                      prefix, suffix, forceChain=hasMarks)

    def parse_position_cursive_(self, enumerated, vertical):
        location = self.cur_token_location_
        self.expect_keyword_("cursive")
        if enumerated:
            raise FeatureLibError(
                '"enumerate" is not allowed with '
                'cursive attachment positioning',
                location)
        glyphclass = self.parse_glyphclass_(accept_glyphname=True).glyphSet()
        entryAnchor = self.parse_anchor_()
        exitAnchor = self.parse_anchor_()
        self.expect_symbol_(";")
        return ast.CursivePosStatement(
            location, glyphclass, entryAnchor, exitAnchor)

    def parse_position_base_(self, enumerated, vertical):
        location = self.cur_token_location_
        self.expect_keyword_("base")
        if enumerated:
            raise FeatureLibError(
                '"enumerate" is not allowed with '
                'mark-to-base attachment positioning',
                location)
        base = self.parse_glyphclass_(accept_glyphname=True).glyphSet()
        marks = self.parse_anchor_marks_()
        self.expect_symbol_(";")
        return ast.MarkBasePosStatement(location, base, marks)

    def parse_position_ligature_(self, enumerated, vertical):
        location = self.cur_token_location_
        self.expect_keyword_("ligature")
        if enumerated:
            raise FeatureLibError(
                '"enumerate" is not allowed with '
                'mark-to-ligature attachment positioning',
                location)
        ligatures = self.parse_glyphclass_(accept_glyphname=True).glyphSet()
        marks = [self.parse_anchor_marks_()]
        while self.next_token_ == "ligComponent":
            self.expect_keyword_("ligComponent")
            marks.append(self.parse_anchor_marks_())
        self.expect_symbol_(";")
        return ast.MarkLigPosStatement(location, ligatures, marks)

    def parse_position_mark_(self, enumerated, vertical):
        location = self.cur_token_location_
        self.expect_keyword_("mark")
        if enumerated:
            raise FeatureLibError(
                '"enumerate" is not allowed with '
                'mark-to-mark attachment positioning',
                location)
        baseMarks = self.parse_glyphclass_(accept_glyphname=True).glyphSet()
        marks = self.parse_anchor_marks_()
        self.expect_symbol_(";")
        return ast.MarkMarkPosStatement(location, baseMarks, marks)

    def parse_script_(self):
        assert self.is_cur_keyword_("script")
        location, script = self.cur_token_location_, self.expect_script_tag_()
        self.expect_symbol_(";")
        return ast.ScriptStatement(location, script)

    def parse_substitute_(self):
        assert self.cur_token_ in {"substitute", "sub", "reversesub", "rsub"}
        location = self.cur_token_location_
        reverse = self.cur_token_ in {"reversesub", "rsub"}
        old_prefix, old, lookups, values, old_suffix, hasMarks = \
            self.parse_glyph_pattern_(vertical=False)
        if any(values):
            raise FeatureLibError(
                "Substitution statements cannot contain values", location)
        new = []
        if self.next_token_ == "by":
            keyword = self.expect_keyword_("by")
            while self.next_token_ != ";":
                gc = self.parse_glyphclass_(accept_glyphname=True)
                new.append(gc)
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
            if reverse:
                raise FeatureLibError(
                    'Reverse chaining substitutions do not support "from"',
                    location)
            if len(old) != 1 or len(old[0].glyphSet()) != 1:
                raise FeatureLibError(
                    'Expected a single glyph before "from"',
                    location)
            if len(new) != 1:
                raise FeatureLibError(
                    'Expected a single glyphclass after "from"',
                    location)
            return ast.AlternateSubstStatement(
                location, old_prefix, old[0], old_suffix, new[0])

        num_lookups = len([l for l in lookups if l is not None])

        # GSUB lookup type 1: Single substitution.
        # Format A: "substitute a by a.sc;"
        # Format B: "substitute [one.fitted one.oldstyle] by one;"
        # Format C: "substitute [a-d] by [A.sc-D.sc];"
        if (not reverse and len(old) == 1 and len(new) == 1 and
                num_lookups == 0):
            glyphs = sorted(list(old[0].glyphSet()))
            replacements = sorted(list(new[0].glyphSet()))
            if len(replacements) == 1:
                replacements = replacements * len(glyphs)
            if len(glyphs) != len(replacements):
                raise FeatureLibError(
                    'Expected a glyph class with %d elements after "by", '
                    'but found a glyph class with %d elements' %
                    (len(glyphs), len(replacements)), location)
            return ast.SingleSubstStatement(location,
                                            dict(zip(glyphs, replacements)),
                                            old_prefix, old_suffix,
                                            forceChain=hasMarks)

        # GSUB lookup type 2: Multiple substitution.
        # Format: "substitute f_f_i by f f i;"
        if (not reverse and
                len(old) == 1 and len(old[0].glyphSet()) == 1 and
                len(new) > 1 and max([len(n.glyphSet()) for n in new]) == 1 and
                num_lookups == 0):
            return ast.MultipleSubstStatement(
                location, old_prefix, tuple(old[0].glyphSet())[0], old_suffix,
                tuple([list(n.glyphSet())[0] for n in new]))

        # GSUB lookup type 4: Ligature substitution.
        # Format: "substitute f f i by f_f_i;"
        if (not reverse and
                len(old) > 1 and len(new) == 1 and
                len(new[0].glyphSet()) == 1 and
                num_lookups == 0):
            return ast.LigatureSubstStatement(
                location, old_prefix, old, old_suffix,
                list(new[0].glyphSet())[0], forceChain=hasMarks)

        # GSUB lookup type 8: Reverse chaining substitution.
        if reverse:
            if len(old) != 1:
                raise FeatureLibError(
                    "In reverse chaining single substitutions, "
                    "only a single glyph or glyph class can be replaced",
                    location)
            if len(new) != 1:
                raise FeatureLibError(
                    'In reverse chaining single substitutions, '
                    'the replacement (after "by") must be a single glyph '
                    'or glyph class', location)
            if num_lookups != 0:
                raise FeatureLibError(
                    "Reverse chaining substitutions cannot call named lookups",
                    location)
            glyphs = sorted(list(old[0].glyphSet()))
            replacements = sorted(list(new[0].glyphSet()))
            if len(replacements) == 1:
                replacements = replacements * len(glyphs)
            if len(glyphs) != len(replacements):
                raise FeatureLibError(
                    'Expected a glyph class with %d elements after "by", '
                    'but found a glyph class with %d elements' %
                    (len(glyphs), len(replacements)), location)
            return ast.ReverseChainSingleSubstStatement(
                location, old_prefix, old_suffix,
                dict(zip(glyphs, replacements)))

        # GSUB lookup type 6: Chaining contextual substitution.
        assert len(new) == 0, new
        rule = ast.ChainContextSubstStatement(
            location, old_prefix, old, old_suffix, lookups)
        return rule

    def parse_subtable_(self):
        assert self.is_cur_keyword_("subtable")
        location = self.cur_token_location_
        self.expect_symbol_(";")
        return ast.SubtableStatement(location)

    def parse_table_(self):
        assert self.is_cur_keyword_("table")
        location, name = self.cur_token_location_, self.expect_tag_()
        table = ast.TableBlock(location, name)
        self.expect_symbol_("{")
        handler = {
            "GDEF": self.parse_table_GDEF_,
            "head": self.parse_table_head_,
            "name": self.parse_table_name_,
        }.get(name)
        if handler:
            handler(table)
        else:
            raise FeatureLibError('"table %s" is not supported' % name.strip(),
                                  location)
        self.expect_symbol_("}")
        end_tag = self.expect_tag_()
        if end_tag != name:
            raise FeatureLibError('Expected "%s"' % name.strip(),
                                  self.cur_token_location_)
        self.expect_symbol_(";")
        return table

    def parse_table_GDEF_(self, table):
        statements = table.statements
        while self.next_token_ != "}":
            self.advance_lexer_()
            if self.is_cur_keyword_("Attach"):
                statements.append(self.parse_attach_())
            elif self.is_cur_keyword_("GlyphClassDef"):
                statements.append(self.parse_GlyphClassDef_())
            elif self.is_cur_keyword_("LigatureCaretByIndex"):
                statements.append(self.parse_ligatureCaretByIndex_())
            elif self.is_cur_keyword_("LigatureCaretByPos"):
                statements.append(self.parse_ligatureCaretByPos_())
            else:
                raise FeatureLibError(
                    "Expected Attach, LigatureCaretByIndex, "
                    "or LigatureCaretByPos",
                    self.cur_token_location_)

    def parse_table_head_(self, table):
        statements = table.statements
        while self.next_token_ != "}":
            self.advance_lexer_()
            if self.is_cur_keyword_("FontRevision"):
                statements.append(self.parse_FontRevision_())
            else:
                raise FeatureLibError("Expected FontRevision",
                                      self.cur_token_location_)

    def parse_table_name_(self, table):
        statements = table.statements
        while self.next_token_ != "}":
            self.advance_lexer_()
            if self.is_cur_keyword_("nameid"):
                statement = self.parse_nameid_()
                if statement:
                    statements.append(statement)
            else:
                raise FeatureLibError("Expected nameid",
                                      self.cur_token_location_)

    def parse_nameid_(self):
        assert self.cur_token_ == "nameid", self.cur_token_
        location, nameID = self.cur_token_location_, self.expect_number_()
        if nameID > 255:
            raise FeatureLibError("Expected name id < 255",
                                  self.cur_token_location_)
        if 1 <= nameID <= 6:
            # TODO: issue a warning
            return None

        if self.next_token_type_ == Lexer.NUMBER:
            platformID = self.expect_number_()
            if platformID not in (1, 3):
                raise FeatureLibError("Expected platform id 1 or 3",
                                      self.cur_token_location_)
            if self.next_token_type_ == Lexer.NUMBER:
                platEncID = self.expect_number_()
                langID = self.expect_number_()
        else:
            platformID = 3

        if platformID == 1:   # Macintosh
            platEncID = 0     # Roman
            langID = 0        # English
        else:                 # 3, Windows
            platEncID = 1     # Unicode
            langID = 0x0409   # English

        string = self.expect_string_()
        self.expect_symbol_(";")

        if platformID == 1 and platEncID == 0:
            string = self.unescape_mac_name_string(string)
        elif platformID == 3 and platEncID == 1:
            string = self.unescape_windows_name_string(string)

        return ast.NameRecord(location, nameID, platformID,
                              platEncID, langID, string)

    def unescape_mac_name_string(self, string):
        def unescape(match):
            n = match.group(0)[1:]
            c = bytechr(int(n, 16)).decode('mac_roman')
            return c

        return re.sub(r'\\[0-9a-zAZ]{2}', unescape, string)

    def unescape_windows_name_string(self, string):
        def unescape(match):
            n = match.group(0)[1:]
            c = unichr(int(n, 16))
            return c

        return re.sub(r'\\[0-9a-zAZ]{4}', unescape, string)

    def parse_device_(self):
        result = None
        self.expect_symbol_("<")
        self.expect_keyword_("device")
        if self.next_token_ == "NULL":
            self.expect_keyword_("NULL")
        else:
            result = [(self.expect_number_(), self.expect_number_())]
            while self.next_token_ == ",":
                self.expect_symbol_(",")
                result.append((self.expect_number_(), self.expect_number_()))
            result = tuple(result)  # make it hashable
        self.expect_symbol_(">")
        return result

    def is_next_value_(self):
        return self.next_token_type_ is Lexer.NUMBER or self.next_token_ == "<"

    def parse_valuerecord_(self, vertical):
        if self.next_token_type_ is Lexer.NUMBER:
            number, location = self.expect_number_(), self.cur_token_location_
            if vertical:
                val = ast.ValueRecord(location, 0, 0, 0, number,
                                      None, None, None, None)
            else:
                val = ast.ValueRecord(location, 0, 0, number, 0,
                                      None, None, None, None)
            return val
        self.expect_symbol_("<")
        location = self.cur_token_location_
        if self.next_token_type_ is Lexer.NAME:
            name = self.expect_name_()
            if name == "NULL":
                self.expect_symbol_(">")
                return None
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

        if self.next_token_ == "<":
            xPlaDevice, yPlaDevice, xAdvDevice, yAdvDevice = (
                self.parse_device_(), self.parse_device_(),
                self.parse_device_(), self.parse_device_())
            allDeltas = sorted([
                delta
                for size, delta
                in (xPlaDevice if xPlaDevice else ()) +
                (yPlaDevice if yPlaDevice else ()) +
                (xAdvDevice if xAdvDevice else ()) +
                (yAdvDevice if yAdvDevice else ())])
            if allDeltas[0] < -128 or allDeltas[-1] > 127:
                raise FeatureLibError(
                    "Device value out of valid range (-128..127)",
                    self.cur_token_location_)
        else:
            xPlaDevice, yPlaDevice, xAdvDevice, yAdvDevice = (
                None, None, None, None)

        self.expect_symbol_(">")
        return ast.ValueRecord(
            location, xPlacement, yPlacement, xAdvance, yAdvance,
            xPlaDevice, yPlaDevice, xAdvDevice, yAdvDevice)

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
        vertical = (tag in {"vkrn", "vpal", "vhal", "valt"})

        use_extension = False
        if self.next_token_ == "useExtension":
            self.expect_keyword_("useExtension")
            use_extension = True

        block = ast.FeatureBlock(location, tag, use_extension)
        self.parse_block_(block, vertical)
        return block

    def parse_feature_reference_(self):
        assert self.cur_token_ == "feature", self.cur_token_
        location = self.cur_token_location_
        featureName = self.expect_tag_()
        self.expect_symbol_(";")
        return ast.FeatureReferenceStatement(location, featureName)

    def parse_FontRevision_(self):
        assert self.cur_token_ == "FontRevision", self.cur_token_
        location, version = self.cur_token_location_, self.expect_float_()
        self.expect_symbol_(";")
        if version <= 0:
            raise FeatureLibError("Font revision numbers must be positive",
                                  location)
        return ast.FontRevisionStatement(location, version)

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
            elif self.is_cur_keyword_({"enum", "enumerate"}):
                statements.append(self.parse_enumerate_(vertical=vertical))
            elif self.is_cur_keyword_("feature"):
                statements.append(self.parse_feature_reference_())
            elif self.is_cur_keyword_("ignore"):
                statements.append(self.parse_ignore_())
            elif self.is_cur_keyword_("language"):
                statements.append(self.parse_language_())
            elif self.is_cur_keyword_("lookup"):
                statements.append(self.parse_lookup_(vertical))
            elif self.is_cur_keyword_("lookupflag"):
                statements.append(self.parse_lookupflag_())
            elif self.is_cur_keyword_("markClass"):
                statements.append(self.parse_markClass_())
            elif self.is_cur_keyword_({"pos", "position"}):
                statements.append(
                    self.parse_position_(enumerated=False, vertical=vertical))
            elif self.is_cur_keyword_("script"):
                statements.append(self.parse_script_())
            elif (self.is_cur_keyword_({"sub", "substitute",
                                        "rsub", "reversesub"})):
                statements.append(self.parse_substitute_())
            elif self.is_cur_keyword_("subtable"):
                statements.append(self.parse_subtable_())
            elif self.is_cur_keyword_("valueRecordDef"):
                statements.append(self.parse_valuerecord_definition_(vertical))
            elif self.cur_token_ == ";":
                continue
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
        if self.cur_token_type_ is Lexer.NAME:
            if isinstance(k, type("")):  # basestring is gone in Python3
                return self.cur_token_ == k
            else:
                return self.cur_token_ in k
        return False

    def expect_class_name_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is not Lexer.GLYPHCLASS:
            raise FeatureLibError("Expected @NAME", self.cur_token_location_)
        return self.cur_token_

    def expect_cid_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.CID:
            return self.cur_token_
        raise FeatureLibError("Expected a CID", self.cur_token_location_)

    def expect_glyph_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.NAME:
            if len(self.cur_token_) > 63:
                raise FeatureLibError(
                    "Glyph names must not be longer than 63 characters",
                    self.cur_token_location_)
            return self.cur_token_
        elif self.cur_token_type_ is Lexer.CID:
            return "cid%05d" % self.cur_token_
        raise FeatureLibError("Expected a glyph name or CID",
                              self.cur_token_location_)

    def expect_markClass_reference_(self):
        name = self.expect_class_name_()
        mc = self.glyphclasses_.resolve(name)
        if mc is None:
            raise FeatureLibError("Unknown markClass @%s" % name,
                                  self.cur_token_location_)
        if not isinstance(mc, ast.MarkClass):
            raise FeatureLibError("@%s is not a markClass" % name,
                                  self.cur_token_location_)
        return mc

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

    def expect_float_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.FLOAT:
            return self.cur_token_
        raise FeatureLibError("Expected a floating-point number",
                              self.cur_token_location_)

    def expect_string_(self):
        self.advance_lexer_()
        if self.cur_token_type_ is Lexer.STRING:
            return self.cur_token_
        raise FeatureLibError("Expected a string", self.cur_token_location_)

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

    def make_cid_range_(self, location, start, limit):
        """(location, 999, 1001) --> {"cid00999", "cid01000", "cid01001"}"""
        result = set()
        if start > limit:
            raise FeatureLibError(
                "Bad range: start should be less than limit", location)
        for cid in range(start, limit + 1):
            result.add("cid%05d" % cid)
        return result

    def make_glyph_range_(self, location, start, limit):
        """(location, "a.sc", "d.sc") --> {"a.sc", "b.sc", "c.sc", "d.sc"}"""
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
