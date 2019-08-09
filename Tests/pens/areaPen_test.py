from fontTools.misc.py23 import *
from fontTools.pens.areaPen import AreaPen
import unittest

precision = 6

def draw1_(pen):
    pen.moveTo( (254, 360) )
    pen.lineTo( (771, 367) )
    pen.curveTo( (800, 393), (808, 399), (819, 412) )
    pen.curveTo( (818, 388), (774, 138), (489, 145) )
    pen.curveTo( (188, 145), (200, 398), (200, 421) )
    pen.curveTo( (209, 409), (220, 394), (254, 360) )
    pen.closePath()

def draw2_(pen):
    pen.moveTo( (254, 360) )
    pen.curveTo( (220, 394), (209, 409), (200, 421) )
    pen.curveTo( (200, 398), (188, 145), (489, 145) )
    pen.curveTo( (774, 138), (818, 388), (819, 412) )
    pen.curveTo( (808, 399), (800, 393), (771, 367) )
    pen.closePath()

def draw3_(pen):
    pen.moveTo( (771, 367) )
    pen.curveTo( (800, 393), (808, 399), (819, 412) )
    pen.curveTo( (818, 388), (774, 138), (489, 145) )
    pen.curveTo( (188, 145), (200, 398), (200, 421) )
    pen.curveTo( (209, 409), (220, 394), (254, 360) )
    pen.closePath()

def draw4_(pen):
    pen.moveTo( (771, 367) )
    pen.lineTo( (254, 360) )
    pen.curveTo( (220, 394), (209, 409), (200, 421) )
    pen.curveTo( (200, 398), (188, 145), (489, 145) )
    pen.curveTo( (774, 138), (818, 388), (819, 412) )
    pen.curveTo( (808, 399), (800, 393), (771, 367) )
    pen.closePath()

def draw5_(pen):
    pen.moveTo( (254, 360) )
    pen.lineTo( (771, 367) )
    pen.qCurveTo( (793, 386), (802, 394) )
    pen.qCurveTo( (811, 402), (819, 412) )
    pen.qCurveTo( (819, 406), (814, 383.5) )
    pen.qCurveTo( (809, 361), (796, 330.5) )
    pen.qCurveTo( (783, 300), (760.5, 266.5) )
    pen.qCurveTo( (738, 233), (701, 205.5) )
    pen.qCurveTo( (664, 178), (612, 160.5) )
    pen.qCurveTo( (560, 143), (489, 145) )
    pen.qCurveTo( (414, 145), (363, 164) )
    pen.qCurveTo( (312, 183), (280, 211.5) )
    pen.qCurveTo( (248, 240), (231.5, 274.5) )
    pen.qCurveTo( (215, 309), (208, 339.5) )
    pen.qCurveTo( (201, 370), (200.5, 392.5) )
    pen.qCurveTo( (200, 415), (200, 421) )
    pen.qCurveTo( (207, 412), (217.5, 399) )
    pen.qCurveTo( (228, 386), (254, 360) )
    pen.closePath()

def draw6_(pen):
    pen.moveTo( (254, 360) )
    pen.qCurveTo( (228, 386), (217.5, 399) )
    pen.qCurveTo( (207, 412), (200, 421) )
    pen.qCurveTo( (200, 415), (200.5, 392.5) )
    pen.qCurveTo( (201, 370), (208, 339.5) )
    pen.qCurveTo( (215, 309), (231.5, 274.5) )
    pen.qCurveTo( (248, 240), (280, 211.5) )
    pen.qCurveTo( (312, 183), (363, 164) )
    pen.qCurveTo( (414, 145), (489, 145) )
    pen.qCurveTo( (560, 143), (612, 160.5) )
    pen.qCurveTo( (664, 178), (701, 205.5) )
    pen.qCurveTo( (738, 233), (760.5, 266.5) )
    pen.qCurveTo( (783, 300), (796, 330.5) )
    pen.qCurveTo( (809, 361), (814, 383.5) )
    pen.qCurveTo( (819, 406), (819, 412) )
    pen.qCurveTo( (811, 402), (802, 394) )
    pen.qCurveTo( (793, 386), (771, 367) )
    pen.closePath()

def draw7_(pen):
    pen.moveTo( (771, 367) )
    pen.qCurveTo( (793, 386), (802, 394) )
    pen.qCurveTo( (811, 402), (819, 412) )
    pen.qCurveTo( (819, 406), (814, 383.5) )
    pen.qCurveTo( (809, 361), (796, 330.5) )
    pen.qCurveTo( (783, 300), (760.5, 266.5) )
    pen.qCurveTo( (738, 233), (701, 205.5) )
    pen.qCurveTo( (664, 178), (612, 160.5) )
    pen.qCurveTo( (560, 143), (489, 145) )
    pen.qCurveTo( (414, 145), (363, 164) )
    pen.qCurveTo( (312, 183), (280, 211.5) )
    pen.qCurveTo( (248, 240), (231.5, 274.5) )
    pen.qCurveTo( (215, 309), (208, 339.5) )
    pen.qCurveTo( (201, 370), (200.5, 392.5) )
    pen.qCurveTo( (200, 415), (200, 421) )
    pen.qCurveTo( (207, 412), (217.5, 399) )
    pen.qCurveTo( (228, 386), (254, 360) )
    pen.closePath()

def draw8_(pen):
    pen.moveTo( (771, 367) )
    pen.lineTo( (254, 360) )
    pen.qCurveTo( (228, 386), (217.5, 399) )
    pen.qCurveTo( (207, 412), (200, 421) )
    pen.qCurveTo( (200, 415), (200.5, 392.5) )
    pen.qCurveTo( (201, 370), (208, 339.5) )
    pen.qCurveTo( (215, 309), (231.5, 274.5) )
    pen.qCurveTo( (248, 240), (280, 211.5) )
    pen.qCurveTo( (312, 183), (363, 164) )
    pen.qCurveTo( (414, 145), (489, 145) )
    pen.qCurveTo( (560, 143), (612, 160.5) )
    pen.qCurveTo( (664, 178), (701, 205.5) )
    pen.qCurveTo( (738, 233), (760.5, 266.5) )
    pen.qCurveTo( (783, 300), (796, 330.5) )
    pen.qCurveTo( (809, 361), (814, 383.5) )
    pen.qCurveTo( (819, 406), (819, 412) )
    pen.qCurveTo( (811, 402), (802, 394) )
    pen.qCurveTo( (793, 386), (771, 367) )
    pen.closePath()


class AreaPenTest(unittest.TestCase):
    def test_PScontour_clockwise_line_first(self):
        pen = AreaPen(None)
        draw1_(pen)
        self.assertEqual(-104561.35, round(pen.value, precision))

    def test_PScontour_counterclockwise_line_last(self):
        pen = AreaPen(None)
        draw2_(pen)
        self.assertEqual(104561.35, round(pen.value, precision))

    def test_PScontour_clockwise_line_last(self):
        pen = AreaPen(None)
        draw3_(pen)
        self.assertEqual(-104561.35, round(pen.value, precision))

    def test_PScontour_counterclockwise_line_first(self):
        pen = AreaPen(None)
        draw4_(pen)
        self.assertEqual(104561.35, round(pen.value, precision))

    def test_TTcontour_clockwise_line_first(self):
        pen = AreaPen(None)
        draw5_(pen)
        self.assertEqual(-104602.791667, round(pen.value, precision))

    def test_TTcontour_counterclockwise_line_last(self):
        pen = AreaPen(None)
        draw6_(pen)
        self.assertEqual(104602.791667, round(pen.value, precision))

    def test_TTcontour_clockwise_line_last(self):
        pen = AreaPen(None)
        draw7_(pen)
        self.assertEqual(-104602.791667, round(pen.value, precision))

    def test_TTcontour_counterclockwise_line_first(self):
        pen = AreaPen(None)
        draw8_(pen)
        self.assertEqual(104602.791667, round(pen.value, precision))

    def test_openPaths(self):
        pen = AreaPen()
        pen.moveTo((0, 0))
        pen.endPath()
        self.assertEqual(0, pen.value)

        pen.moveTo((0, 0))
        pen.lineTo((1, 0))
        with self.assertRaises(NotImplementedError):
            pen.endPath()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
