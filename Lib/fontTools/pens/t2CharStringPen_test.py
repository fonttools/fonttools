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

    def test_draw_lines(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((0, 0))
        pen.lineTo((10, 0))
        pen.lineTo((10, 10))
        pen.lineTo((0, 10))
        pen.closePath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 0, 'rmoveto',
             10, 0, 'rlineto',
             0, 10, 'rlineto',
             -10, 0, 'rlineto',
             'endchar'],
            charstring.program)

    def test_draw_curves(self):
        pen = T2CharStringPen(100, {})
        pen.moveTo((0, 0))
        pen.curveTo((10, 0), (20, 10), (20, 20))
        pen.curveTo((20, 30), (10, 40), (0, 40))
        pen.endPath()  # no-op
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 0, 'rmoveto',
             10, 0, 10, 10, 0, 10, 'rrcurveto',
             0, 10, -10, 10, -10, 0, 'rrcurveto',
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
             0, 0, 'rmoveto',
             10.1, 0.1, 9.8, 9.8, 0.59, 10.59, 'rrcurveto',
             0, 10, -10.59, 9.41, -9.8, 0.2, 'rrcurveto',
             'endchar'],
            charstring.program)

    def test_round_all(self):
        pen = T2CharStringPen(100.1, {}, roundTolerance=0.5)
        pen.moveTo((0, 0))
        pen.curveTo((10.1, 0.1), (19.9, 9.9), (20.49, 20.49))
        pen.curveTo((20.49, 30.49), (9.9, 39.9), (0.1, 40.1))
        pen.closePath()
        charstring = pen.getCharString(None, None)

        self.assertEqual(
            [100,
             0, 0, 'rmoveto',
             10, 0, 10, 10, 0, 10, 'rrcurveto',
             0, 10, -10, 10, -10, 0, 'rrcurveto',
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
             0, 0, 'rmoveto',
             10, 0, 'rlineto',
             10, 10, 'rlineto',
             0.49, 10.49, 'rlineto',
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
