from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
import os


def write(buffer, text):
    buffer.write(text.encode("utf-8"))


class Features:
    def __init__(self):
        self.language_system = {}  # script --> {language}

    def write(self, out, linesep=os.linesep):
        for script in sorted(self.language_system.keys()):
            for lang in sorted(self.language_system[script]):
                write(out, "languagesystem %s %s;%s" % (script, lang, linesep))
