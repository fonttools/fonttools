from fontTools.misc.py23 import *
from fontTools.misc.loggingTools import CapturingLogHandler
import unittest

from fontTools.pens.basePen import AbstractPen
from fontTools.pens.pointPen import AbstractPointPen, PointToSegmentPen, \
    SegmentToPointPen, GuessSmoothPointPen, ReverseContourPointPen


class _TestSegmentPen(AbstractPen):

    def __init__(self):
        self._commands = []

    def __repr__(self):
        return " ".join(self._commands)

    def moveTo(self, pt):
        self._commands.append("%s %s moveto" % (pt[0], pt[1]))

    def lineTo(self, pt):
        self._commands.append("%s %s lineto" % (pt[0], pt[1]))

    def curveTo(self, *pts):
        pts = ["%s %s" % pt for pt in pts]
        self._commands.append("%s curveto" % " ".join(pts))

    def qCurveTo(self, *pts):
        pts = ["%s %s" % pt if pt is not None else "None" for pt in pts]
        self._commands.append("%s qcurveto" % " ".join(pts))

    def closePath(self):
        self._commands.append("closepath")

    def endPath(self):
        self._commands.append("endpath")

    def addComponent(self, glyphName, transformation):
        self._commands.append("'%s' %s addcomponent" % (glyphName, transformation))


def _reprKwargs(kwargs):
    items = []
    for key in sorted(kwargs):
        value = kwargs[key]
        if isinstance(value, basestring):
            items.append("%s='%s'" % (key, value))
        else:
            items.append("%s=%s" % (key, value))
    return items


class _TestPointPen(AbstractPointPen):

    def __init__(self):
        self._commands = []

    def __repr__(self):
        return " ".join(self._commands)

    def beginPath(self, identifier=None, **kwargs):
        items = []
        if identifier is not None:
            items.append("identifier='%s'" % identifier)
        items.extend(_reprKwargs(kwargs))
        self._commands.append("beginPath(%s)" % ", ".join(items))

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 identifier=None, **kwargs):
        items = ["%s" % (pt,)]
        if segmentType is not None:
            items.append("segmentType='%s'" % segmentType)
        if smooth:
            items.append("smooth=True")
        if name is not None:
            items.append("name='%s'" % name)
        if identifier is not None:
            items.append("identifier='%s'" % identifier)
        items.extend(_reprKwargs(kwargs))
        self._commands.append("addPoint(%s)" % ", ".join(items))

    def endPath(self):
        self._commands.append("endPath()")

    def addComponent(self, glyphName, transform, identifier=None, **kwargs):
        items = ["'%s'" % glyphName, "%s" % transform]
        if identifier is not None:
            items.append("identifier='%s'" % identifier)
        items.extend(_reprKwargs(kwargs))
        self._commands.append("addComponent(%s)" % ", ".join(items))


class PointToSegmentPenTest(unittest.TestCase):

    def test_open(self):
        pen = _TestSegmentPen()
        ppen = PointToSegmentPen(pen)
        ppen.beginPath()
        ppen.addPoint((10, 10), "move")
        ppen.addPoint((10, 20), "line")
        ppen.endPath()
        self.assertEqual("10 10 moveto 10 20 lineto endpath", repr(pen))

    def test_closed(self):
        pen = _TestSegmentPen()
        ppen = PointToSegmentPen(pen)
        ppen.beginPath()
        ppen.addPoint((10, 10), "line")
        ppen.addPoint((10, 20), "line")
        ppen.addPoint((20, 20), "line")
        ppen.endPath()
        self.assertEqual("10 10 moveto 10 20 lineto 20 20 lineto closepath", repr(pen))

    def test_cubic(self):
        pen = _TestSegmentPen()
        ppen = PointToSegmentPen(pen)
        ppen.beginPath()
        ppen.addPoint((10, 10), "line")
        ppen.addPoint((10, 20))
        ppen.addPoint((20, 20))
        ppen.addPoint((20, 40), "curve")
        ppen.endPath()
        self.assertEqual("10 10 moveto 10 20 20 20 20 40 curveto closepath", repr(pen))

    def test_quad(self):
        pen = _TestSegmentPen()
        ppen = PointToSegmentPen(pen)
        ppen.beginPath(identifier='foo')
        ppen.addPoint((10, 10), "line")
        ppen.addPoint((10, 40))
        ppen.addPoint((40, 40))
        ppen.addPoint((10, 40), "qcurve")
        ppen.endPath()
        self.assertEqual("10 10 moveto 10 40 40 40 10 40 qcurveto closepath", repr(pen))

    def test_quad_onlyOffCurvePoints(self):
        pen = _TestSegmentPen()
        ppen = PointToSegmentPen(pen)
        ppen.beginPath()
        ppen.addPoint((10, 10))
        ppen.addPoint((10, 40))
        ppen.addPoint((40, 40))
        ppen.endPath()
        self.assertEqual("10 10 10 40 40 40 None qcurveto closepath", repr(pen))

    def test_roundTrip1(self):
        tpen = _TestPointPen()
        ppen = PointToSegmentPen(SegmentToPointPen(tpen))
        ppen.beginPath()
        ppen.addPoint((10, 10), "line")
        ppen.addPoint((10, 20))
        ppen.addPoint((20, 20))
        ppen.addPoint((20, 40), "curve")
        ppen.endPath()
        self.assertEqual("beginPath() addPoint((10, 10), segmentType='line') addPoint((10, 20)) "
                         "addPoint((20, 20)) addPoint((20, 40), segmentType='curve') endPath()",
                         repr(tpen))

    def test_closed_outputImpliedClosingLine(self):
        tpen = _TestSegmentPen()
        ppen = PointToSegmentPen(tpen, outputImpliedClosingLine=True)
        ppen.beginPath()
        ppen.addPoint((10, 10), "line")
        ppen.addPoint((10, 20), "line")
        ppen.addPoint((20, 20), "line")
        ppen.endPath()
        self.assertEqual(
            "10 10 moveto "
            "10 20 lineto "
            "20 20 lineto "
            "10 10 lineto "  # explicit closing line
            "closepath",
            repr(tpen)
        )

    def test_closed_line_overlapping_start_end_points(self):
        # Test case from https://github.com/googlefonts/fontmake/issues/572.
        tpen = _TestSegmentPen()
        ppen = PointToSegmentPen(tpen, outputImpliedClosingLine=False)
        # The last oncurve point on this closed contour is a "line" segment and has
        # same coordinates as the starting point.
        ppen.beginPath()
        ppen.addPoint((0, 651), segmentType="line")
        ppen.addPoint((0, 101), segmentType="line")
        ppen.addPoint((0, 101), segmentType="line")
        ppen.addPoint((0, 651), segmentType="line")
        ppen.endPath()
        # Check that we always output an explicit 'lineTo' segment at the end,
        # regardless of the value of 'outputImpliedClosingLine', to disambiguate
        # the duplicate point from the implied closing line.
        self.assertEqual(
            "0 651 moveto "
            "0 101 lineto "
            "0 101 lineto "
            "0 651 lineto "
            "0 651 lineto "
            "closepath",
            repr(tpen)
        )

    def test_roundTrip2(self):
        tpen = _TestPointPen()
        ppen = PointToSegmentPen(SegmentToPointPen(tpen))
        ppen.beginPath()
        ppen.addPoint((0, 651), segmentType="line")
        ppen.addPoint((0, 101), segmentType="line")
        ppen.addPoint((0, 101), segmentType="line")
        ppen.addPoint((0, 651), segmentType="line")
        ppen.endPath()
        self.assertEqual(
            "beginPath() "
            "addPoint((0, 651), segmentType='line') "
            "addPoint((0, 101), segmentType='line') "
            "addPoint((0, 101), segmentType='line') "
            "addPoint((0, 651), segmentType='line') "
            "endPath()",
            repr(tpen)
        )


class TestSegmentToPointPen(unittest.TestCase):

    def test_move(self):
        tpen = _TestPointPen()
        pen = SegmentToPointPen(tpen)
        pen.moveTo((10, 10))
        pen.endPath()
        self.assertEqual("beginPath() addPoint((10, 10), segmentType='move') endPath()",
                         repr(tpen))

    def test_poly(self):
        tpen = _TestPointPen()
        pen = SegmentToPointPen(tpen)
        pen.moveTo((10, 10))
        pen.lineTo((10, 20))
        pen.lineTo((20, 20))
        pen.closePath()
        self.assertEqual("beginPath() addPoint((10, 10), segmentType='line') "
                         "addPoint((10, 20), segmentType='line') "
                         "addPoint((20, 20), segmentType='line') endPath()",
                         repr(tpen))

    def test_cubic(self):
        tpen = _TestPointPen()
        pen = SegmentToPointPen(tpen)
        pen.moveTo((10, 10))
        pen.curveTo((10, 20), (20, 20), (20, 10))
        pen.closePath()
        self.assertEqual("beginPath() addPoint((10, 10), segmentType='line') "
                         "addPoint((10, 20)) addPoint((20, 20)) addPoint((20, 10), "
                         "segmentType='curve') endPath()", repr(tpen))

    def test_quad(self):
        tpen = _TestPointPen()
        pen = SegmentToPointPen(tpen)
        pen.moveTo((10, 10))
        pen.qCurveTo((10, 20), (20, 20), (20, 10))
        pen.closePath()
        self.assertEqual("beginPath() addPoint((10, 10), segmentType='line') "
                         "addPoint((10, 20)) addPoint((20, 20)) "
                         "addPoint((20, 10), segmentType=qcurve) endPath()",
                         repr(tpen))

    def test_quad(self):
        tpen = _TestPointPen()
        pen = SegmentToPointPen(tpen)
        pen.qCurveTo((10, 20), (20, 20), (20, 10), (10, 10), None)
        pen.closePath()
        self.assertEqual("beginPath() addPoint((10, 20)) addPoint((20, 20)) "
                         "addPoint((20, 10)) addPoint((10, 10)) endPath()",
                         repr(tpen))

    def test_roundTrip1(self):
        spen = _TestSegmentPen()
        pen = SegmentToPointPen(PointToSegmentPen(spen))
        pen.moveTo((10, 10))
        pen.lineTo((10, 20))
        pen.lineTo((20, 20))
        pen.closePath()
        self.assertEqual("10 10 moveto 10 20 lineto 20 20 lineto closepath", repr(spen))

    def test_roundTrip2(self):
        spen = _TestSegmentPen()
        pen = SegmentToPointPen(PointToSegmentPen(spen))
        pen.qCurveTo((10, 20), (20, 20), (20, 10), (10, 10), None)
        pen.closePath()
        pen.addComponent('base', [1, 0, 0, 1, 0, 0])
        self.assertEqual("10 20 20 20 20 10 10 10 None qcurveto closepath "
                         "'base' [1, 0, 0, 1, 0, 0] addcomponent",
                         repr(spen))


class TestGuessSmoothPointPen(unittest.TestCase):

    def test_guessSmooth_exact(self):
        tpen = _TestPointPen()
        pen = GuessSmoothPointPen(tpen)
        pen.beginPath(identifier="foo")
        pen.addPoint((0, 100), segmentType="curve")
        pen.addPoint((0, 200))
        pen.addPoint((400, 200), identifier='bar')
        pen.addPoint((400, 100), segmentType="curve")
        pen.addPoint((400, 0))
        pen.addPoint((0, 0))
        pen.endPath()
        self.assertEqual("beginPath(identifier='foo') "
                         "addPoint((0, 100), segmentType='curve', smooth=True) "
                         "addPoint((0, 200)) addPoint((400, 200), identifier='bar') "
                         "addPoint((400, 100), segmentType='curve', smooth=True) "
                         "addPoint((400, 0)) addPoint((0, 0)) endPath()",
                         repr(tpen))

    def test_guessSmooth_almost(self):
        tpen = _TestPointPen()
        pen = GuessSmoothPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 100), segmentType="curve")
        pen.addPoint((1, 200))
        pen.addPoint((395, 200))
        pen.addPoint((400, 100), segmentType="curve")
        pen.addPoint((400, 0))
        pen.addPoint((0, 0))
        pen.endPath()
        self.assertEqual("beginPath() addPoint((0, 100), segmentType='curve', smooth=True) "
                         "addPoint((1, 200)) addPoint((395, 200)) "
                         "addPoint((400, 100), segmentType='curve', smooth=True) "
                         "addPoint((400, 0)) addPoint((0, 0)) endPath()",
                         repr(tpen))

    def test_guessSmooth_tangent(self):
        tpen = _TestPointPen()
        pen = GuessSmoothPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="move")
        pen.addPoint((0, 100), segmentType="line")
        pen.addPoint((3, 200))
        pen.addPoint((300, 200))
        pen.addPoint((400, 200), segmentType="curve")
        pen.endPath()
        self.assertEqual("beginPath() addPoint((0, 0), segmentType='move') "
                         "addPoint((0, 100), segmentType='line', smooth=True) "
                         "addPoint((3, 200)) addPoint((300, 200)) "
                         "addPoint((400, 200), segmentType='curve') endPath()",
                         repr(tpen))

class TestReverseContourPointPen(unittest.TestCase):

    def test_singlePoint(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="move")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((0, 0), segmentType='move') "
                         "endPath()",
                         repr(tpen))

    def test_line(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="move")
        pen.addPoint((0, 100), segmentType="line")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((0, 100), segmentType='move') "
                         "addPoint((0, 0), segmentType='line') "
                         "endPath()",
                         repr(tpen))

    def test_triangle(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="line")
        pen.addPoint((0, 100), segmentType="line")
        pen.addPoint((100, 100), segmentType="line")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((0, 0), segmentType='line') "
                         "addPoint((100, 100), segmentType='line') "
                         "addPoint((0, 100), segmentType='line') "
                         "endPath()",
                         repr(tpen))

    def test_cubicOpen(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="move")
        pen.addPoint((0, 100))
        pen.addPoint((100, 200))
        pen.addPoint((200, 200), segmentType="curve")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((200, 200), segmentType='move') "
                         "addPoint((100, 200)) "
                         "addPoint((0, 100)) "
                         "addPoint((0, 0), segmentType='curve') "
                         "endPath()",
                         repr(tpen))

    def test_quadOpen(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="move")
        pen.addPoint((0, 100))
        pen.addPoint((100, 200))
        pen.addPoint((200, 200), segmentType="qcurve")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((200, 200), segmentType='move') "
                         "addPoint((100, 200)) "
                         "addPoint((0, 100)) "
                         "addPoint((0, 0), segmentType='qcurve') "
                         "endPath()",
                         repr(tpen))

    def test_cubicClosed(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 0), segmentType="line")
        pen.addPoint((0, 100))
        pen.addPoint((100, 200))
        pen.addPoint((200, 200), segmentType="curve")
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((0, 0), segmentType='curve') "
                         "addPoint((200, 200), segmentType='line') "
                         "addPoint((100, 200)) "
                         "addPoint((0, 100)) "
                         "endPath()",
                         repr(tpen))

    def test_quadClosedOffCurveStart(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((100, 200))
        pen.addPoint((200, 200), segmentType="qcurve")
        pen.addPoint((0, 0), segmentType="line")
        pen.addPoint((0, 100))
        pen.endPath()
        self.assertEqual("beginPath() "
                         "addPoint((100, 200)) "
                         "addPoint((0, 100)) "
                         "addPoint((0, 0), segmentType='qcurve') "
                         "addPoint((200, 200), segmentType='line') "
                         "endPath()",
                         repr(tpen))

    def test_quadNoOnCurve(self):
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath(identifier='bar')
        pen.addPoint((0, 0))
        pen.addPoint((0, 100), identifier='foo', arbitrary='foo')
        pen.addPoint((100, 200), arbitrary=123)
        pen.addPoint((200, 200))
        pen.endPath()
        pen.addComponent("base", [1, 0, 0, 1, 0, 0], identifier='foo')
        self.assertEqual("beginPath(identifier='bar') "
                         "addPoint((0, 0)) "
                         "addPoint((200, 200)) "
                         "addPoint((100, 200), arbitrary=123) "
                         "addPoint((0, 100), identifier='foo', arbitrary='foo') "
                         "endPath() "
                         "addComponent('base', [1, 0, 0, 1, 0, 0], identifier='foo')",
                         repr(tpen))

    def test_closed_line_overlapping_start_end_points(self):
        # Test case from https://github.com/googlefonts/fontmake/issues/572
        tpen = _TestPointPen()
        pen = ReverseContourPointPen(tpen)
        pen.beginPath()
        pen.addPoint((0, 651), segmentType="line")
        pen.addPoint((0, 101), segmentType="line")
        pen.addPoint((0, 101), segmentType="line")
        pen.addPoint((0, 651), segmentType="line")
        pen.endPath()
        self.assertEqual(
            "beginPath() "
            "addPoint((0, 651), segmentType='line') "
            "addPoint((0, 651), segmentType='line') "
            "addPoint((0, 101), segmentType='line') "
            "addPoint((0, 101), segmentType='line') "
            "endPath()",
            repr(tpen)
        )
