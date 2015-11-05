from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import os
import unittest

from fontTools import ttLib
from fontTools.pens.ttGlyphPen import TTGlyphPen


class TTGlyphPenTest(unittest.TestCase):
    def setUp(self):
        #self.font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
        self.font = ttLib.TTFont()
        ttx_path = os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            '..', 'ttLib', 'testdata', 'TestTTF-Regular.ttx')
        self.font.importXML(ttx_path, quiet=True)
        self.pen = TTGlyphPen(self.font.getGlyphSet())

    def test_drawGlyphsUnchanged(self):
        glyphSet = self.font.getGlyphSet()
        glyfTable = self.font['glyf']

        for name in self.font.getGlyphOrder():
            oldGlyph = glyphSet[name]
            oldGlyph.draw(self.pen)
            oldGlyph = oldGlyph._glyph
            newGlyph = self.pen.glyph()
            newGlyph.recalcBounds(glyfTable)
            if hasattr(oldGlyph, 'program'):
                newGlyph.program = oldGlyph.program
            self.assertEqual(
                oldGlyph.compile(glyfTable), newGlyph.compile(glyfTable))


if __name__ == '__main__':
    unittest.main()
