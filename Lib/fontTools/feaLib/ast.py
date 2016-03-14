from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
import itertools


def deviceToString(device):
    if device is None:
        return "<device NULL>"
    else:
        return "<device %s>" % ", ".join(["%d %d" % t for t in device])


class Statement(object):
    def __init__(self, location):
        self.location = location

    def build(self, builder):
        pass


class Expression(object):
    def __init__(self, location):
        self.location = location

    def build(self, builder):
        pass


class GlyphName(Expression):
    """A single glyph name, such as cedilla."""
    def __init__(self, location, glyph):
        Expression.__init__(self, location)
        self.glyph = glyph

    def glyphSet(self):
        return frozenset((self.glyph,))


class GlyphClass(Expression):
    """A glyph class, such as [acute cedilla grave]."""
    def __init__(self, location, glyphs):
        Expression.__init__(self, location)
        self.glyphs = glyphs

    def glyphSet(self):
        return frozenset(self.glyphs)


class GlyphClassName(Expression):
    """A glyph class name, such as @FRENCH_MARKS."""
    def __init__(self, location, glyphclass):
        Expression.__init__(self, location)
        assert isinstance(glyphclass, GlyphClassDefinition)
        self.glyphclass = glyphclass

    def glyphSet(self):
        return frozenset(self.glyphclass.glyphs)


class MarkClassName(Expression):
    """A mark class name, such as @FRENCH_MARKS defined with markClass."""
    def __init__(self, location, markClass):
        Expression.__init__(self, location)
        assert isinstance(markClass, MarkClass)
        self.markClass = markClass

    def glyphSet(self):
        return self.markClass.glyphSet()


class Block(Statement):
    def __init__(self, location):
        Statement.__init__(self, location)
        self.statements = []

    def build(self, builder):
        for s in self.statements:
            s.build(builder)


class FeatureFile(Block):
    def __init__(self):
        Block.__init__(self, location=None)
        self.markClasses = {}  # name --> ast.MarkClass


class FeatureBlock(Block):
    def __init__(self, location, name, use_extension):
        Block.__init__(self, location)
        self.name, self.use_extension = name, use_extension

    def build(self, builder):
        # TODO(sascha): Handle use_extension.
        builder.start_feature(self.location, self.name)
        Block.build(self, builder)
        builder.end_feature()


class LookupBlock(Block):
    def __init__(self, location, name, use_extension):
        Block.__init__(self, location)
        self.name, self.use_extension = name, use_extension

    def build(self, builder):
        # TODO(sascha): Handle use_extension.
        builder.start_lookup_block(self.location, self.name)
        Block.build(self, builder)
        builder.end_lookup_block()


class TableBlock(Block):
    def __init__(self, location, name):
        Block.__init__(self, location)
        self.name = name


class GlyphClassDefinition(Statement):
    """Example: @UPPERCASE = [A-Z];"""
    def __init__(self, location, name, glyphs):
        Statement.__init__(self, location)
        self.name = name
        self.glyphs = glyphs

    def glyphSet(self):
        return frozenset(self.glyphs)


class GlyphClassDefStatement(Statement):
    """Example: GlyphClassDef @UPPERCASE, [B], [C], [D];"""
    def __init__(self, location, baseGlyphs, markGlyphs,
                 ligatureGlyphs, componentGlyphs):
        Statement.__init__(self, location)
        self.baseGlyphs, self.markGlyphs = (baseGlyphs, markGlyphs)
        self.ligatureGlyphs = ligatureGlyphs
        self.componentGlyphs = componentGlyphs

    def build(self, builder):
        base = self.baseGlyphs.glyphSet() if self.baseGlyphs else set()
        liga = self.ligatureGlyphs.glyphSet() if self.ligatureGlyphs else set()
        mark = self.markGlyphs.glyphSet() if self.markGlyphs else set()
        comp = (self.componentGlyphs.glyphSet()
                if self.componentGlyphs else set())
        builder.add_glyphClassDef(self.location, base, liga, mark, comp)


# While glyph classes can be defined only once, the feature file format
# allows expanding mark classes with multiple definitions, each using
# different glyphs and anchors. The following are two MarkClassDefinitions
# for the same MarkClass:
#     markClass [acute grave] <anchor 350 800> @FRENCH_ACCENTS;
#     markClass [cedilla] <anchor 350 -200> @FRENCH_ACCENTS;
class MarkClass(object):
    def __init__(self, name):
        self.name = name
        self.definitions = []
        self.glyphs = {}  # glyph --> ast.MarkClassDefinitions

    def addDefinition(self, definition):
        assert isinstance(definition, MarkClassDefinition)
        self.definitions.append(definition)
        for glyph in definition.glyphSet():
            if glyph in self.definitions:
                otherLoc = self.definitions[glyph].location
                raise FeatureLibError(
                    "Glyph %s already defined at %s:%d:%d" % (
                        glyph, otherLoc[0], otherLoc[1], otherLoc[2]),
                    definition.location)
            self.glyphs[glyph] = definition

    def glyphSet(self):
        return frozenset(self.glyphs.keys())


class MarkClassDefinition(Statement):
    def __init__(self, location, markClass, anchor, glyphs):
        Statement.__init__(self, location)
        assert isinstance(markClass, MarkClass)
        assert isinstance(anchor, Anchor) and isinstance(glyphs, Expression)
        self.markClass, self.anchor, self.glyphs = markClass, anchor, glyphs

    def glyphSet(self):
        return self.glyphs.glyphSet()


class AlternateSubstStatement(Statement):
    def __init__(self, location, prefix, glyph, suffix, replacement):
        Statement.__init__(self, location)
        self.prefix, self.glyph, self.suffix = (prefix, glyph, suffix)
        self.replacement = replacement

    def build(self, builder):
        glyph = self.glyph.glyphSet()
        assert len(glyph) == 1, glyph
        glyph = list(glyph)[0]
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        replacement = self.replacement.glyphSet()
        builder.add_alternate_subst(self.location, prefix, glyph, suffix,
                                    replacement)


class Anchor(Expression):
    def __init__(self, location, x, y, contourpoint,
                 xDeviceTable, yDeviceTable):
        Expression.__init__(self, location)
        self.x, self.y, self.contourpoint = x, y, contourpoint
        self.xDeviceTable, self.yDeviceTable = xDeviceTable, yDeviceTable


class AnchorDefinition(Statement):
    def __init__(self, location, name, x, y, contourpoint):
        Statement.__init__(self, location)
        self.name, self.x, self.y, self.contourpoint = name, x, y, contourpoint


class AttachStatement(Statement):
    def __init__(self, location, glyphs, contourPoints):
        Statement.__init__(self, location)
        self.glyphs, self.contourPoints = (glyphs, contourPoints)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_attach_points(self.location, glyphs, self.contourPoints)


class ChainContextPosStatement(Statement):
    def __init__(self, location, prefix, glyphs, suffix, lookups):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = prefix, glyphs, suffix
        self.lookups = lookups

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_chain_context_pos(
            self.location, prefix, glyphs, suffix, self.lookups)


class ChainContextSubstStatement(Statement):
    def __init__(self, location, prefix, glyphs, suffix, lookups):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = prefix, glyphs, suffix
        self.lookups = lookups

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_chain_context_subst(
            self.location, prefix, glyphs, suffix, self.lookups)


class CursivePosStatement(Statement):
    def __init__(self, location, glyphclass, entryAnchor, exitAnchor):
        Statement.__init__(self, location)
        self.glyphclass = glyphclass
        self.entryAnchor, self.exitAnchor = entryAnchor, exitAnchor

    def build(self, builder):
        builder.add_cursive_pos(
            self.location, self.glyphclass, self.entryAnchor, self.exitAnchor)


class FeatureReferenceStatement(Statement):
    """Example: feature salt;"""
    def __init__(self, location, featureName):
        Statement.__init__(self, location)
        self.location, self.featureName = (location, featureName)

    def build(self, builder):
        builder.add_feature_reference(self.location, self.featureName)


class IgnorePosStatement(Statement):
    def __init__(self, location, chainContexts):
        Statement.__init__(self, location)
        self.chainContexts = chainContexts

    def build(self, builder):
        for prefix, glyphs, suffix in self.chainContexts:
            prefix = [p.glyphSet() for p in prefix]
            glyphs = [g.glyphSet() for g in glyphs]
            suffix = [s.glyphSet() for s in suffix]
            builder.add_chain_context_pos(
                self.location, prefix, glyphs, suffix, [])


class IgnoreSubstStatement(Statement):
    def __init__(self, location, chainContexts):
        Statement.__init__(self, location)
        self.chainContexts = chainContexts

    def build(self, builder):
        for prefix, glyphs, suffix in self.chainContexts:
            prefix = [p.glyphSet() for p in prefix]
            glyphs = [g.glyphSet() for g in glyphs]
            suffix = [s.glyphSet() for s in suffix]
            builder.add_chain_context_subst(
                self.location, prefix, glyphs, suffix, [])


class LanguageStatement(Statement):
    def __init__(self, location, language, include_default, required):
        Statement.__init__(self, location)
        assert(len(language) == 4)
        self.language = language
        self.include_default = include_default
        self.required = required

    def build(self, builder):
        builder.set_language(location=self.location, language=self.language,
                             include_default=self.include_default,
                             required=self.required)


class LanguageSystemStatement(Statement):
    def __init__(self, location, script, language):
        Statement.__init__(self, location)
        self.script, self.language = (script, language)

    def build(self, builder):
        builder.add_language_system(self.location, self.script, self.language)


class FontRevisionStatement(Statement):
    def __init__(self, location, revision):
        Statement.__init__(self, location)
        self.revision = revision

    def build(self, builder):
        builder.set_font_revision(self.location, self.revision)


class LigatureCaretByIndexStatement(Statement):
    def __init__(self, location, glyphs, carets):
        Statement.__init__(self, location)
        self.glyphs, self.carets = (glyphs, carets)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_ligatureCaretByIndex_(self.location, glyphs, self.carets)


class LigatureCaretByPosStatement(Statement):
    def __init__(self, location, glyphs, carets):
        Statement.__init__(self, location)
        self.glyphs, self.carets = (glyphs, carets)

    def build(self, builder):
        glyphs = self.glyphs.glyphSet()
        builder.add_ligatureCaretByPos_(self.location, glyphs, self.carets)


class LigatureSubstStatement(Statement):
    def __init__(self, location, prefix, glyphs, suffix, replacement,
                 forceChain):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = (prefix, glyphs, suffix)
        self.replacement, self.forceChain = replacement, forceChain

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        glyphs = [g.glyphSet() for g in self.glyphs]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_ligature_subst(
            self.location, prefix, glyphs, suffix, self.replacement,
            self.forceChain)


class LookupFlagStatement(Statement):
    def __init__(self, location, value, markAttachment, markFilteringSet):
        Statement.__init__(self, location)
        self.value = value
        self.markAttachment = markAttachment
        self.markFilteringSet = markFilteringSet

    def build(self, builder):
        markAttach = None
        if self.markAttachment is not None:
            markAttach = self.markAttachment.glyphSet()
        markFilter = None
        if self.markFilteringSet is not None:
            markFilter = self.markFilteringSet.glyphSet()
        builder.set_lookup_flag(self.location, self.value,
                                markAttach, markFilter)


class LookupReferenceStatement(Statement):
    def __init__(self, location, lookup):
        Statement.__init__(self, location)
        self.location, self.lookup = (location, lookup)

    def build(self, builder):
        builder.add_lookup_call(self.lookup.name)


class MarkBasePosStatement(Statement):
    def __init__(self, location, base, marks):
        Statement.__init__(self, location)
        self.base, self.marks = base, marks

    def build(self, builder):
        builder.add_mark_base_pos(self.location, self.base, self.marks)


class MarkLigPosStatement(Statement):
    def __init__(self, location, ligatures, marks):
        Statement.__init__(self, location)
        self.ligatures, self.marks = ligatures, marks

    def build(self, builder):
        builder.add_mark_lig_pos(self.location, self.ligatures, self.marks)


class MarkMarkPosStatement(Statement):
    def __init__(self, location, baseMarks, marks):
        Statement.__init__(self, location)
        self.baseMarks, self.marks = baseMarks, marks

    def build(self, builder):
        builder.add_mark_mark_pos(self.location, self.baseMarks, self.marks)


class MultipleSubstStatement(Statement):
    def __init__(self, location, prefix, glyph, suffix, replacement):
        Statement.__init__(self, location)
        self.prefix, self.glyph, self.suffix = prefix, glyph, suffix
        self.replacement = replacement

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_multiple_subst(
            self.location, prefix, self.glyph, suffix, self.replacement)


class PairPosStatement(Statement):
    def __init__(self, location, enumerated,
                 glyphs1, valuerecord1, glyphs2, valuerecord2):
        Statement.__init__(self, location)
        self.enumerated = enumerated
        self.glyphs1, self.valuerecord1 = glyphs1, valuerecord1
        self.glyphs2, self.valuerecord2 = glyphs2, valuerecord2

    def build(self, builder):
        if self.enumerated:
            g = [self.glyphs1.glyphSet(), self.glyphs2.glyphSet()]
            for glyph1, glyph2 in itertools.product(*g):
                builder.add_specific_pair_pos(
                    self.location, glyph1, self.valuerecord1,
                    glyph2, self.valuerecord2)
            return

        is_specific = (isinstance(self.glyphs1, GlyphName) and
                       isinstance(self.glyphs2, GlyphName))
        if is_specific:
            builder.add_specific_pair_pos(
                self.location, self.glyphs1.glyph, self.valuerecord1,
                self.glyphs2.glyph, self.valuerecord2)
        else:
            builder.add_class_pair_pos(
                self.location, self.glyphs1.glyphSet(), self.valuerecord1,
                self.glyphs2.glyphSet(), self.valuerecord2)


class ReverseChainSingleSubstStatement(Statement):
    def __init__(self, location, old_prefix, old_suffix, mapping):
        Statement.__init__(self, location)
        self.old_prefix, self.old_suffix = old_prefix, old_suffix
        self.mapping = mapping

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.old_prefix]
        suffix = [s.glyphSet() for s in self.old_suffix]
        builder.add_reverse_chain_single_subst(
            self.location, prefix, suffix, self.mapping)


class SingleSubstStatement(Statement):
    def __init__(self, location, mapping, prefix, suffix, forceChain):
        Statement.__init__(self, location)
        self.mapping, self.prefix, self.suffix = mapping, prefix, suffix
        self.forceChain = forceChain

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        builder.add_single_subst(self.location, prefix, suffix, self.mapping,
                                 self.forceChain)


class ScriptStatement(Statement):
    def __init__(self, location, script):
        Statement.__init__(self, location)
        self.script = script

    def build(self, builder):
        builder.set_script(self.location, self.script)


class SinglePosStatement(Statement):
    def __init__(self, location, pos, prefix, suffix, forceChain):
        Statement.__init__(self, location)
        self.pos, self.prefix, self.suffix = pos, prefix, suffix
        self.forceChain = forceChain

    def build(self, builder):
        prefix = [p.glyphSet() for p in self.prefix]
        suffix = [s.glyphSet() for s in self.suffix]
        pos = [(g.glyphSet(), value) for g, value in self.pos]
        builder.add_single_pos(self.location, prefix, suffix,
                               pos, self.forceChain)


class SubtableStatement(Statement):
    def __init__(self, location):
        Statement.__init__(self, location)


class ValueRecord(Expression):
    def __init__(self, location, xPlacement, yPlacement, xAdvance, yAdvance,
                 xPlaDevice, yPlaDevice, xAdvDevice, yAdvDevice):
        Expression.__init__(self, location)
        self.xPlacement, self.yPlacement = (xPlacement, yPlacement)
        self.xAdvance, self.yAdvance = (xAdvance, yAdvance)
        self.xPlaDevice, self.yPlaDevice = (xPlaDevice, yPlaDevice)
        self.xAdvDevice, self.yAdvDevice = (xAdvDevice, yAdvDevice)

    def __eq__(self, other):
        return (self.xPlacement == other.xPlacement and
                self.yPlacement == other.yPlacement and
                self.xAdvance == other.xAdvance and
                self.yAdvance == other.yAdvance and
                self.xPlaDevice == other.xPlaDevice and
                self.xAdvDevice == other.xAdvDevice)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return (hash(self.xPlacement) ^ hash(self.yPlacement) ^
                hash(self.xAdvance) ^ hash(self.yAdvance) ^
                hash(self.xPlaDevice) ^ hash(self.yPlaDevice) ^
                hash(self.xAdvDevice) ^ hash(self.yAdvDevice))

    def makeString(self, vertical):
        x, y = self.xPlacement, self.yPlacement
        xAdvance, yAdvance = self.xAdvance, self.yAdvance
        xPlaDevice, yPlaDevice = self.xPlaDevice, self.yPlaDevice
        xAdvDevice, yAdvDevice = self.xAdvDevice, self.yAdvDevice

        # Try format A, if possible.
        if x == 0 and y == 0:
            if xAdvance == 0 and vertical:
                return str(yAdvance)
            elif yAdvance == 0 and not vertical:
                return str(xAdvance)

        # Try format B, if possible.
        if (xPlaDevice is None and yPlaDevice is None and
                xAdvDevice is None and yAdvDevice is None):
            return "<%s %s %s %s>" % (x, y, xAdvance, yAdvance)

        # Last resort is format C.
        return "<%s %s %s %s %s %s %s %s %s %s>" % (
            x, y, xAdvance, yAdvance,
            deviceToString(xPlaDevice), deviceToString(yPlaDevice),
            deviceToString(xAdvDevice), deviceToString(yAdvDevice))


class ValueRecordDefinition(Statement):
    def __init__(self, location, name, value):
        Statement.__init__(self, location)
        self.name = name
        self.value = value


class NameRecord(Statement):
    def __init__(self, location, nameID, platformID,
                 platEncID, langID, string):
        Statement.__init__(self, location)
        self.nameID = nameID
        self.platformID = platformID
        self.platEncID = platEncID
        self.langID = langID
        self.string = string

    def build(self, builder):
        builder.add_name_record(
            self.location, self.nameID, self.platformID,
            self.platEncID, self.langID, self.string)
