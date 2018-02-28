from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.voltLib.error import VoltLibError


class Statement(object):
    def __init__(self, location=None):
        self.location = location

    def build(self, builder):
        pass


class Expression(object):
    def __init__(self, location=None):
        self.location = location

    def build(self, builder):
        pass


class Block(Statement):
    def __init__(self, location=None):
        Statement.__init__(self, location)
        self.statements = []

    def build(self, builder):
        for s in self.statements:
            s.build(builder)


class VoltFile(Block):
    def __init__(self):
        Block.__init__(self, location=None)


class LookupBlock(Block):
    def __init__(self, name, location=None):
        Block.__init__(self, location)
        self.name = name

    def build(self, builder):
        builder.start_lookup_block(self.location, self.name)
        Block.build(self, builder)
        builder.end_lookup_block()


class GlyphDefinition(Statement):
    def __init__(self, name, gid, gunicode, gtype, components, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.id = gid
        self.unicode = gunicode
        self.type = gtype
        self.components = components


class GroupDefinition(Statement):
    def __init__(self, name, enum, location=None):
        Statement.__init__(self, location)
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


class GlyphName(Expression):
    """A single glyph name, such as cedilla."""
    def __init__(self, glyph, location=None):
        Expression.__init__(self, location)
        self.glyph = glyph

    def glyphSet(self):
        return frozenset((self.glyph,))


class Enum(Expression):
    """An enum"""
    def __init__(self, enum, location=None):
        Expression.__init__(self, location)
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


class GroupName(Expression):
    """A glyph group"""
    def __init__(self, group, parser, location=None):
        Expression.__init__(self, location)
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


class Range(Expression):
    """A glyph range"""
    def __init__(self, start, end, parser, location=None):
        Expression.__init__(self, location)
        self.start = start
        self.end = end
        self.parser = parser

    def glyphSet(self):
        glyphs = self.parser.glyph_range(self.start, self.end)
        return frozenset(glyphs)


class ScriptDefinition(Statement):
    def __init__(self, name, tag, langs, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.langs = langs


class LangSysDefinition(Statement):
    def __init__(self, name, tag, features, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.features = features


class FeatureDefinition(Statement):
    def __init__(self, name, tag, lookups, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.tag = tag
        self.lookups = lookups


class LookupDefinition(Statement):
    def __init__(self, name, process_base, process_marks, direction,
                 reversal, comments, context, sub, pos, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.process_base = process_base
        self.process_marks = process_marks
        self.direction = direction
        self.reversal = reversal
        self.comments = comments
        self.context = context
        self.sub = sub
        self.pos = pos


class SubstitutionDefinition(Statement):
    def __init__(self, mapping, location=None):
        Statement.__init__(self, location)
        self.mapping = mapping


class SubstitutionSingleDefinition(SubstitutionDefinition):
    pass


class SubstitutionMultipleDefinition(SubstitutionDefinition):
    pass


class SubstitutionLigatureDefinition(SubstitutionDefinition):
    pass


class SubstitutionReverseChainingSingleDefinition(SubstitutionDefinition):
    pass


class PositionAttachDefinition(Statement):
    def __init__(self, coverage, coverage_to, location=None):
        Statement.__init__(self, location)
        self.coverage = coverage
        self.coverage_to = coverage_to


class PositionAttachCursiveDefinition(Statement):
    def __init__(self, coverages_exit, coverages_enter, location=None):
        Statement.__init__(self, location)
        self.coverages_exit = coverages_exit
        self.coverages_enter = coverages_enter


class PositionAdjustPairDefinition(Statement):
    def __init__(self, coverages_1, coverages_2, adjust_pair, location=None):
        Statement.__init__(self, location)
        self.coverages_1 = coverages_1
        self.coverages_2 = coverages_2
        self.adjust_pair = adjust_pair


class PositionAdjustSingleDefinition(Statement):
    def __init__(self, adjust_single, location=None):
        Statement.__init__(self, location)
        self.adjust_single = adjust_single


class ContextDefinition(Statement):
    def __init__(self, ex_or_in, left=None, right=None, location=None):
        Statement.__init__(self, location)
        self.ex_or_in = ex_or_in
        self.left = left if left is not None else []
        self.right = right if right is not None else []


class AnchorDefinition(Statement):
    def __init__(self, name, gid, glyph_name, component, locked,
                 pos, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.gid = gid
        self.glyph_name = glyph_name
        self.component = component
        self.locked = locked
        self.pos = pos


class SettingDefinition(Statement):
    def __init__(self, name, value, location=None):
        Statement.__init__(self, location)
        self.name = name
        self.value = value
