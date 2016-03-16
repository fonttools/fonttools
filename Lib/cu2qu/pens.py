from __future__ import print_function, division, absolute_import
from cu2qu import curve_to_quadratic
from fontTools.pens.basePen import AbstractPen, decomposeSuperBezierSegment

try:
    from ufoLib.pointPen import AbstractPointPen, BasePointToSegmentPen
    from ufoLib.pointPen import PointToSegmentPen, SegmentToPointPen
except ImportError:
    from robofab.pens.pointPen import AbstractPointPen, BasePointToSegmentPen
    from robofab.pens.adapterPens import PointToSegmentPen, SegmentToPointPen


class Cu2QuPen(AbstractPen):
    """ A filter pen to convert cubic bezier curves to quadratic b-splines
    using the FontTools SegmentPen protocol.

    other_pen: another SegmentPen used to draw the transformed outline.
    max_err: maximum approximation error in font units.
    reverse_direction: flip the contours' direction but keep starting point.
    stats: a dictionary counting the point numbers of quadratic segments.
    ignore_single_points: don't emit contours containing only a single point.
    """

    def __init__(self, other_pen, max_err, reverse_direction=False,
                 stats=None, ignore_single_points=False):
        if reverse_direction:
            self.pen = ReverseContourPen(other_pen)
        else:
            self.pen = other_pen
        self.max_err = max_err
        self.stats = stats
        self.ignore_single_points = ignore_single_points
        self.start_pt = None
        self.current_pt = None

    def _add_moveTo(self):
        if self.start_pt is not None:
            self.pen.moveTo(self.start_pt)
            self.start_pt = None

    def moveTo(self, pt):
        assert self.current_pt is None
        self.start_pt = self.current_pt = pt
        if not self.ignore_single_points:
            self._add_moveTo()

    def lineTo(self, pt):
        assert self.current_pt is not None
        self._add_moveTo()
        self.pen.lineTo(pt)
        self.current_pt = pt

    def qCurveTo(self, *points):
        assert self.current_pt is not None
        n = len(points)
        if n == 1:
            self.lineTo(points[0])
        elif n > 1:
            self._add_moveTo()
            self.pen.qCurveTo(*points)
            self.current_pt = points[-1]
        else:
            raise AssertionError("illegal qcurve segment point count: %d" % n)

    def _curve_to_quadratic(self, pt1, pt2, pt3):
        assert self.current_pt is not None
        curve = (self.current_pt, pt1, pt2, pt3)
        quadratic, _ = curve_to_quadratic(curve, self.max_err)
        if self.stats is not None:
            n = str(len(quadratic))
            self.stats[n] = self.stats.get(n, 0) + 1
        self.qCurveTo(*quadratic[1:])

    def curveTo(self, *points):
        n = len(points)
        if n == 3:
            # this is the most common case, so we special-case it
            self._curve_to_quadratic(*points)
        elif n > 3:
            for segment in decomposeSuperBezierSegment(points):
                self._curve_to_quadratic(*segment)
        elif n == 2:
            self.qCurveTo(*points)
        elif n == 1:
            self.lineTo(points[0])
        else:
            raise AssertionError("illegal curve segment point count: %d" % n)

    def closePath(self):
        assert self.current_pt is not None
        if self.start_pt is None:
            # if 'start_pt' is _not_ None, we are ignoring single-point paths
            self.pen.closePath()
        self.current_pt = self.start_pt = None

    def endPath(self):
        assert self.current_pt is not None
        if self.start_pt is None:
            self.pen.endPath()
        self.current_pt = self.start_pt = None

    def addComponent(self, glyphName, transformation):
        assert self.current_pt is None
        self.pen.addComponent(glyphName, transformation)


class Cu2QuPointPen(BasePointToSegmentPen):
    """ A filter pen to convert cubic bezier curves to quadratic b-splines
    using the RoboFab PointPen protocol.

    other_point_pen: another PointPen used to draw the transformed outline.
    max_err: maximum approximation error in font units.
    reverse_direction: reverse the winding direction of all contours.
    stats: a dictionary counting the point numbers of quadratic segments.
    """

    def __init__(self, other_point_pen, max_err, reverse_direction=False,
                 stats=None):
        super(Cu2QuPointPen, self).__init__()
        if reverse_direction:
            self.pen = ReverseContourPointPen(other_point_pen)
        else:
            self.pen = other_point_pen
        self.max_err = max_err
        self.stats = stats

    def _flushContour(self, segments):
        assert len(segments) >= 1
        closed = segments[0][0] != "move"
        new_segments = []
        prev_points = segments[-1][1]
        prev_on_curve = prev_points[-1][0]
        for segment_type, points in segments:
            if segment_type == 'curve':
                # XXX do we actually need to decomposeSuperBezierSegment?
                assert len(points) == 3
                on_curve, smooth, name, kwargs = points[-1]
                bcp1, bcp2 = points[0][0], points[1][0]
                cubic = [prev_on_curve, bcp1, bcp2, on_curve]
                quadratic, _ = curve_to_quadratic(cubic, self.max_err)
                if self.stats is not None:
                    n = str(len(quadratic))
                    self.stats[n] = self.stats.get(n, 0) + 1
                new_points = [(pt, None, None, {}) for pt in quadratic[1:-1]]
                new_points.append((on_curve, smooth, name, kwargs))
                new_segments.append(["qcurve", new_points])
            else:
                new_segments.append([segment_type, points])
            prev_on_curve = points[-1][0]
        if closed:
            # restore the original starting point
            new_segments = new_segments[-1:] + new_segments[:-1]
        self._drawPoints(new_segments)

    def _drawPoints(self, segments):
        pen = self.pen
        pen.beginPath()
        for segment_type, points in segments:
            if segment_type in ("move", "line"):
                assert len(points) == 1, (
                    "illegal line segment point count: %d" % len(points))
                pt, smooth, name, kwargs = points[0]
                pen.addPoint(pt, segment_type, smooth, name, **kwargs)
            elif segment_type == "qcurve":
                assert len(points) >= 2, (
                    "illegal qcurve segment point count: %d" % len(points))
                for (pt, smooth, name, kwargs) in points[:-1]:
                    pen.addPoint(pt, None, smooth, name, **kwargs)
                pt, smooth, name, kwargs = points[-1]
                pen.addPoint(pt, segment_type, smooth, name, **kwargs)
            else:
                # 'curve' segments must have been converted to 'qcurve' by now
                raise AssertionError(
                    "unexpected segment type: %r" % segment_type)
        pen.endPath()

    def addComponent(self, baseGlyphName, transformation):
        assert self.currentPath is None
        self.pen.addComponent(baseGlyphName, transformation)


class ReverseContourPointPen(AbstractPointPen):

    """This is a PointPen that passes outline data to another PointPen, but
    reversing the winding direction of all contours. Components are simply
    passed through unchanged.

    Closed contours are reversed in such a way that the first point remains
    the first point.

    (Copied from robofab.pens.reverseContourPointPen)

    TODO(anthrotype) Move this to future "penBox" package?
    """

    def __init__(self, outputPointPen):
        self.pen = outputPointPen
        # a place to store the points for the current sub path
        self.currentContour = None

    def _flushContour(self):
        pen = self.pen
        contour = self.currentContour
        if not contour:
            pen.beginPath()
            pen.endPath()
            return

        closed = contour[0][1] != "move"
        if not closed:
            lastSegmentType = "move"
        else:
            # Remove the first point and insert it at the end. When
            # the list of points gets reversed, this point will then
            # again be at the start. In other words, the following
            # will hold:
            #   for N in range(len(originalContour)):
            #       originalContour[N] == reversedContour[-N]
            contour.append(contour.pop(0))
            # Find the first on-curve point.
            firstOnCurve = None
            for i in range(len(contour)):
                if contour[i][1] is not None:
                    firstOnCurve = i
                    break
            if firstOnCurve is None:
                # There are no on-curve points, be basically have to
                # do nothing but contour.reverse().
                lastSegmentType = None
            else:
                lastSegmentType = contour[firstOnCurve][1]

        contour.reverse()
        if not closed:
            # Open paths must start with a move, so we simply dump
            # all off-curve points leading up to the first on-curve.
            while contour[0][1] is None:
                contour.pop(0)
        pen.beginPath()
        for pt, nextSegmentType, smooth, name in contour:
            if nextSegmentType is not None:
                segmentType = lastSegmentType
                lastSegmentType = nextSegmentType
            else:
                segmentType = None
            pen.addPoint(pt, segmentType=segmentType, smooth=smooth, name=name)
        pen.endPath()

    def beginPath(self):
        assert self.currentContour is None
        self.currentContour = []

    def endPath(self):
        assert self.currentContour is not None
        self._flushContour()
        self.currentContour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        self.currentContour.append((pt, segmentType, smooth, name))

    def addComponent(self, glyphName, transform):
        assert self.currentContour is None
        self.pen.addComponent(glyphName, transform)


class ReverseContourPen(SegmentToPointPen):
    """ Same as 'ReverseContourPointPen' but using the SegmentPen protocol. """

    def __init__(self, other_pen):
        adapter_point_pen = PointToSegmentPen(other_pen)
        reverse_point_pen = ReverseContourPointPen(adapter_point_pen)
        super(ReverseContourPen, self).__init__(reverse_point_pen)
