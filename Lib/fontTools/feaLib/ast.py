from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
import itertools


class Statement(object):
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


class AlternateSubstitution(Statement):
    def __init__(self, location, glyph, from_class):
        Statement.__init__(self, location)
        self.glyph, self.from_class = (glyph, from_class)

    def build(self, builder):
        builder.add_alternate_substitution(self.location, self.glyph,
                                           self.from_class)


class AnchorDefinition(Statement):
    def __init__(self, location, name, x, y, contourpoint):
        Statement.__init__(self, location)
        self.name, self.x, self.y, self.contourpoint = name, x, y, contourpoint


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


class MultipleSubstitution(Statement):
    def __init__(self, location, glyph, replacement):
        Statement.__init__(self, location)
        self.glyph, self.replacement = glyph, replacement

    def build(self, builder):
        builder.add_multiple_substitution(self.location, glyph, replacement)


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


class ValueRecord(Statement):
    def __init__(self, location, xPlacement, yPlacement, xAdvance, yAdvance):
        Statement.__init__(self, location)
        self.xPlacement, self.yPlacement = (xPlacement, yPlacement)
        self.xAdvance, self.yAdvance = (xAdvance, yAdvance)


class ValueRecordDefinition(Statement):
    def __init__(self, location, name, value):
        Statement.__init__(self, location)
        self.name = name
        self.value = value
