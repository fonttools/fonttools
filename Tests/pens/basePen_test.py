from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import \
    BasePen, decomposeSuperBezierSegment, decomposeQuadraticSegment
from fontTools.misc.loggingTools import CapturingLogHandler
import unittest


class _TestPen(BasePen):
    def __init__(self):
        BasePen.__init__(self, glyphSet={})
        self._commands = []

    def __repr__(self):
        return " ".join(self._commands)

    def getCurrentPoint(self):
        return self._getCurrentPoint()

    def _moveTo(self, pt):
        self._commands.append("%s %s moveto" % (pt[0], pt[1]))

    def _lineTo(self, pt):
        self._commands.append("%s %s lineto" % (pt[0], pt[1]))

    def _curveToOne(self, bcp1, bcp2, pt):
        self._commands.append("%s %s %s %s %s %s curveto" %
                              (bcp1[0], bcp1[1],
                               bcp2[0], bcp2[1],
                               pt[0], pt[1]))

    def _closePath(self):
        self._commands.append("closepath")

    def _endPath(self):
        self._commands.append("endpath")


class _TestGlyph:
    def draw(self, pen):
        pen.moveTo((0.0, 0.0))
        pen.lineTo((0.0, 100.0))
        pen.curveTo((50.0, 75.0), (60.0, 50.0), (50.0, 25.0), (0.0, 0.0))
        pen.closePath()


class BasePenTest(unittest.TestCase):
    def test_moveTo(self):
        pen = _TestPen()
        pen.moveTo((0.5, -4.3))
        self.assertEqual("0.5 -4.3 moveto", repr(pen))
        self.assertEqual((0.5, -4.3), pen.getCurrentPoint())

    def test_lineTo(self):
        pen = _TestPen()
        pen.moveTo((4, 5))
        pen.lineTo((7, 8))
        self.assertEqual("4 5 moveto 7 8 lineto", repr(pen))
        self.assertEqual((7, 8), pen.getCurrentPoint())

    def test_curveTo_zeroPoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        self.assertRaises(AssertionError, pen.curveTo)

    def test_curveTo_onePoint(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.curveTo((1.0, 1.1))
        self.assertEqual("0.0 0.0 moveto 1.0 1.1 lineto", repr(pen))
        self.assertEqual((1.0, 1.1), pen.getCurrentPoint())

    def test_curveTo_twoPoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.curveTo((6.0, 3.0), (3.0, 6.0))
        self.assertEqual("0.0 0.0 moveto 4.0 2.0 5.0 4.0 3.0 6.0 curveto",
                         repr(pen))
        self.assertEqual((3.0, 6.0), pen.getCurrentPoint())

    def test_curveTo_manyPoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.curveTo((1.0, 1.1), (2.0, 2.1), (3.0, 3.1), (4.0, 4.1))
        self.assertEqual("0.0 0.0 moveto "
                         "1.0 1.1 1.5 1.6 2.0 2.1 curveto "
                         "2.5 2.6 3.0 3.1 4.0 4.1 curveto", repr(pen))
        self.assertEqual((4.0, 4.1), pen.getCurrentPoint())

    def test_qCurveTo_zeroPoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        self.assertRaises(AssertionError, pen.qCurveTo)

    def test_qCurveTo_onePoint(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.qCurveTo((77.7, 99.9))
        self.assertEqual("0.0 0.0 moveto 77.7 99.9 lineto", repr(pen))
        self.assertEqual((77.7, 99.9), pen.getCurrentPoint())

    def test_qCurveTo_manyPoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.qCurveTo((6.0, 3.0), (3.0, 6.0))
        self.assertEqual("0.0 0.0 moveto 4.0 2.0 5.0 4.0 3.0 6.0 curveto",
                         repr(pen))
        self.assertEqual((3.0, 6.0), pen.getCurrentPoint())

    def test_qCurveTo_onlyOffCurvePoints(self):
        pen = _TestPen()
        pen.moveTo((0.0, 0.0))
        pen.qCurveTo((6.0, -6.0), (12.0, 12.0), (18.0, -18.0), None)
        self.assertEqual("0.0 0.0 moveto "
                         "12.0 -12.0 moveto "
                         "8.0 -8.0 7.0 -3.0 9.0 3.0 curveto "
                         "11.0 9.0 13.0 7.0 15.0 -3.0 curveto "
                         "17.0 -13.0 16.0 -16.0 12.0 -12.0 curveto", repr(pen))
        self.assertEqual((12.0, -12.0), pen.getCurrentPoint())

    def test_closePath(self):
        pen = _TestPen()
        pen.lineTo((3, 4))
        pen.closePath()
        self.assertEqual("3 4 lineto closepath", repr(pen))
        self.assertEqual(None, pen.getCurrentPoint())

    def test_endPath(self):
        pen = _TestPen()
        pen.lineTo((3, 4))
        pen.endPath()
        self.assertEqual("3 4 lineto endpath", repr(pen))
        self.assertEqual(None, pen.getCurrentPoint())

    def test_addComponent(self):
        pen = _TestPen()
        pen.glyphSet["oslash"] = _TestGlyph()
        pen.addComponent("oslash", (2, 3, 0.5, 2, -10, 0))
        self.assertEqual("-10.0 0.0 moveto "
                         "40.0 200.0 lineto "
                         "127.5 300.0 131.25 290.0 125.0 265.0 curveto "
                         "118.75 240.0 102.5 200.0 -10.0 0.0 curveto "
                         "closepath", repr(pen))
        self.assertEqual(None, pen.getCurrentPoint())

    def test_addComponent_skip_missing(self):
        pen = _TestPen()
        with CapturingLogHandler(pen.log, "WARNING") as captor:
            pen.addComponent("nonexistent", (1, 0, 0, 1, 0, 0))
        captor.assertRegex("glyph '.*' is missing from glyphSet; skipped")


class DecomposeSegmentTest(unittest.TestCase):
    def test_decomposeSuperBezierSegment(self):
        decompose = decomposeSuperBezierSegment
        self.assertRaises(AssertionError, decompose, [])
        self.assertRaises(AssertionError, decompose, [(0, 0)])
        self.assertRaises(AssertionError, decompose, [(0, 0), (1, 1)])
        self.assertEqual([((0, 0), (1, 1), (2, 2))],
                         decompose([(0, 0), (1, 1), (2, 2)]))
        self.assertEqual(
            [((0, 0), (2, -2), (4, 0)), ((6, 2), (8, 8), (12, -12))],
            decompose([(0, 0), (4, -4), (8, 8), (12, -12)]))

    def test_decomposeQuadraticSegment(self):
        decompose = decomposeQuadraticSegment
        self.assertRaises(AssertionError, decompose, [])
        self.assertRaises(AssertionError, decompose, [(0, 0)])
        self.assertEqual([((0,0), (4, 8))], decompose([(0, 0), (4, 8)]))
        self.assertEqual([((0,0), (2, 4)), ((4, 8), (9, -9))],
                         decompose([(0, 0), (4, 8), (9, -9)]))
        self.assertEqual(
            [((0, 0), (2.0, 4.0)), ((4, 8), (6.5, -0.5)), ((9, -9), (10, 10))],
            decompose([(0, 0), (4, 8), (9, -9), (10, 10)]))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
