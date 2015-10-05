from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
import fontTools.feaLib.ast as ast


class VoltFile(ast.Block):
    def __init__(self):
        ast.Block.__init__(self, location=None)

class GlyphDefinition(ast.Statement):
    def __init__(self, location, name, gid, gunicode, gtype, components):
        ast.Statement.__init__(self,location)
        self.name = name
        self.id = gid
        self.unicode = gunicode
        self.type = gtype
        self.components = components

class GroupDefinition(ast.Statement):
    def __init__(self, location, name, enum):
        ast.Statement.__init__(self,location)
        self.name = name
        self.enum = enum

class ScriptDefinition(ast.Statement):
    def __init__(self, location, name, tag, langs):
        ast.Statement.__init__(self,location)
        self.name = name
        self.tag = tag
        self.langs = langs

class LangSysDefinition(ast.Statement):
    def __init__(self, location, name, tag, features):
        ast.Statement.__init__(self,location)
        self.name = name
        self.tag = tag
        self.features = features

class FeatureDefinition(ast.Statement):
    def __init__(self, location, name, tag, lookups):
        ast.Statement.__init__(self,location)
        self.name = name
        self.tag = tag
        self.lookups = lookups

class LookupDefinition(ast.Statement):
    def __init__(self, location, name, base, marks, all_flag, direction,
                 comments, context, sub, pos):
        ast.Statement.__init__(self, location)
        self.name = name
        self.base = base
        self.marks = marks
        self.all = all_flag
        self.direction = direction
        self.comments = comments
        self.context = context
        self.sub = sub
        self.pos = pos

class SubstitutionDefinition(ast.Statement):
    def __init__(self, location, src, dest):
        ast.Statement.__init__(self, location)
        self.mapping = zip(src, dest)
