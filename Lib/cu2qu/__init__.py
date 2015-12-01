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


def vector(p1, p2):
    """Return the vector from p1 to p2."""
    return p2[0] - p1[0], p2[1] - p1[1]


def translate(p, v):
    """Translate a point by a vector."""
    return p[0] + v[0], p[1] + v[1]


def scale(v, n):
    """Scale a vector."""
    return v[0] * n, v[1] * n


def dist(p1, p2):
    """Calculate the distance between two points."""
    return hypot(p1[0] - p2[0], p1[1] - p2[1])


def dot(v1, v2):
    """Return the dot product of two vectors."""
    return v1[0] * v2[0] + v1[1] * v2[1]


def lerp(a, b, t):
    """Linearly interpolate between scalars a and b at time t."""
    return a * (1 - t) + b * t


def lerp_pt(p1, p2, t):
    """Linearly interpolate between points p1 and p2 at time t."""
    (x1, y1), (x2, y2) = p1, p2
    return lerp(x1, x2, t), lerp(y1, y2, t)


def quadratic_bezier_at(p, t):
    """Return the point on a quadratic bezier curve at time t."""

    (x1, y1), (x2, y2), (x3, y3) = p
    return (
        lerp(lerp(x1, x2, t), lerp(x2, x3, t), t),
        lerp(lerp(y1, y2, t), lerp(y2, y3, t), t))


def cubic_bezier_at(p, t):
    """Return the point on a cubic bezier curve at time t."""

    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p
    return (
        lerp(lerp(lerp(x1, x2, t), lerp(x2, x3, t), t),
             lerp(lerp(x2, x3, t), lerp(x3, x4, t), t), t),
        lerp(lerp(lerp(y1, y2, t), lerp(y2, y3, t), t),
             lerp(lerp(y2, y3, t), lerp(y3, y4, t), t), t))


def cubic_approx(p, t):
    """Approximate a cubic bezier curve with a quadratic one."""

    p1 = lerp_pt(p[0], p[1], 1.5)
    p2 = lerp_pt(p[3], p[2], 1.5)
    return p[0], lerp_pt(p1, p2, t), p[3]


def calc_intersect(p):
    """Calculate the intersection of ab and cd, given [a, b, c, d]."""

    a, b, c, d = p
    ab = vector(a, b)
    cd = vector(c, d)
    p = -ab[1], ab[0]
    try:
        h = dot(p, vector(c, a)) / dot(p, cd)
    except ZeroDivisionError:
        raise ValueError('Parallel vectors given to calc_intersect.')
    return translate(c, scale(cd, h))


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
    segments = bezierTools.splitCubicAtT(p[0], p[1], p[2], p[3], *ts)
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
            spline[i + 1] if i == n else lerp_pt(spline[i], spline[i + 1], 0.5)]
        for j in range(steps):
            p1 = cubic_bezier_at(bezier, (float(j) / steps + i - 1) / n)
            p2 = quadratic_bezier_at(segment, float(j) / steps)
            error = max(error, dist(p1, p2))
    return error


def curve_to_quadratic(p, max_err, max_n):
    """Return a quadratic spline approximating this cubic bezier."""

    for n in range(1, max_n + 1):
        spline = cubic_approx_spline(p, n)
        if spline and curve_spline_dist(p, spline) <= max_err:
            break
    return spline


def curves_to_quadratic(curves, max_errors, max_n):
    """Return quadratic splines approximating these cubic beziers."""

    for n in range(1, max_n + 1):
        splines = [cubic_approx_spline(c, n) for c in curves]
        if (all(splines) and
            all(curve_spline_dist(c, s) < max_err
                for c, s, max_err in zip(curves, splines, max_errors))):
            break
    return splines
