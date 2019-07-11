from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import os
import unittest
import struct

from fontTools import ttLib
from fontTools.misc.testTools import TestCase
from fontTools.pens.ttGlyphPen import TTGlyphPen, MAX_F2DOT14


class TTGlyphPenTest(TestCase):

    def runEndToEnd(self, filename):
        font = ttLib.TTFont()
        ttx_path = os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            '..', 'ttLib', 'data', filename)
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
        pen.addComponent("missing", (1, 0, 0, 1, 0, 0))  # skipped
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

    def test_within_range_component_transform(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        compositeGlyph = pen.glyph()

        pen.addComponent(componentName, (1.5, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, -1.5, 0, 0))
        expectedGlyph = pen.glyph()

        self.assertEqual(expectedGlyph, compositeGlyph)

    def test_clamp_to_almost_2_component_transform(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (1.99999, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        compositeGlyph = pen.glyph()

        almost2 = MAX_F2DOT14  # 0b1.11111111111111
        pen.addComponent(componentName, (almost2, 0, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, almost2, 0, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, almost2, 1, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, almost2, 0, 0))
        pen.addComponent(componentName, (-2, 0, 0, -2, 0, 0))
        expectedGlyph = pen.glyph()

        self.assertEqual(expectedGlyph, compositeGlyph)

    def test_out_of_range_transform_decomposed(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPen(glyphSet)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (3, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 1, -1, 2))
        pen.addComponent(componentName, (2, 0, 0, -3, 0, 0))
        compositeGlyph = pen.glyph()

        pen.moveTo((0, 0))
        pen.lineTo((0, 2))
        pen.lineTo((3, 0))
        pen.closePath()
        pen.moveTo((-1, 2))
        pen.lineTo((-1, 3))
        pen.lineTo((0, 2))
        pen.closePath()
        pen.moveTo((0, 0))
        pen.lineTo((0, -3))
        pen.lineTo((2, 0))
        pen.closePath()
        expectedGlyph = pen.glyph()

        self.assertEqual(expectedGlyph, compositeGlyph)

    def test_no_handle_overflowing_transform(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPen(glyphSet, handleOverflowingTransforms=False)

        pen.moveTo((0, 0))
        pen.lineTo((0, 1))
        pen.lineTo((1, 0))
        pen.closePath()
        baseGlyph = pen.glyph()
        glyphSet[componentName] = _TestGlyph(baseGlyph)

        pen.addComponent(componentName, (3, 0, 0, 1, 0, 0))
        compositeGlyph = pen.glyph()

        self.assertEqual(compositeGlyph.components[0].transform,
                         ((3, 0), (0, 1)))

        with self.assertRaises(struct.error):
            compositeGlyph.compile({'a': baseGlyph})


class _TestGlyph(object):
    def __init__(self, glyph):
        self.coordinates = glyph.coordinates

    def draw(self, pen):
        pen.moveTo(self.coordinates[0])
        for point in self.coordinates[1:]:
            pen.lineTo(point)
        pen.closePath()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
