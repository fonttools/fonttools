from fontTools.misc.py23 import *
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
import unittest


def draw_(pen):
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.qCurveTo((50, 75), (60, 50), (50, 25), (0, 0))
    pen.curveTo((-50, 25), (-60, 50), (-50, 75), (0, 100))
    pen.closePath()


def bounds_(pen):
    return " ".join(["%.0f" % c for c in pen.bounds])


class BoundsPenTest(unittest.TestCase):
    def test_draw(self):
        pen = BoundsPen(None)
        draw_(pen)
        self.assertEqual("-55 0 58 100", bounds_(pen))

    def test_empty(self):
        pen = BoundsPen(None)
        self.assertEqual(None, pen.bounds)

    def test_curve(self):
        pen = BoundsPen(None)
        pen.moveTo((0, 0))
        pen.curveTo((20, 10), (90, 40), (0, 0))
        self.assertEqual("0 0 45 20", bounds_(pen))

    def test_quadraticCurve(self):
        pen = BoundsPen(None)
        pen.moveTo((0, 0))
        pen.qCurveTo((6, 6), (10, 0))
        self.assertEqual("0 0 10 3", bounds_(pen))


class ControlBoundsPenTest(unittest.TestCase):
    def test_draw(self):
        pen = ControlBoundsPen(None)
        draw_(pen)
        self.assertEqual("-55 0 60 100", bounds_(pen))

    def test_empty(self):
        pen = ControlBoundsPen(None)
        self.assertEqual(None, pen.bounds)

    def test_curve(self):
        pen = ControlBoundsPen(None)
        pen.moveTo((0, 0))
        pen.curveTo((20, 10), (90, 40), (0, 0))
        self.assertEqual("0 0 90 40", bounds_(pen))

    def test_quadraticCurve(self):
        pen = ControlBoundsPen(None)
        pen.moveTo((0, 0))
        pen.qCurveTo((6, 6), (10, 0))
        self.assertEqual("0 0 10 6", bounds_(pen))

    def test_singlePoint(self):
        pen = ControlBoundsPen(None)
        pen.moveTo((-5, 10))
        self.assertEqual("-5 10 -5 10", bounds_(pen))

    def test_ignoreSinglePoint(self):
        pen = ControlBoundsPen(None, ignoreSinglePoints=True)
        pen.moveTo((0, 10))
        self.assertEqual(None, pen.bounds)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
