from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.t2CharStringPen import T2CharStringPen
import unittest


class T2CharStringPenTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def assertAlmostEqualProgram(self, expected, actual):
        self.assertEqual(len(expected), len(actual))
        for i1, i2 in zip(expected, actual):
            if isinstance(i1, basestring):
                self.assertIsInstance(i2, basestring)
                self.assertEqual(i1, i2)
            else:
                self.assertAlmostEqual(i1, i2)

    def test_draw_h_v_lines(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))
        pen.lineTo((10, 10))
        pen.lineTo((0, 10))
        pen.closePath()  # no-op
        pen.moveTo((10, 10))
        pen.lineTo((10, 20))
        pen.lineTo((0, 20))
        pen.lineTo((0, 10))
        pen.closePath()
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 'hmoveto',
             10, 10, -10, 'hlineto',
             10, 'hmoveto',
             10, -10, -10, 'vlineto',
             'endchar'],
            charstring.program)

    def test_draw_lines(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((5, 5))
        pen.lineTo((25, 15))
        pen.lineTo((35, 35))
        pen.lineTo((15, 25))
        pen.closePath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             5, 5, 'rmoveto',
             20, 10, 10, 20, -20, -10, 'rlineto',
             'endchar'],
            charstring.program)

    def test_draw_h_v_curves(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((0, 0))
        pen.curveTo((10, 0), (20, 10), (20, 20))
        pen.curveTo((20, 30), (10, 40), (0, 40))
        pen.endPath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 'hmoveto',
             10, 10, 10, 10, 10, -10, 10, -10, 'hvcurveto',
             'endchar'],
            charstring.program)

    def test_draw_curves(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((95, 25))
        pen.curveTo((115, 44), (115, 76), (95, 95))
        pen.curveTo((76, 114), (44, 115), (25, 95))
        pen.endPath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             95, 25, 'rmoveto',
             20, 19, 0, 32, -20, 19, -19, 19, -32, 1, -19, -20, 'rrcurveto',
             'endchar'],
            charstring.program)

    def test_draw_more_curves(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((10, 10))
        pen.curveTo((20, 10), (50, 10), (60, 10))
        pen.curveTo((60, 20), (60, 50), (60, 60))
        pen.curveTo((50, 50), (40, 60), (30, 60))
        pen.curveTo((40, 50), (30, 40), (30, 30))
        pen.curveTo((30, 25), (25, 19), (20, 20))
        pen.curveTo((15, 20), (9, 25), (10, 30))
        pen.curveTo((7, 25), (6, 15), (10, 10))
        pen.endPath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             10, 10, 'rmoveto',
             10, 30, 0, 10, 'hhcurveto',
             10, 0, 30, 10, 'vvcurveto',
             -10, -10, -10, 10, -10, 'hhcurveto',
             10, -10, -10, -10, -10, 'vvcurveto',
             -5, -5, -6, -5, 1, 'vhcurveto',
             -5, -6, 5, 5, 1, 'hvcurveto',
             -3, -5, -1, -10, 4, -5, 'rrcurveto',
             'endchar'],
            charstring.program)

    def test_default_width(self):
        pen = T2CharStringPen(None, {})
        charstring = pen.getCharString(None, None)
        self.assertEqual(['endchar'], charstring.program)

    def test_no_round(self):
        pen = T2CharStringPen(100.1, {}, roundTolerance=0.0)
        pen.moveTo((0, 0))
        pen.curveTo((10.1, 0.1), (19.9, 9.9), (20.49, 20.49))
        pen.curveTo((20.49, 30.49), (9.9, 39.9), (0.1, 40.1))
        pen.closePath()
        charstring = pen.getCharString(None, None)

        self.assertAlmostEqualProgram(
            [100,  # we always round the advance width
             0, 'hmoveto',
             10.1, 0.1, 9.8, 9.8, 0.59, 10.59, 'rrcurveto',
             10, -10.59, 9.41, -9.8, 0.2, 'vhcurveto',
             'endchar'],
            charstring.program)

    def test_round_all(self):
        pen = T2CharStringPen(100.1, {}, roundTolerance=0.5)
        pen.moveTo((0, 0))
        pen.curveTo((10.1, 0.1), (19.9, 9.9), (20.49, 20.49))
        pen.curveTo((20.49, 30.5), (9.9, 39.9), (0.1, 40.1))
        pen.closePath()
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 'hmoveto',
             10, 10, 10, 10, 11, -10, 9, -10, 'hvcurveto',
             'endchar'],
            charstring.program)

    def test_round_some(self):
        pen = T2CharStringPen(100, {}, roundTolerance=0.2)
        pen.moveTo((0, 0))
        # the following two are rounded as within the tolerance
        pen.lineTo((10.1, 0.1))
        pen.lineTo((19.9, 9.9))
        # this one is not rounded as it exceeds the tolerance
        pen.lineTo((20.49, 20.49))
        pen.closePath()
        charstring = pen.getCharString(None, None)

        self.assertAlmostEqualProgram(
            [100,
             0, 'hmoveto',
             10, 'hlineto',
             10, 10, 0.49, 10.49, 'rlineto',
             'endchar'],
            charstring.program)

    def test_invalid_tolerance(self):
        self.assertRaisesRegex(
            ValueError,
            "Rounding tolerance must be positive",
            T2CharStringPen, None, {}, roundTolerance=-0.1)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
