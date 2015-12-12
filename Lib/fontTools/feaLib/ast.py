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


class GlyphClassDefinition(Statement):
    def __init__(self, location, name, glyphs):
        Statement.__init__(self, location)
        self.name = name
        self.glyphs = glyphs

    def glyphSet(self):
        return frozenset(self.glyphs)


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
                assert FeatureLibError(
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
    def __init__(self, location, glyph, from_class):
        Statement.__init__(self, location)
        self.glyph, self.from_class = (glyph, from_class)

    def build(self, builder):
        builder.add_alternate_subst(self.location, self.glyph, self.from_class)


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


class ChainContextPosStatement(Statement):
    def __init__(self, location, prefix, glyphs, suffix, lookups):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = prefix, glyphs, suffix
        self.lookups = lookups

    def build(self, builder):
        builder.add_chain_context_pos(
            self.location, self.prefix, self.glyphs, self.suffix, self.lookups)


class ChainContextSubstStatement(Statement):
    def __init__(self, location, old_prefix, old, old_suffix, lookups):
        Statement.__init__(self, location)
        self.old, self.lookups = old, lookups
        self.old_prefix, self.old_suffix = old_prefix, old_suffix

    def build(self, builder):
        builder.add_chain_context_subst(
            self.location, self.old_prefix, self.old, self.old_suffix,
            self.lookups)


class CursivePosStatement(Statement):
    def __init__(self, location, glyphclass, entryAnchor, exitAnchor):
        Statement.__init__(self, location)
        self.glyphclass = glyphclass
        self.entryAnchor, self.exitAnchor = entryAnchor, exitAnchor

    def build(self, builder):
        builder.add_cursive_pos(
            self.location, self.glyphclass, self.entryAnchor, self.exitAnchor)


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


class IgnoreSubstitutionRule(Statement):
    def __init__(self, location, prefix, glyphs, suffix):
        Statement.__init__(self, location)
        self.prefix, self.glyphs, self.suffix = (prefix, glyphs, suffix)


class LigatureSubstStatement(Statement):
    def __init__(self, location, glyphs, replacement):
        Statement.__init__(self, location)
        self.glyphs, self.replacement = (glyphs, replacement)

    def build(self, builder):
        # OpenType feature file syntax, section 5.d, "Ligature substitution":
        # "Since the OpenType specification does not allow ligature
        # substitutions to be specified on target sequences that contain
        # glyph classes, the implementation software will enumerate
        # all specific glyph sequences if glyph classes are detected"
        for glyphs in sorted(itertools.product(*self.glyphs)):
            builder.add_ligature_subst(self.location, glyphs, self.replacement)


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
        for s in self.lookup.statements:
            s.build(builder)


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
        pass


class MultipleSubstStatement(Statement):
    def __init__(self, location, glyph, replacement):
        Statement.__init__(self, location)
        self.glyph, self.replacement = glyph, replacement

    def build(self, builder):
        builder.add_multiple_subst(self.location, self.glyph, self.replacement)


class PairPosStatement(Statement):
    def __init__(self, location, enumerated,
                 glyphclass1, valuerecord1, glyphclass2, valuerecord2):
        Statement.__init__(self, location)
        self.enumerated = enumerated
        self.glyphclass1, self.valuerecord1 = glyphclass1, valuerecord1
        self.glyphclass2, self.valuerecord2 = glyphclass2, valuerecord2

    def build(self, builder):
        builder.add_pair_pos(self.location, self.enumerated,
                             self.glyphclass1, self.valuerecord1,
                             self.glyphclass2, self.valuerecord2)


class ReverseChainSingleSubstStatement(Statement):
    def __init__(self, location, old_prefix, old_suffix, mapping):
        Statement.__init__(self, location)
        self.old_prefix, self.old_suffix = old_prefix, old_suffix
        self.mapping = mapping

    def build(self, builder):
        builder.add_reverse_chain_single_subst(
            self.location, self.old_prefix, self.old_suffix, self.mapping)


class SingleSubstStatement(Statement):
    def __init__(self, location, mapping):
        Statement.__init__(self, location)
        self.mapping = mapping

    def build(self, builder):
        builder.add_single_subst(self.location, self.mapping)


class ScriptStatement(Statement):
    def __init__(self, location, script):
        Statement.__init__(self, location)
        self.script = script

    def build(self, builder):
        builder.set_script(self.location, self.script)


class SinglePosStatement(Statement):
    def __init__(self, location, glyphclass, valuerecord):
        Statement.__init__(self, location)
        self.glyphclass, self.valuerecord = glyphclass, valuerecord

    def build(self, builder):
        for glyph in self.glyphclass:
            builder.add_single_pos(self.location, glyph, self.valuerecord)


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
