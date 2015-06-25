from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.pointInsidePen import PointInsidePen
import unittest


class PointInsidePenTest(unittest.TestCase):
    def test_line(self):
        def draw_triangles(pen):
            pen.moveTo((0,0)); pen.lineTo((10,5)); pen.lineTo((10,0))
            pen.moveTo((9,1)); pen.lineTo((4,1)); pen.lineTo((9,4))
            pen.closePath()

        self.assertEqual(
            " *********"
            "   **    *"
            "     **  *"
            "       * *"
            "         *",
            self.render(draw_triangles, even_odd=True))

        self.assertEqual(
            " *********"
            "   *******"
            "     *****"
            "       ***"
            "         *",
            self.render(draw_triangles, even_odd=False))

    def test_curve(self):
        def draw_curves(pen):
            pen.moveTo((0,0)); pen.curveTo((9,1), (9,4), (0,5))
            pen.moveTo((10,5)); pen.curveTo((1,4), (1,1), (10,0))
            pen.closePath()

        self.assertEqual(
            "***    ***"
            "****  ****"
            "***    ***"
            "****  ****"
            "***    ***",
            self.render(draw_curves, even_odd=True))

        self.assertEqual(
            "***    ***"
            "**********"
            "**********"
            "**********"
            "***    ***",
            self.render(draw_curves, even_odd=False))

    def test_qCurve(self):
        def draw_qCurves(pen):
            pen.moveTo((0,0)); pen.qCurveTo((15,2), (0,5))
            pen.moveTo((10,5)); pen.qCurveTo((-5,3), (10,0))
            pen.closePath()

        self.assertEqual(
            "***     **"
            "****   ***"
            "***    ***"
            "***   ****"
            "**     ***",
            self.render(draw_qCurves, even_odd=True))

        self.assertEqual(
            "***     **"
            "**********"
            "**********"
            "**********"
            "**     ***",
            self.render(draw_qCurves, even_odd=False))

    @staticmethod
    def render(draw_function, even_odd):
        result = StringIO()
        for y in range(5):
            for x in range(10):
                pen = PointInsidePen(None, (x + 0.5, y + 0.5), even_odd)
                draw_function(pen)
                if pen.getResult():
                    result.write(b"*")
                else:
                    result.write(b" ")
        return tounicode(result.getvalue())


if __name__ == "__main__":
    unittest.main()

