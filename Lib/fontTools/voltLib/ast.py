from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
import fontTools.feaLib.ast as ast
from fontTools.voltLib.error import VoltLibError


class VoltFile(ast.Block):
    def __init__(self):
        ast.Block.__init__(self, location=None)


class LookupBlock(ast.Block):
    def __init__(self, location, name):
        ast.Block.__init__(self, location)
        self.name = name

    def build(self, builder):
        builder.start_lookup_block(self.location, self.name)
        ast.Block.build(self, builder)
        builder.end_lookup_block()


class GlyphDefinition(ast.Statement):
    def __init__(self, location, name, gid, gunicode, gtype, components):
        ast.Statement.__init__(self, location)
        self.name = name
        self.id = gid
        self.unicode = gunicode
        self.type = gtype
        self.components = components


class GroupDefinition(ast.Statement):
    def __init__(self, location, name, enum):
        ast.Statement.__init__(self, location)
        self.name = name
        self.enum = enum
        self.glyphs_ = None

    def glyphSet(self, groups=None):
        if groups is not None and self.name in groups:
            raise VoltLibError(
                'Group "%s" contains itself.' % (self.name),
                self.location)
        if self.glyphs_ is None:
            if groups is None:
                groups = set({self.name})
            else:
                groups.add(self.name)
            self.glyphs_ = self.enum.glyphSet(groups)
        return self.glyphs_


class GlyphName(ast.Expression):
    """A single glyph name, such as cedilla."""
    def __init__(self, location, glyph):
        ast.Expression.__init__(self, location)
        self.glyph = glyph

    def glyphSet(self):
        return frozenset((self.glyph,))


class Enum(ast.Expression):
    """An enum"""
    def __init__(self, location, enum):
        ast.Expression.__init__(self, location)
        self.enum = enum

    def __iter__(self):
        for e in self.glyphSet():
            yield e

    def glyphSet(self, groups=None):
        glyphs = set()
        for element in self.enum:
            if isinstance(element, (GroupName, Enum)):
                glyphs = glyphs.union(element.glyphSet(groups))
            else:
                glyphs = glyphs.union(element.glyphSet())
        return frozenset(glyphs)


class GroupName(ast.Expression):
    """A glyph group"""
    def __init__(self, location, group, parser):
        ast.Expression.__init__(self, location)
        self.group = group
        self.parser_ = parser

    def glyphSet(self, groups=None):
        group = self.parser_.resolve_group(self.group)
        if group is not None:
            self.glyphs_ = group.glyphSet(groups)
            return self.glyphs_
        else:
            raise VoltLibError(
                'Group "%s" is used but undefined.' % (self.group),
                self.location)


class Range(ast.Expression):
    """A glyph range"""
    def __init__(self, location, start, end, parser):
        ast.Expression.__init__(self, location)
        self.start = start
        self.end = end
        self.parser = parser

    def glyphSet(self):
        glyphs = self.parser.glyph_range(self.start, self.end)
        return frozenset(glyphs)


class ScriptDefinition(ast.Statement):
    def __init__(self, location, name, tag, langs):
        ast.Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.langs = langs


class LangSysDefinition(ast.Statement):
    def __init__(self, location, name, tag, features):
        ast.Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.features = features


class FeatureDefinition(ast.Statement):
    def __init__(self, location, name, tag, lookups):
        ast.Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.lookups = lookups


class LookupDefinition(ast.Statement):
    def __init__(self, location, name, process_base, process_marks, direction,
                 reversal, comments, context, sub, pos):
        ast.Statement.__init__(self, location)
        self.name = name
        self.process_base = process_base
        self.process_marks = process_marks
        self.direction = direction
        self.reversal = reversal
        self.comments = comments
        self.context = context
        self.sub = sub
        self.pos = pos


class SubstitutionDefinition(ast.Statement):
    def __init__(self, location, mapping):
        ast.Statement.__init__(self, location)
        self.mapping = mapping


class SubstitutionSingleDefinition(SubstitutionDefinition):
    def __init__(self, location, mapping):
        SubstitutionDefinition.__init__(self, location, mapping)


class SubstitutionMultipleDefinition(SubstitutionDefinition):
    def __init__(self, location, mapping):
        SubstitutionDefinition.__init__(self, location, mapping)


class SubstitutionLigatureDefinition(SubstitutionDefinition):
    def __init__(self, location, mapping):
        SubstitutionDefinition.__init__(self, location, mapping)


class SubstitutionReverseChainingSingleDefinition(SubstitutionDefinition):
    def __init__(self, location, mapping):
        SubstitutionDefinition.__init__(self, location, mapping)


class PositionAttachDefinition(ast.Statement):
    def __init__(self, location, coverage, coverage_to):
        ast.Statement.__init__(self, location)
        self.coverage = coverage
        self.coverage_to = coverage_to


class PositionAttachCursiveDefinition(ast.Statement):
    def __init__(self, location, coverages_exit, coverages_enter):
        ast.Statement.__init__(self, location)
        self.coverages_exit = coverages_exit
        self.coverages_enter = coverages_enter


class PositionAdjustPairDefinition(ast.Statement):
    def __init__(self, location, coverages_1, coverages_2, adjust_pair):
        ast.Statement.__init__(self, location)
        self.coverages_1 = coverages_1
        self.coverages_2 = coverages_2
        self.adjust_pair = adjust_pair


class PositionAdjustSingleDefinition(ast.Statement):
    def __init__(self, location, adjust_single):
        ast.Statement.__init__(self, location)
        self.adjust_single = adjust_single


class ContextDefinition(ast.Statement):
    def __init__(self, location, ex_or_in, left=[], right=[]):
        ast.Statement.__init__(self, location)
        self.ex_or_in = ex_or_in
        self.left = left
        self.right = right


class AnchorDefinition(ast.Statement):
    def __init__(self, location, name, gid, glyph_name, component, locked,
                 pos):
        ast.Statement.__init__(self, location)
        self.name = name
        self.gid = gid
        self.glyph_name = glyph_name
        self.component = component
        self.locked = locked
        self.pos = pos


class SettingDefinition(ast.Statement):
    def __init__(self, location, name, value):
        ast.Statement.__init__(self, location)
        self.name = name
        self.value = value
