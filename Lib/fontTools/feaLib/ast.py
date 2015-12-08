from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
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
        self.markClasses = {}  # name --> ast.MarkClassDefinition


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


class MarkClassDefinition(object):
    def __init__(self, location, name):
        self.location, self.name = location, name
        self.anchors = {}  # glyph --> ast.Anchor
        self.glyphLocations = {}  # glyph --> (filepath, line, column)


class AlternateSubstitution(Statement):
    def __init__(self, location, glyph, from_class):
        Statement.__init__(self, location)
        self.glyph, self.from_class = (glyph, from_class)

    def build(self, builder):
        builder.add_alternate_substitution(self.location, self.glyph,
                                           self.from_class)


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


class CursiveAttachmentPositioning(Statement):
    def __init__(self, location, glyphclass, entryAnchor, exitAnchor):
        Statement.__init__(self, location)
        self.glyphclass = glyphclass
        self.entryAnchor, self.exitAnchor = entryAnchor, exitAnchor

    def build(self, builder):
        builder.add_cursive_attachment_pos(
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


class LigatureSubstitution(Statement):
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
            builder.add_ligature_substitution(
                self.location, glyphs, self.replacement)


class LookupReferenceStatement(Statement):
    def __init__(self, location, lookup):
        Statement.__init__(self, location)
        self.location, self.lookup = (location, lookup)

    def build(self, builder):
        for s in self.lookup.statements:
            s.build(builder)


class MarkToBaseAttachmentPositioning(Statement):
    def __init__(self, location, base, marks):
        Statement.__init__(self, location)
        self.base, self.marks = base, marks

    def build(self, builder):
        builder.add_mark_to_base_attachment_pos(
            self.location, self.base, self.marks)


class MultipleSubstitution(Statement):
    def __init__(self, location, glyph, replacement):
        Statement.__init__(self, location)
        self.glyph, self.replacement = glyph, replacement

    def build(self, builder):
        builder.add_multiple_substitution(self.location,
                                          self.glyph, self.replacement)


class PairAdjustmentPositioning(Statement):
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


class ReverseChainingSingleSubstitution(Statement):
    def __init__(self, location, old_prefix, old_suffix, mapping):
        Statement.__init__(self, location)
        self.old_prefix, self.old_suffix = old_prefix, old_suffix
        self.mapping = mapping

    def build(self, builder):
        builder.add_reverse_chaining_single_substitution(
            self.location, self.old_prefix, self.old_suffix, self.mapping)


class SingleSubstitution(Statement):
    def __init__(self, location, mapping):
        Statement.__init__(self, location)
        self.mapping = mapping

    def build(self, builder):
        builder.add_single_substitution(self.location, self.mapping)


class ScriptStatement(Statement):
    def __init__(self, location, script):
        Statement.__init__(self, location)
        self.script = script

    def build(self, builder):
        builder.set_script(self.location, self.script)


class SingleAdjustmentPositioning(Statement):
    def __init__(self, location, glyphclass, valuerecord):
        Statement.__init__(self, location)
        self.glyphclass, self.valuerecord = glyphclass, valuerecord

    def build(self, builder):
        for glyph in self.glyphclass:
            builder.add_single_pos(self.location, glyph, self.valuerecord)


class SubtableStatement(Statement):
    def __init__(self, location):
        Statement.__init__(self, location)


class SubstitutionRule(Statement):
    def __init__(self, location, old, new):
        Statement.__init__(self, location)
        self.old, self.new = (old, new)
        self.old_prefix = []
        self.old_suffix = []
        self.lookups = [None] * len(old)

    def build(self, builder):
        builder.add_substitution(
            self.location, self.old_prefix, self.old, self.old_suffix,
            self.new, self.lookups)


class ValueRecord(Statement):
    def __init__(self, location, xPlacement, yPlacement, xAdvance, yAdvance,
                 xPlaDevice, yPlaDevice, xAdvDevice, yAdvDevice):
        Statement.__init__(self, location)
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
