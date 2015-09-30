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
    def __init__(self, location, name, glyphs, groups, ranges):
        ast.Statement.__init__(self,location)
        self.name = name
        self.enum = {"glyphs": glyphs,
                     "groups": groups,
                     "ranges": ranges}
