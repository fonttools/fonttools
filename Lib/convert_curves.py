#! /usr/bin/env python
#
# Copyright 2015 Google Inc. All Rights Reserved.
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


"""Converts cubic bezier curves to quadratic splines.

Conversion is performed such that the quadratic splines keep the same end-curve
tangents as the original cubics. The approach is iterative, increasing the
number of segments for a spline until the error gets below a bound.

If necessary, respective curves from multiple fonts will be converted at once to
ensure that the resulting splines are interpolation-compatible.
"""


from math import hypot

from fontTools.misc import bezierTools
from robofab.objects.objectsRF import RSegment, RPoint


def replaceSegments(contour, segments):
    try:
        return contour.replaceSegments(segments)
    except AttributeError:
        pass
    while len(contour):
        contour.removeSegment(0)
    for s in segments:
        contour.appendSegment(s.type, [(p.x, p.y) for p in s.points], s.smooth)


_zip = zip
def zip(*args):
    """Ensure each argument to zip has the same length."""
    if len(set(len(a) for a in args)) != 1:
        msg = "Args to zip in convertCurves.py should have equal lengths: "
        raise ValueError(msg + " ".join(str(a) for a in args))
    return _zip(*args)


class Point:
    """An arithmetic-compatible 2D vector.
    We use this because arithmetic with RoboFab's RPoint is prohibitively slow.
    """

    def __init__(self, p):
        self.p = map(float, p)

    def __getitem__(self, key):
        return self.p[key]

    def __add__(self, other):
        return Point([a + b for a, b in zip(self.p, other.p)])

    def __sub__(self, other):
        return Point([a - b for a, b in zip(self.p, other.p)])

    def __mul__(self, n):
        return Point([a * n for a in self.p])

    def dist(self, other):
        """Calculate the distance between two points."""
        return hypot(self[0] - other[0], self[1] - other[1])

    def dot(self, other):
        """Return the dot product of two points."""
        return self[0] * other[0] + self[1] * other[1]


def lerp(p1, p2, t):
    """Linearly interpolate between p1 and p2 at time t."""
    return p1 * (1 - t) + p2 * t


def quadraticBezierAt(p, t):
    """Return the point on a quadratic bezier curve at time t."""

    return Point([
        lerp(lerp(p[0][0], p[1][0], t), lerp(p[1][0], p[2][0], t), t),
        lerp(lerp(p[0][1], p[1][1], t), lerp(p[1][1], p[2][1], t), t)])


def cubicBezierAt(p, t):
    """Return the point on a cubic bezier curve at time t."""

    return Point([
        lerp(lerp(lerp(p[0][0], p[1][0], t), lerp(p[1][0], p[2][0], t), t),
             lerp(lerp(p[1][0], p[2][0], t), lerp(p[2][0], p[3][0], t), t), t),
        lerp(lerp(lerp(p[0][1], p[1][1], t), lerp(p[1][1], p[2][1], t), t),
             lerp(lerp(p[1][1], p[2][1], t), lerp(p[2][1], p[3][1], t), t), t)])


def cubicApprox(p, t):
    """Approximate a cubic bezier curve with a quadratic one."""

    p1 = lerp(p[0], p[1], 1.5)
    p2 = lerp(p[3], p[2], 1.5)
    return [p[0], lerp(p1, p2, t), p[3]]


def calcIntersect(p):
    """Calculate the intersection of ab and cd, given [a, b, c, d]."""

    a, b, c, d = p
    ab = b - a
    cd = d - c
    p = Point([-ab[1], ab[0]])
    try:
        h = p.dot(a - c) / p.dot(cd)
    except ZeroDivisionError:
        raise ValueError("Parallel vectors given to calcIntersect.")
    return c + cd * h


def cubicApproxSpline(p, n):
    """Approximate a cubic bezier curve with a spline of n quadratics.

    Returns None if n is 1 and the cubic's control vectors are parallel, since
    no quadratic exists with this cubic's tangents."""

    if n == 1:
        try:
            p1 = calcIntersect(p)
        except ValueError:
            return None
        return p[0], p1, p[3]

    spline = [p[0]]
    ts = [(float(i) / n) for i in range(1, n)]
    segments = [
        map(Point, segment)
        for segment in bezierTools.splitCubicAtT(p[0], p[1], p[2], p[3], *ts)]
    for i in range(len(segments)):
        segment = cubicApprox(segments[i], float(i) / (n - 1))
        spline.append(segment[1])
    spline.append(p[3])
    return spline


def curveSplineDist(bezier, spline):
    """Max distance between a bezier and quadratic spline at sampled ts."""

    TOTAL_STEPS = 20
    error = 0
    n = len(spline) - 2
    steps = TOTAL_STEPS / n
    for i in range(1, n + 1):
        segment = [
            spline[0] if i == 1 else segment[2],
            spline[i],
            spline[i + 1] if i == n else lerp(spline[i], spline[i + 1], 0.5)]
        for j in range(steps):
            p1 = cubicBezierAt(bezier, (float(j) / steps + i - 1) / n)
            p2 = quadraticBezierAt(segment, float(j) / steps)
            error = max(error, p1.dist(p2))
    return error


def convertToQuadratic(p0,p1,p2,p3, max_n, max_err):
    if not isinstance(p0, RPoint):
        return convertCollectionToQuadratic(p0, p1, p2, p3, max_n, max_err)

    p = [Point([i.x, i.y]) for i in [p0, p1, p2, p3]]
    for n in range(1, max_n + 1):
        spline = cubicApproxSpline(p, n)
        if spline and curveSplineDist(p, spline) <= max_err:
            break
    return spline


def convertCollectionToQuadratic(p0, p1, p2, p3, max_n, max_err):
    curves = [[Point([i.x, i.y]) for i in p] for p in zip(p0, p1, p2, p3)]
    for n in range(1, max_n + 1):
        splines = [cubicApproxSpline(c, n) for c in curves]
        if not all(splines):
            continue
        if max(curveSplineDist(*a) for a in zip(curves, splines)) <= max_err:
            break
    return splines


def cubicSegmentToQuadratic(c, sid, max_n, max_err, report):

    segment = c[sid]
    if (segment.type != "curve"):
        print "Segment type not curve"
        return
    
    #pSegment,junk = getPrevAnchor(c,sid)
    pSegment = c[sid-1] #assumes that a curve type will always be proceeded by another point on the same contour
    points = convertToQuadratic(pSegment.points[-1],segment.points[0],
                                segment.points[1],segment.points[2],
                                max_n, max_err)

    if isinstance(points[0][0], float):  # just one spline
        n = str(len(points))
    else:  # collection of splines
        n = str(len(points[0]))
    report[n] = report.get(n, 0) + 1

    try:
        return segment.asQuadratic([p[1:] for p in points])
    except AttributeError:
        pass
    return RSegment(
        'qcurve', [[int(i) for i in p] for p in points[1:]], segment.smooth)


def glyphCurvesToQuadratic(g, max_n, max_err, report):

    for c in g:
        segments = []
        for i in range(len(c)):
            s = c[i]
            if s.type == "curve":
                try:
                    segments.append(cubicSegmentToQuadratic(
                        c, i, max_n, max_err, report))
                except Exception:
                    print g.name, i
                    raise
            else:
                segments.append(s)
        replaceSegments(c, segments)


def fonts_to_quadratic(fonts, compatible=False, max_n=10, max_err=5):
    """Convert the curves of a collection of fonts to quadratic.

    If compatibility is required, all curves will be converted to quadratic
    at once. Otherwise the glyphs will be converted one font at a time,
    which should be slightly more optimized.
    """

    report = {}
    if compatible:
        fonts = [FontCollection(fonts)]
    for font in fonts:
        for glyph in font:
            glyphCurvesToQuadratic(glyph, max_n, max_err, report)

    spline_lengths = report.keys()
    spline_lengths.sort()
    return (
        '>>> New spline lengths:\n' +
        '\n'.join('%s: %d' % (l, report[l]) for l in spline_lengths))


class FontCollection:
    """A collection of fonts, or font components from different fonts.

    Behaves like a single instance of the component, allowing access into
    multiple fonts simultaneously for purposes of ensuring interpolation
    compatibility.
    """

    def __init__(self, fonts):
        self.init(fonts, GlyphCollection)

    def __getitem__(self, key):
        return self.children[key]

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return str(self.instances)

    def init(self, instances, childCollectionType, getChildren=None):
        self.instances = instances
        childrenByInstance = map(getChildren, self.instances)
        self.children = map(childCollectionType, zip(*childrenByInstance))


class GlyphCollection(FontCollection):
    def __init__(self, glyphs):
        self.init(glyphs, ContourCollection)
        self.name = glyphs[0].name


class ContourCollection(FontCollection):
    def __init__(self, contours):
        self.init(contours, SegmentCollection)

    def replaceSegments(self, segmentCollections):
        segmentsByContour = zip(*[s.instances for s in segmentCollections])
        for contour, segments in zip(self.instances, segmentsByContour):
            replaceSegments(contour, segments)


class SegmentCollection(FontCollection):
    def __init__(self, segments):
        self.init(segments, None, lambda s: s.points)
        self.points = self.children
        self.type = segments[0].type

    def asQuadratic(self, newPoints=None):
        points = newPoints or self.children
        return SegmentCollection([
            RSegment("qcurve", [[int(i) for i in p] for p in pts], s.smooth)
            for s, pts in zip(self.instances, points)])
