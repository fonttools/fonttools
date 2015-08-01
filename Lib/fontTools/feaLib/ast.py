from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals


def write(buffer, text):
    buffer.write(text.encode("utf-8"))


class FeatureFile(object):
    def __init__(self):
        self.statements = []

    def write(self, out, linesep):
        for s in self.statements:
            s.write(out, linesep)


class GlyphClassDefinition(object):
    def __init__(self, location, name, glyphs):
        self.location = location
        self.name = name
        self.glyphs = glyphs

    def write(self, out, linesep):
        glyphs = " ".join(sorted(self.glyphs))
        write(out, "@%s = [%s];%s" % (self.name, glyphs, linesep))


class LanguageSystemStatement(object):
    def __init__(self, location, script, language):
        self.location = location
        self.script, self.language = (script, language)

    def write(self, out, linesep):
        write(out, "languagesystem %s %s;%s" %
              (self.script.strip(), self.language.strip(), linesep))
