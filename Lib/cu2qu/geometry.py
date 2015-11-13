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


from math import hypot
from fontTools.misc import bezierTools


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
        return sum(a * b for a, b in zip(self.p, other.p))


def lerp(p1, p2, t):
    """Linearly interpolate between p1 and p2 at time t."""
    return p1 * (1 - t) + p2 * t


def quadratic_bezier_at(p, t):
    """Return the point on a quadratic bezier curve at time t."""

    return Point([
        lerp(lerp(p[0][0], p[1][0], t), lerp(p[1][0], p[2][0], t), t),
        lerp(lerp(p[0][1], p[1][1], t), lerp(p[1][1], p[2][1], t), t)])


def cubic_bezier_at(p, t):
    """Return the point on a cubic bezier curve at time t."""

    return Point([
        lerp(lerp(lerp(p[0][0], p[1][0], t), lerp(p[1][0], p[2][0], t), t),
             lerp(lerp(p[1][0], p[2][0], t), lerp(p[2][0], p[3][0], t), t), t),
        lerp(lerp(lerp(p[0][1], p[1][1], t), lerp(p[1][1], p[2][1], t), t),
             lerp(lerp(p[1][1], p[2][1], t), lerp(p[2][1], p[3][1], t), t), t)])


def cubic_approx(p, t):
    """Approximate a cubic bezier curve with a quadratic one."""

    p1 = lerp(p[0], p[1], 1.5)
    p2 = lerp(p[3], p[2], 1.5)
    return [p[0], lerp(p1, p2, t), p[3]]


def calc_intersect(p):
    """Calculate the intersection of ab and cd, given [a, b, c, d]."""

    a, b, c, d = p
    ab = b - a
    cd = d - c
    p = Point([-ab[1], ab[0]])
    try:
        h = p.dot(a - c) / p.dot(cd)
    except ZeroDivisionError:
        raise ValueError('Parallel vectors given to calc_intersect.')
    return c + cd * h


def cubic_approx_spline(p, n):
    """Approximate a cubic bezier curve with a spline of n quadratics.

    Returns None if n is 1 and the cubic's control vectors are parallel, since
    no quadratic exists with this cubic's tangents.
    """

    if n == 1:
        try:
            p1 = calc_intersect(p)
        except ValueError:
            return None
        return p[0], p1, p[3]

    spline = [p[0]]
    ts = [(float(i) / n) for i in range(1, n)]
    segments = [
        map(Point, segment)
        for segment in bezierTools.splitCubicAtT(p[0], p[1], p[2], p[3], *ts)]
    for i in range(len(segments)):
        segment = cubic_approx(segments[i], float(i) / (n - 1))
        spline.append(segment[1])
    spline.append(p[3])
    return spline


def curve_spline_dist(bezier, spline):
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
            p1 = cubic_bezier_at(bezier, (float(j) / steps + i - 1) / n)
            p2 = quadratic_bezier_at(segment, float(j) / steps)
            error = max(error, p1.dist(p2))
    return error


def curve_to_quadratic(p, max_n, max_err):
    """Return a quadratic spline approximating this cubic bezier."""

    for n in range(1, max_n + 1):
        spline = cubic_approx_spline(p, n)
        if spline and curve_spline_dist(p, spline) <= max_err:
            break
    return spline


def curves_to_quadratic(curves, max_n, max_err):
    """Return quadratic splines approximating these cubic beziers."""

    for n in range(1, max_n + 1):
        splines = [cubic_approx_spline(c, n) for c in curves]
        if (all(splines) and
            max(curve_spline_dist(c, s)
                for c, s in zip(curves, splines)) <= max_err):
            break
    return splines
