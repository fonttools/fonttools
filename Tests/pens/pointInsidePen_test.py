from io import StringIO
from fontTools.pens.pointInsidePen import PointInsidePen
import unittest


class PointInsidePenTest(unittest.TestCase):
    def test_line(self):
        def draw_triangles(pen):
            pen.moveTo((0, 0))
            pen.lineTo((10, 5))
            pen.lineTo((10, 0))
            pen.moveTo((9, 1))
            pen.lineTo((4, 1))
            pen.lineTo((9, 4))
            pen.closePath()

        self.assertEqual(
            " *********" "   **    *" "     **  *" "       * *" "         *",
            self.render(draw_triangles, even_odd=True),
        )

        self.assertEqual(
            " *********" "   *******" "     *****" "       ***" "         *",
            self.render(draw_triangles, even_odd=False),
        )

    def test_curve(self):
        def draw_curves(pen):
            pen.moveTo((0, 0))
            pen.curveTo((9, 1), (9, 4), (0, 5))
            pen.moveTo((10, 5))
            pen.curveTo((1, 4), (1, 1), (10, 0))
            pen.closePath()

        self.assertEqual(
            "***    ***" "****  ****" "***    ***" "****  ****" "***    ***",
            self.render(draw_curves, even_odd=True),
        )

        self.assertEqual(
            "***    ***" "**********" "**********" "**********" "***    ***",
            self.render(draw_curves, even_odd=False),
        )

    def test_qCurve(self):
        def draw_qCurves(pen):
            pen.moveTo((0, 0))
            pen.qCurveTo((15, 2), (0, 5))
            pen.moveTo((10, 5))
            pen.qCurveTo((-5, 3), (10, 0))
            pen.closePath()

        self.assertEqual(
            "***     **" "****   ***" "***    ***" "***   ****" "**     ***",
            self.render(draw_qCurves, even_odd=True),
        )

        self.assertEqual(
            "***     **" "**********" "**********" "**********" "**     ***",
            self.render(draw_qCurves, even_odd=False),
        )

    @staticmethod
    def render(draw_function, even_odd):
        result = StringIO()
        for y in range(5):
            for x in range(10):
                pen = PointInsidePen(None, (x + 0.5, y + 0.5), even_odd)
                draw_function(pen)
                if pen.getResult():
                    result.write("*")
                else:
                    result.write(" ")
        return result.getvalue()

    def test_contour_no_solutions(self):
        def draw_contour(pen):
            pen.moveTo((969, 230))
            pen.curveTo((825, 348), (715, 184), (614, 202))
            pen.lineTo((614, 160))
            pen.lineTo((969, 160))
            pen.closePath()

        piPen = PointInsidePen(None, (750, 295))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)
        self.assertEqual(piPen.getResult(), False)

        piPen = PointInsidePen(None, (835, 190))  # this point is inside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 1)
        self.assertEqual(piPen.getResult(), True)

    def test_contour_square_closed(self):
        def draw_contour(pen):
            pen.moveTo((100, 100))
            pen.lineTo((-100, 100))
            pen.lineTo((-100, -100))
            pen.lineTo((100, -100))
            pen.closePath()

        piPen = PointInsidePen(None, (0, 0))  # this point is inside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 1)
        self.assertEqual(piPen.getResult(), True)

    def test_contour_square_opened(self):
        def draw_contour(pen):
            pen.moveTo((100, 100))
            pen.lineTo((-100, 100))
            pen.lineTo((-100, -100))
            pen.lineTo((100, -100))
            # contour not explicitly closed

        piPen = PointInsidePen(None, (0, 0))  # this point is inside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 1)
        self.assertEqual(piPen.getResult(), True)

    def test_contour_circle(self):
        def draw_contour(pen):
            pen.moveTo((0, 100))
            pen.curveTo((-55, 100), (-100, 55), (-100, 0))
            pen.curveTo((-100, -55), (-55, -100), (0, -100))
            pen.curveTo((55, -100), (100, -55), (100, 0))
            pen.curveTo((100, 55), (55, 100), (0, 100))

        piPen = PointInsidePen(None, (50, 50))  # this point is inside
        draw_contour(piPen)
        self.assertEqual(piPen.getResult(), True)

        piPen = PointInsidePen(None, (50, -50))  # this point is inside
        draw_contour(piPen)
        self.assertEqual(piPen.getResult(), True)

    def test_contour_diamond(self):
        def draw_contour(pen):
            pen.moveTo((0, 100))
            pen.lineTo((100, 0))
            pen.lineTo((0, -100))
            pen.lineTo((-100, 0))
            pen.closePath()

        piPen = PointInsidePen(None, (-200, 0))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

        piPen = PointInsidePen(None, (-200, 100))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

        piPen = PointInsidePen(None, (-200, -100))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

        piPen = PointInsidePen(None, (-200, 50))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

    def test_contour_integers(self):
        def draw_contour(pen):
            pen.moveTo((728, 697))
            pen.lineTo((504, 699))
            pen.curveTo((487, 719), (508, 783), (556, 783))
            pen.lineTo((718, 783))
            pen.curveTo((739, 783), (749, 712), (728, 697))
            pen.closePath()

        piPen = PointInsidePen(None, (416, 783))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

    def test_contour_decimals(self):
        def draw_contour(pen):
            pen.moveTo((727.546875, 697.0))
            pen.lineTo((504.375, 698.515625))
            pen.curveTo(
                (487.328125, 719.359375),
                (507.84375, 783.140625),
                (555.796875, 783.140625),
            )
            pen.lineTo((717.96875, 783.140625))
            pen.curveTo(
                (738.890625, 783.140625), (748.796875, 711.5), (727.546875, 697.0)
            )
            pen.closePath()

        piPen = PointInsidePen(None, (416.625, 783.140625))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

    def test_contour2_integers(self):
        def draw_contour(pen):
            pen.moveTo((51, 22))
            pen.lineTo((51, 74))
            pen.lineTo((83, 50))
            pen.curveTo((83, 49), (82, 48), (82, 47))
            pen.closePath()

        piPen = PointInsidePen(None, (21, 50))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)

    def test_contour2_decimals(self):
        def draw_contour(pen):
            pen.moveTo((51.25, 21.859375))
            pen.lineTo((51.25, 73.828125))
            pen.lineTo((82.5, 50.0))
            pen.curveTo((82.5, 49.09375), (82.265625, 48.265625), (82.234375, 47.375))
            pen.closePath()

        piPen = PointInsidePen(None, (21.25, 50.0))  # this point is outside
        draw_contour(piPen)
        self.assertEqual(piPen.getWinding(), 0)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
