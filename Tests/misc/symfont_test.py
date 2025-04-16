try:
    from fontTools.misc.symfont import AreaPen
except ImportError:
    AreaPen = None
import unittest
import pytest

precision = 6


def draw1_(pen):
    pen.moveTo((254, 360))
    pen.lineTo((771, 367))
    pen.curveTo((800, 393), (808, 399), (819, 412))
    pen.curveTo((818, 388), (774, 138), (489, 145))
    pen.curveTo((188, 145), (200, 398), (200, 421))
    pen.curveTo((209, 409), (220, 394), (254, 360))
    pen.closePath()


class AreaPenTest(unittest.TestCase):
    @pytest.mark.skipif(AreaPen is None, reason="sympy not installed")
    def test_PScontour_clockwise_line_first(self):
        pen = AreaPen(glyphset=None)
        draw1_(pen)
        self.assertEqual(-104561.35, round(pen.value, precision))

    @pytest.mark.skipif(AreaPen is None, reason="sympy not installed")
    def test_openPaths(self):
        pen = AreaPen()
        pen.moveTo((0, 0))
        pen.endPath()
        self.assertEqual(0, pen.value)

        pen.moveTo((0, 0))
        pen.lineTo((1, 0))
        with self.assertRaises(NotImplementedError):
            pen.endPath()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
