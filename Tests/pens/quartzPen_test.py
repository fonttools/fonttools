import unittest

try:
    from fontTools.pens.quartzPen import QuartzPen

    from Quartz.CoreGraphics import CGPathApply
    from Quartz.CoreGraphics import kCGPathElementMoveToPoint
    from Quartz.CoreGraphics import kCGPathElementAddLineToPoint
    from Quartz.CoreGraphics import kCGPathElementAddQuadCurveToPoint
    from Quartz.CoreGraphics import kCGPathElementAddCurveToPoint
    from Quartz.CoreGraphics import kCGPathElementCloseSubpath

    PATH_ELEMENTS = {
        # CG constant key                    desc       num_points
        kCGPathElementMoveToPoint: ("moveto", 1),
        kCGPathElementAddLineToPoint: ("lineto", 1),
        kCGPathElementAddCurveToPoint: ("curveto", 3),
        kCGPathElementAddQuadCurveToPoint: ("qcurveto", 2),
        kCGPathElementCloseSubpath: ("close", 0),
    }

    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False


def draw(pen):
    pen.moveTo((50, 0))
    pen.lineTo((50, 500))
    pen.lineTo((200, 500))
    pen.curveTo((350, 500), (450, 400), (450, 250))
    pen.curveTo((450, 100), (350, 0), (200, 0))
    pen.closePath()


def quartzPathApplier(elements, element):
    num_points = 0
    elem_type = None
    if element.type in PATH_ELEMENTS:
        num_points = PATH_ELEMENTS[element.type][1]
        elem_type = PATH_ELEMENTS[element.type][0]
    elements.append((elem_type, element.points.as_tuple(num_points)))


def quartzPathElements(path):
    elements = []
    CGPathApply(path, elements, quartzPathApplier)
    return elements


def quartzPathToString(path):
    elements = quartzPathElements(path)
    output = []
    for element in elements:
        elem_type, elem_points = element
        path_points = " ".join([f"{p.x} {p.y}" for p in elem_points])
        output.append(f"{elem_type} {path_points}")
    return " ".join(output)


@unittest.skipUnless(PYOBJC_AVAILABLE, "pyobjc not installed")
class QuartzPenTest(unittest.TestCase):
    def test_draw(self):
        pen = QuartzPen(None)
        draw(pen)
        self.assertEqual(
            "moveto 50.0 0.0 lineto 50.0 500.0 lineto 200.0 500.0 curveto 350.0 500.0 450.0 400.0 450.0 250.0 curveto 450.0 100.0 350.0 0.0 200.0 0.0 close ",
            quartzPathToString(pen.path),
        )

    def test_empty(self):
        pen = QuartzPen(None)
        self.assertEqual("", quartzPathToString(pen.path))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
