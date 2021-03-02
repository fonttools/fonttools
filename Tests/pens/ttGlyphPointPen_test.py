import os
import unittest
import struct

from fontTools import ttLib
from fontTools.misc.testTools import TestCase
from fontTools.pens.ttGlyphPointPen import TTGlyphPointPen, MAX_F2DOT14
from fontTools.ttLib.tables import ttProgram


class TTGlyphPointPenTest(TestCase):

    def runEndToEnd(self, filename):
        font = ttLib.TTFont()
        ttx_path = os.path.join(
            os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
            '..', 'ttLib', 'data', filename)
        font.importXML(ttx_path)

        glyphSet = font.getGlyphSet()
        glyfTable = font['glyf']
        pen = TTGlyphPointPen(font.getGlyphSet())

        for name in font.getGlyphOrder():
            oldGlyph = glyphSet[name]
            oldGlyph.drawPoints(pen)
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

    def test_glyph_simple(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((50, 0), "line")
        pen.addPoint((450, 0), "line")
        pen.addPoint((450, 700), "line")
        pen.addPoint((50, 700), "line")
        pen.endPath()
        glyph = pen.glyph()
        self.assertEqual(glyph.numberOfContours, 1)
        self.assertEqual(glyph.endPtsOfContours, [3])

    def test_glyph_errorOnCurve(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        with self.assertRaises(NotImplementedError):
            pen.addPoint((0, 0), "curve")

    def test_beginPath_beginPathOnOpenPath(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0))
        with self.assertRaises(AssertionError):
            pen.beginPath()

    def test_closePath_ignoresAnchors(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.endPath()
        self.assertFalse(pen.points)
        self.assertFalse(pen.types)
        self.assertFalse(pen.endPts)

    def test_glyph_errorOnUnendedContour(self):
        pen = TTGlyphPointPen(None)
        pen.beginPath()
        pen.addPoint((0, 0))
        with self.assertRaises(AssertionError):
            pen.glyph()

    def test_glyph_decomposes(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        pen.addComponent(componentName, (1, 0, 0, 1, 2, 0))
        pen.addComponent("missing", (1, 0, 0, 1, 0, 0))  # skipped
        compositeGlyph = pen.glyph()

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((2, 0), "line")
        pen.addPoint((2, 1), "line")
        pen.addPoint((3, 0), "line")
        pen.endPath()
        plainGlyph = pen.glyph()

        self.assertEqual(plainGlyph, compositeGlyph)

    # def test_remove_extra_move_points(self):
    #     pen = TTGlyphPointPen(None)
    #     pen.moveTo((0, 0))
    #     pen.lineTo((100, 0))
    #     pen.qCurveTo((100, 50), (50, 100), (0, 0))
    #     pen.closePath()
    #     self.assertEqual(len(pen.points), 4)
    #     self.assertEqual(pen.points[0], (0, 0))

    # def test_keep_move_point(self):
    #     pen = TTGlyphPointPen(None)
    #     pen.moveTo((0, 0))
    #     pen.lineTo((100, 0))
    #     pen.qCurveTo((100, 50), (50, 100), (30, 30))
    #     # when last and move pts are different, closePath() implies a lineTo
    #     pen.closePath()
    #     self.assertEqual(len(pen.points), 5)
    #     self.assertEqual(pen.points[0], (0, 0))

    # def test_keep_duplicate_end_point(self):
    #     pen = TTGlyphPointPen(None)
    #     pen.moveTo((0, 0))
    #     pen.lineTo((100, 0))
    #     pen.qCurveTo((100, 50), (50, 100), (0, 0))
    #     pen.lineTo((0, 0))  # the duplicate point is not removed
    #     pen.closePath()
    #     self.assertEqual(len(pen.points), 5)
    #     self.assertEqual(pen.points[0], (0, 0))

    def test_within_range_component_transform(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
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
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
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
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        glyphSet[componentName] = _TestGlyph(pen.glyph())

        pen.addComponent(componentName, (3, 0, 0, 2, 0, 0))
        pen.addComponent(componentName, (1, 0, 0, 1, -1, 2))
        pen.addComponent(componentName, (2, 0, 0, -3, 0, 0))
        compositeGlyph = pen.glyph()

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 2), "line")
        pen.addPoint((3, 0), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((-1, 2), "line")
        pen.addPoint((-1, 3), "line")
        pen.addPoint((0, 2), "line")
        pen.endPath()
        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, -3), "line")
        pen.addPoint((2, 0), "line")
        pen.endPath()
        expectedGlyph = pen.glyph()

        self.assertEqual(expectedGlyph, compositeGlyph)

    def test_no_handle_overflowing_transform(self):
        componentName = 'a'
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet, handleOverflowingTransforms=False)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((1, 0), "line")
        pen.endPath()
        baseGlyph = pen.glyph()
        glyphSet[componentName] = _TestGlyph(baseGlyph)

        pen.addComponent(componentName, (3, 0, 0, 1, 0, 0))
        compositeGlyph = pen.glyph()

        self.assertEqual(compositeGlyph.components[0].transform,
                         ((3, 0), (0, 1)))

        with self.assertRaises(struct.error):
            compositeGlyph.compile({'a': baseGlyph})

    def assertGlyphBoundsEqual(self, glyph, bounds):
        self.assertEqual((glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax), bounds)

    def test_round_float_coordinates_and_component_offsets(self):
        glyphSet = {}
        pen = TTGlyphPointPen(glyphSet)

        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((0, 1), "line")
        pen.addPoint((367.6, 0), "line")
        pen.endPath()
        simpleGlyph = pen.glyph()

        simpleGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(simpleGlyph, (0, 0, 368, 1))

        componentName = 'a'
        glyphSet[componentName] = simpleGlyph

        pen.addComponent(componentName, (1, 0, 0, 1, -86.4, 0))
        compositeGlyph = pen.glyph()

        compositeGlyph.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(compositeGlyph, (-86, 0, 282, 1))

    def test_scaled_component_bounds(self):
        glyphSet = {}

        pen = TTGlyphPointPen(glyphSet)
        pen.beginPath()
        pen.addPoint((-231, 939), "line")
        pen.addPoint((-55, 939), "line")
        pen.addPoint((-55, 745), "line")
        pen.addPoint((-231, 745), "line")
        pen.endPath()
        glyphSet["gravecomb"] = gravecomb = pen.glyph()

        pen = TTGlyphPointPen(glyphSet)
        pen.beginPath()
        pen.addPoint((-278, 939), "line")
        pen.addPoint((8, 939), "line")
        pen.addPoint((8, 745), "line")
        pen.addPoint((-278, 745), "line")
        pen.endPath()
        glyphSet["circumflexcomb"] = circumflexcomb = pen.glyph()

        pen = TTGlyphPointPen(glyphSet)
        pen.addComponent("circumflexcomb", (1, 0, 0, 1, 0, 0))
        pen.addComponent("gravecomb", (0.9, 0, 0, 0.9, 198, 180))
        glyphSet["uni0302_uni0300"] = uni0302_uni0300 = pen.glyph()

        uni0302_uni0300.recalcBounds(glyphSet)
        self.assertGlyphBoundsEqual(uni0302_uni0300, (-278, 745, 148, 1025))


class _TestGlyph(object):
    def __init__(self, glyph):
        self.coordinates = glyph.coordinates

    def drawPoints(self, pen):
        pen.beginPath()
        for point in self.coordinates:
            pen.addPoint(point, "line")
        pen.endPath()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
