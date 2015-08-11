from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals


class FeatureFile(object):
    def __init__(self):
        self.statements = []


class FeatureBlock(object):
    def __init__(self, location, name, use_extension):
        self.location = location
        self.name, self.use_extension = name, use_extension
        self.statements = []


class LookupBlock(object):
    def __init__(self, location, name, use_extension):
        self.location = location
        self.name, self.use_extension = name, use_extension
        self.statements = []


class GlyphClassDefinition(object):
    def __init__(self, location, name, glyphs):
        self.location = location
        self.name = name
        self.glyphs = glyphs


class AnchorDefinition(object):
    def __init__(self, location, name, x, y, contourpoint):
        self.location = location
        self.name, self.x, self.y, self.contourpoint = name, x, y, contourpoint


class LanguageStatement(object):
    def __init__(self, location, language, include_default, required):
        self.location = location
        self.language = language
        self.include_default = include_default
        self.required = required


class LanguageSystemStatement(object):
    def __init__(self, location, script, language):
        self.location = location
        self.script, self.language = (script, language)


class IgnoreSubstitutionRule(object):
    def __init__(self, location, prefix, glyphs, suffix):
        self.location = location
        self.prefix, self.glyphs, self.suffix = (prefix, glyphs, suffix)


class LookupReferenceStatement(object):
    def __init__(self, location, lookup):
        self.location, self.lookup = (location, lookup)


class ScriptStatement(object):
    def __init__(self, location, script):
        self.location = location
        self.script = script


class SubtableStatement(object):
    def __init__(self, location):
        self.location = location


class SubstitutionRule(object):
    def __init__(self, location, old, new):
        self.location, self.old, self.new = (location, old, new)
        self.old_prefix = []
        self.old_suffix = []
        self.lookups = [None] * len(old)


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
