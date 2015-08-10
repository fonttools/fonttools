from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals


class FeatureFile(object):
    def __init__(self):
        self.statements = []


class FeatureBlock(object):
    def __init__(self, location, tag):
        self.location = location
        self.tag = tag
        self.statements = []


class GlyphClassDefinition(object):
    def __init__(self, location, name, glyphs):
        self.location = location
        self.name = name
        self.glyphs = glyphs


class LanguageSystemStatement(object):
    def __init__(self, location, script, language):
        self.location = location
        self.script, self.language = (script, language)


class IgnoreSubstitutionRule(object):
    def __init__(self, location, prefix, glyphs, suffix):
        self.location = location
        self.prefix, self.glyphs, self.suffix = (prefix, glyphs, suffix)


class SubstitutionRule(object):
    def __init__(self, location, old, new):
        self.location, self.old, self.new = (location, old, new)
        self.old_prefix = []
        self.old_suffix = []


class ValueRecord(object):
    def __init__(self, location, xPlacement, yPlacement, xAdvance, yAdvance):
        self.location = location
        self.xPlacement, self.yPlacement = (xPlacement, yPlacement)
        self.xAdvance, self.yAdvance = (xAdvance, yAdvance)


class ValueRecordDefinition(object):
    def __init__(self, location, name, value):
        self.location = location
        self.name = name
        self.value = value
