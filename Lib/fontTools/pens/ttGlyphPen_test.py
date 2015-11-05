from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import os
import unittest

from fontTools import ttLib
from fontTools.pens.ttGlyphPen import TTGlyphPen


class TTGlyphPenTest(unittest.TestCase):

    def runEndToEnd(self, filename):
        font = ttLib.TTFont()
        ttx_path = os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            '..', 'ttLib', 'testdata', filename)
        font.importXML(ttx_path, quiet=True)

        glyphSet = font.getGlyphSet()
        glyfTable = font['glyf']
        pen = TTGlyphPen(font.getGlyphSet())

        for name in font.getGlyphOrder():
            oldGlyph = glyphSet[name]
            oldGlyph.draw(pen)
            oldGlyph = oldGlyph._glyph
            newGlyph = pen.glyph()

            if hasattr(oldGlyph, 'program'):
                newGlyph.program = oldGlyph.program

            self.assertEqual(
                oldGlyph.compile(glyfTable), newGlyph.compile(glyfTable))

    def test_e2e_linesAndSimpleComponents(self):
        self.runEndToEnd('TestTTF-Regular.ttx')

    def test_e2e_curvesAndComponentTransforms(self):
        self.runEndToEnd('TestTTFComplex-Regular.ttx')


if __name__ == '__main__':
    unittest.main()
