import unittest

try:
    from fontTools.pens.cocoaPen import CocoaPen
    from AppKit import NSBezierPathElementMoveTo, NSBezierPathElementLineTo
    from AppKit import NSBezierPathElementCurveTo, NSBezierPathElementClosePath

    PATH_ELEMENTS = {
        # NSBezierPathElement key      desc
        NSBezierPathElementMoveTo: "moveto",
        NSBezierPathElementLineTo: "lineto",
        NSBezierPathElementCurveTo: "curveto",
        NSBezierPathElementClosePath: "close",
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


def cocoaPathToString(path):
    num_elements = path.elementCount()
    output = []
    for i in range(num_elements - 1):
        elem_type, elem_points = path.elementAtIndex_associatedPoints_(i)
        elem_type = PATH_ELEMENTS[elem_type]
        path_points = " ".join([f"{p.x} {p.y}" for p in elem_points])
        output.append(f"{elem_type} {path_points}")
    return " ".join(output)


@unittest.skipUnless(PYOBJC_AVAILABLE, "pyobjc not installed")
class CocoaPenTest(unittest.TestCase):
    def test_draw(self):
        pen = CocoaPen(None)
        draw(pen)
        self.assertEqual(
            "moveto 50.0 0.0 lineto 50.0 500.0 lineto 200.0 500.0 curveto 350.0 500.0 450.0 400.0 450.0 250.0 curveto 450.0 100.0 350.0 0.0 200.0 0.0 close ",
            cocoaPathToString(pen.path),
        )

    def test_empty(self):
        pen = CocoaPen(None)
        self.assertEqual("", cocoaPathToString(pen.path))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
