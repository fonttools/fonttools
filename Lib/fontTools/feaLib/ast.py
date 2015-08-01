from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals


def write(buffer, text):
    buffer.write(text.encode("utf-8"))


class FeatureFile:
    def __init__(self):
        self.statements = []

    def write(self, out, linesep):
        for s in self.statements:
            s.write(out, linesep)


class LanguageSystemStatement:
    def __init__(self, location, script, language):
        self.location = location
        self.script, self.language = (script, language)

    def write(self, out, linesep):
        write(out, "languagesystem %s %s;%s" %
              (self.script.strip(), self.language.strip(), linesep))
