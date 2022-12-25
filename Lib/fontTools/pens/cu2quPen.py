# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations
from typing import Iterable, Sequence

from fontTools.cu2qu import curve_to_quadratic, curves_to_quadratic
from fontTools.pens.basePen import AbstractPen, decomposeSuperBezierSegment
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.pointPen import (
    AbstractPointPen,
    BasePointToSegmentPen,
    SegmentPoints,
    Segments,
)
from fontTools.pens.pointPen import ReverseContourPointPen
from fontTools.pens.typings import Point, Transformation


class Cu2QuPen(AbstractPen):
    """A filter pen to convert cubic bezier curves to quadratic b-splines
    using the FontTools SegmentPen protocol.

    Args:

        other_pen: another SegmentPen used to draw the transformed outline.
        max_err: maximum approximation error in font units. For optimal results,
            if you know the UPEM of the font, we recommend setting this to a
            value equal, or close to UPEM / 1000.
        reverse_direction: flip the contours' direction but keep starting point.
        stats: a dictionary counting the point numbers of quadratic segments.
        ignore_single_points: don't emit contours containing only a single point

    NOTE: The "ignore_single_points" argument is deprecated since v1.3.0,
    which dropped Robofab support. It's no longer needed to special-case
    UFO2-style anchors (aka "named points") when using ufoLib >= 2.0,
    as these are no longer drawn onto pens as single-point contours,
    but are handled separately as anchors.
    """

    def __init__(
        self,
        other_pen: AbstractPen,
        max_err: float,
        reverse_direction: bool = False,
        stats: dict[str, int] | None = None,
        ignore_single_points: bool = False,
    ) -> None:
        self.pen: AbstractPen
        if reverse_direction:
            self.pen = ReverseContourPen(other_pen)
        else:
            self.pen = other_pen
        self.max_err = max_err
        self.stats = stats
        if ignore_single_points:
            import warnings

            warnings.warn(
                "ignore_single_points is deprecated and "
                "will be removed in future versions",
                UserWarning,
                stacklevel=2,
            )
        self.ignore_single_points = ignore_single_points
        self.start_pt: Point | None = None
        self.current_pt: Point | None = None

    def _check_contour_is_open(self) -> None:
        if self.current_pt is None:
            raise AssertionError("moveTo is required")

    def _check_contour_is_closed(self) -> None:
        if self.current_pt is not None:
            raise AssertionError("closePath or endPath is required")

    def _add_moveTo(self) -> None:
        if self.start_pt is not None:
            self.pen.moveTo(self.start_pt)
            self.start_pt = None

    def moveTo(self, pt: Point) -> None:
        self._check_contour_is_closed()
        self.start_pt = self.current_pt = pt
        if not self.ignore_single_points:
            self._add_moveTo()

    def lineTo(self, pt: Point) -> None:
        self._check_contour_is_open()
        self._add_moveTo()
        self.pen.lineTo(pt)
        self.current_pt = pt

    def qCurveTo(self, *points: Point | None) -> None:
        self._check_contour_is_open()
        n = len(points)
        if n == 1:
            assert points[0] is not None
            self.lineTo(points[0])
        elif n > 1:
            self._add_moveTo()
            self.pen.qCurveTo(*points)
            self.current_pt = points[-1]
        else:
            raise AssertionError("illegal qcurve segment point count: %d" % n)

    def _curve_to_quadratic(self, pt1: Point, pt2: Point, pt3: Point) -> None:
        curve = (self.current_pt, pt1, pt2, pt3)
        quadratic = curve_to_quadratic(curve, self.max_err)
        if self.stats is not None:
            n = str(len(quadratic) - 2)
            self.stats[n] = self.stats.get(n, 0) + 1
        self.qCurveTo(*quadratic[1:])

    def curveTo(self, *points: Point) -> None:
        self._check_contour_is_open()
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

    def closePath(self) -> None:
        self._check_contour_is_open()
        if self.start_pt is None:
            # if 'start_pt' is _not_ None, we are ignoring single-point paths
            self.pen.closePath()
        self.current_pt = self.start_pt = None

    def endPath(self) -> None:
        self._check_contour_is_open()
        if self.start_pt is None:
            self.pen.endPath()
        self.current_pt = self.start_pt = None

    def addComponent(self, glyphName: str, transformation: Transformation) -> None:
        self._check_contour_is_closed()
        self.pen.addComponent(glyphName, transformation)


class Cu2QuPointPen(BasePointToSegmentPen):
    """A filter pen to convert cubic bezier curves to quadratic b-splines
    using the RoboFab PointPen protocol.

    Args:
        other_point_pen: another PointPen used to draw the transformed outline.
        max_err: maximum approximation error in font units. For optimal results,
            if you know the UPEM of the font, we recommend setting this to a
            value equal, or close to UPEM / 1000.
        reverse_direction: reverse the winding direction of all contours.
        stats: a dictionary counting the point numbers of quadratic segments.
    """

    def __init__(
        self,
        other_point_pen: AbstractPointPen,
        max_err: float,
        reverse_direction: bool = False,
        stats: dict[str, int] | None = None,
    ) -> None:
        BasePointToSegmentPen.__init__(self)
        self.pen: AbstractPointPen
        if reverse_direction:
            self.pen = ReverseContourPointPen(other_point_pen)
        else:
            self.pen = other_point_pen
        self.max_err = max_err
        self.stats = stats

    def _flushContour(self, segments: Segments) -> None:
        assert len(segments) >= 1
        closed = segments[0][0] != "move"
        new_segments: Segments = []
        prev_points = segments[-1][1]
        prev_on_curve = prev_points[-1][0]
        for segment_type, points in segments:
            if segment_type == "curve":
                for sub_points in self._split_super_bezier_segments(points):
                    on_curve, smooth, name, kwargs = sub_points[-1]
                    bcp1, bcp2 = sub_points[0][0], sub_points[1][0]
                    cubic = [prev_on_curve, bcp1, bcp2, on_curve]
                    quad = curve_to_quadratic(cubic, self.max_err)
                    if self.stats is not None:
                        n = str(len(quad) - 2)
                        self.stats[n] = self.stats.get(n, 0) + 1
                    new_points: SegmentPoints
                    new_points = [(pt, False, None, {}) for pt in quad[1:-1]]
                    new_points.append((on_curve, smooth, name, kwargs))
                    new_segments.append(("qcurve", new_points))
                    prev_on_curve = sub_points[-1][0]
            else:
                new_segments.append((segment_type, points))
                prev_on_curve = points[-1][0]
        if closed:
            # the BasePointToSegmentPen.endPath method that calls _flushContour
            # rotates the point list of closed contours so that they end with
            # the first on-curve point. We restore the original starting point.
            new_segments = new_segments[-1:] + new_segments[:-1]
        self._drawPoints(new_segments)

    def _split_super_bezier_segments(
        self, points: SegmentPoints
    ) -> list[SegmentPoints]:
        sub_segments = []
        # n is the number of control points
        n = len(points) - 1
        if n == 2:
            # a simple bezier curve segment
            sub_segments.append(points)
        elif n > 2:
            # a "super" bezier; decompose it
            on_curve, smooth, name, kwargs = points[-1]
            num_sub_segments = n - 1
            for i, sub_points in enumerate(
                decomposeSuperBezierSegment([pt for pt, _, _, _ in points])  # type: ignore
            ):
                new_segment: SegmentPoints = []
                for point in sub_points[:-1]:
                    new_segment.append((point, False, None, {}))
                if i == (num_sub_segments - 1):
                    # the last on-curve keeps its original attributes
                    new_segment.append((on_curve, smooth, name, kwargs))
                else:
                    # on-curves of sub-segments are always "smooth"
                    new_segment.append((sub_points[-1], True, None, {}))
                sub_segments.append(new_segment)
        else:
            raise AssertionError("expected 2 control points, found: %d" % n)
        return sub_segments

    def _drawPoints(self, segments: Segments) -> None:
        pen = self.pen
        pen.beginPath()
        last_offcurves = []
        for i, (segment_type, points) in enumerate(segments):
            if segment_type in ("move", "line"):
                assert len(points) == 1, "illegal line segment point count: %d" % len(
                    points
                )
                pt, smooth, name, kwargs = points[0]
                assert pt is not None
                assert kwargs is not None
                pen.addPoint(pt, segment_type, smooth, name, **kwargs)
            elif segment_type == "qcurve":
                assert len(points) >= 2, "illegal qcurve segment point count: %d" % len(
                    points
                )
                offcurves = points[:-1]
                if offcurves:
                    if i == 0:
                        # any off-curve points preceding the first on-curve
                        # will be appended at the end of the contour
                        last_offcurves = offcurves
                    else:
                        for (pt, smooth, name, kwargs) in offcurves:
                            assert pt is not None
                            assert kwargs is not None
                            pen.addPoint(pt, None, smooth, name, **kwargs)
                pt, smooth, name, kwargs = points[-1]
                if pt is None:
                    # special quadratic contour with no on-curve points:
                    # we need to skip the "None" point. See also the Pen
                    # protocol's qCurveTo() method and fontTools.pens.basePen
                    pass
                else:
                    assert pt is not None
                    assert kwargs is not None
                    pen.addPoint(pt, segment_type, smooth, name, **kwargs)
            else:
                # 'curve' segments must have been converted to 'qcurve' by now
                raise AssertionError("unexpected segment type: %r" % segment_type)
        for (pt, smooth, name, kwargs) in last_offcurves:
            assert pt is not None
            assert kwargs is not None
            pen.addPoint(pt, None, smooth, name, **kwargs)
        pen.endPath()

    def addComponent(self, baseGlyphName: str, transformation: Transformation) -> None:  # type: ignore
        assert self.currentPath is None
        self.pen.addComponent(baseGlyphName, transformation)


class Cu2QuMultiPen:
    """A filter multi-pen to convert cubic bezier curves to quadratic b-splines
    in a interpolation-compatible manner, using the FontTools SegmentPen protocol.

    Args:

        other_pens: list of SegmentPens used to draw the transformed outlines.
        max_err: maximum approximation error in font units. For optimal results,
            if you know the UPEM of the font, we recommend setting this to a
            value equal, or close to UPEM / 1000.
        reverse_direction: flip the contours' direction but keep starting point.

    This pen does not follow the normal SegmentPen protocol. Instead, its
    moveTo/lineTo/qCurveTo/curveTo methods take a list of tuples that are
    arguments that would normally be passed to a SegmentPen, one item for
    each of the pens in other_pens.
    """

    def __init__(
        self,
        other_pens: Sequence[AbstractPen],
        max_err: float,
        reverse_direction: bool = False,
    ) -> None:
        if reverse_direction:
            other_pens = [
                ReverseContourPen(pen, outputImpliedClosingLine=True)
                for pen in other_pens
            ]
        self.pens = other_pens
        self.max_err = max_err
        # NOTE: Let's ignore the special case that qCurves may contain None as the last
        # Point.
        self.start_pts: list[tuple[Point, ...]] | None = None
        self.current_pts: list[tuple[Point, ...]] | None = None

    def _check_contour_is_open(self) -> None:
        if self.current_pts is None:
            raise AssertionError("moveTo is required")

    def _check_contour_is_closed(self) -> None:
        if self.current_pts is not None:
            raise AssertionError("closePath or endPath is required")

    def _add_moveTo(self) -> None:
        if self.start_pts is not None:
            for pt, pen in zip(self.start_pts, self.pens):
                pen.moveTo(*pt)
            self.start_pts = None

    def moveTo(self, pts: list[tuple[Point, ...]]) -> None:
        self._check_contour_is_closed()
        self.start_pts = self.current_pts = pts
        self._add_moveTo()

    def lineTo(self, pts: list[tuple[Point, ...]]) -> None:
        self._check_contour_is_open()
        self._add_moveTo()
        for pt, pen in zip(pts, self.pens):
            pen.lineTo(*pt)
        self.current_pts = pts

    def qCurveTo(self, pointsList: list[tuple[Point | None, ...]]) -> None:
        self._check_contour_is_open()
        if len(pointsList[0]) == 1:
            self.lineTo([(points[0],) for points in pointsList])  # type: ignore
            return
        self._add_moveTo()
        current_pts = []
        for points, pen in zip(pointsList, self.pens):
            pen.qCurveTo(*points)
            current_pts.append((points[-1],))
        self.current_pts = current_pts  # type: ignore

    def _curves_to_quadratic(self, pointsList: list[tuple[Point, ...]]) -> None:
        curves = []
        assert self.current_pts is not None
        for current_pt, points in zip(self.current_pts, pointsList):
            curves.append(current_pt + points)
        quadratics = curves_to_quadratic(curves, [self.max_err] * len(curves))
        pointsList = []
        for quadratic in quadratics:
            pointsList.append(quadratic[1:])
        self.qCurveTo(pointsList)  # type: ignore

    def curveTo(self, pointsList: list[tuple[Point, ...]]) -> None:
        self._check_contour_is_open()
        self._curves_to_quadratic(pointsList)

    def closePath(self) -> None:
        self._check_contour_is_open()
        if self.start_pts is None:
            for pen in self.pens:
                pen.closePath()
        self.current_pts = self.start_pts = None

    def endPath(self) -> None:
        self._check_contour_is_open()
        if self.start_pts is None:
            for pen in self.pens:
                pen.endPath()
        self.current_pts = self.start_pts = None

    def addComponent(
        self, glyphName: str, transformations: Iterable[Transformation]
    ) -> None:
        self._check_contour_is_closed()
        for trans, pen in zip(transformations, self.pens):
            pen.addComponent(glyphName, trans)
