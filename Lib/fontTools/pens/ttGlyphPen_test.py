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
        font.importXML(ttx_path)

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

    def test_moveTo_errorWithinContour(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        with self.assertRaises(AssertionError):
            pen.moveTo((1, 0))

    def test_closePath_ignoresAnchors(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.closePath()
        self.assertFalse(pen.points)
        self.assertFalse(pen.types)
        self.assertFalse(pen.endPts)

    def test_endPath_sameAsClosePath(self):
        pen = TTGlyphPen(None)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        closePathGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.endPath()
        endPathGlyph = pen.glyph()

        self.assertEqual(closePathGlyph, endPathGlyph)

    def test_glyph_errorOnUnendedContour(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        with self.assertRaises(AssertionError):
            pen.glyph()

    def test_glyph_decomposes(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        pen.addComponent(componentName, (1, 0, 0, 1, 2, 0))
        compositeGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        pen.moveTo((2, 0))
        pen.lineTo((2, 1))
        pen.lineTo((3, 0))
        pen.closePath()
        plainGlyph = pen.glyph()

        self.assertEqual(plainGlyph, compositeGlyph)

    def test_remove_extra_move_points(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (0, 0))
        pen.closePath()
        self.assertEqual(len(pen.points), 4)
        self.assertEqual(pen.points[0], (0, 0))

    def test_keep_move_point(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (30, 30))
        # when last and move pts are different, closePath() implies a lineTo
        pen.closePath()
        self.assertEqual(len(pen.points), 5)
        self.assertEqual(pen.points[0], (0, 0))

    def test_keep_duplicate_end_point(self):
        pen = TTGlyphPen(None)
        pen.moveTo((0, 0))
        pen.lineTo((100, 0))
        pen.qCurveTo((100, 50), (50, 100), (0, 0))
        pen.lineTo((0, 0))  # the duplicate point is not removed
        pen.closePath()
        self.assertEqual(len(pen.points), 5)
        self.assertEqual(pen.points[0], (0, 0))


class _TestGlyph(object):
    def __init__(self, glyph):
        self.coordinates = glyph.coordinates

    def draw(self, pen):
        pen.moveTo(self.coordinates[0])
        for point in self.coordinates[1:]:
            pen.lineTo(point)
        pen.closePath()


if __name__ == '__main__':
    unittest.main()
