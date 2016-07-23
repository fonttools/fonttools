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


from __future__ import print_function, division, absolute_import

from math import hypot
from fontTools.misc import bezierTools

__all__ = ['curve_to_quadratic', 'curves_to_quadratic']

MAX_N = 100


class Cu2QuError(Exception):
    pass


class ApproxNotFoundError(Cu2QuError):
    def __init__(self, curve, error=None):
        if error is None:
            message = "no approximation found: %s" % curve
        else:
            message = ("approximation error exceeds max tolerance: %s, "
                       "error=%g" % (curve, error))
        super(Cu2QuError, self).__init__(message)
        self.curve = curve
        self.error = error


def vector(p1, p2):
    """Return the vector from p1 to p2."""
    return p2[0] - p1[0], p2[1] - p1[1]


def translate(p, v):
    """Translate a point by a vector."""
    return p[0] + v[0], p[1] + v[1]


def scale(v, n):
    """Scale a vector."""
    return v[0] * n, v[1] * n


def dot(v1, v2):
    """Return the dot product of two vectors."""
    return v1[0] * v2[0] + v1[1] * v2[1]


def lerp_pt(p1, p2, t):
    """Linearly interpolate between points p1 and p2 at time t."""
    (x1, y1), (x2, y2) = p1, p2
    return x1+t*(x2-x1), y1+t*(y2-y1)

def mid_pt(p1, p2):
    """Return midpoint between p1 and p2."""
    return ((p1[0]+p2[0])*.5, (p1[1]+p2[1])*.5)


def cubic_from_quadratic(p):
    return (p[0], lerp_pt(p[0],p[1],2./3), lerp_pt(p[2],p[1],2./3), p[2])


def cubic_approx_control(p, t):
    """Approximate a cubic bezier curve with a quadratic one.
       Returns the candidate control point."""

    p1 = lerp_pt(p[0], p[1], 1.5)
    p2 = lerp_pt(p[3], p[2], 1.5)
    return lerp_pt(p1, p2, t)


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


def cubic_farthest2(p,tolerance2):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p

    e0 = x0*x0+y0*y0
    e3 = x3*x3+y3*y3
    e = max(e0, e3)
    if e > tolerance2:
        return e

    e1 = x1*x1+y1*y1
    e2 = x2*x2+y2*y2
    e = max(e1, e2)
    if e <= tolerance2:
        return e

    # Split.
    segments = bezierTools.splitCubicAtT(p[0], p[1], p[2], p[3], .5)
    return max(cubic_farthest2(s,tolerance2) for s in segments)


def cubic_cubic_error2(a,b,tolerance2):
    return cubic_farthest2((vector(a[0],b[0]),
                            vector(a[1],b[1]),
                            vector(a[2],b[2]),
                            vector(a[3],b[3])), tolerance2)


def cubic_quadratic_error2(a,b,tolerance2):
    return cubic_cubic_error2(a, cubic_from_quadratic(b), tolerance2)


def cubic_approx_spline(p, n, tolerance):
    """Approximate a cubic bezier curve with a spline of n quadratics.

    Returns None if n is 1 and the cubic's control vectors are parallel, since
    no quadratic exists with this cubic's tangents.
    """

    tolerance2 = tolerance*tolerance

    if n == 1:
        try:
            p1 = calc_intersect(p)
        except ValueError:
            return None
        quad = (p[0], p1, p[3])
        if cubic_quadratic_error2(p, quad, tolerance2) > tolerance2:
            return None
        return quad

    spline = [p[0]]
    ts = [i / n for i in range(1, n)]
    segments = bezierTools.splitCubicAtT(p[0], p[1], p[2], p[3], *ts)
    for i in range(len(segments)):
        spline.append(cubic_approx_control(segments[i], i / (n - 1)))
    spline.append(p[3])

    for i in range(1,n+1):
        if i == 1:
	    segment = (spline[0],spline[1],mid_pt(spline[1],spline[2]))
	elif i == n:
            segment = mid_pt(spline[-3],spline[-2]),spline[-2],spline[-1]
	else:
            segment = mid_pt(spline[i-1],spline[i]), spline[i], mid_pt(spline[i],spline[i+1])

        error2 = cubic_quadratic_error2(segments[i-1], segment, tolerance2)
	if error2 > tolerance2: return None

    return spline


def curve_to_quadratic(p, max_err):
    """Return a quadratic spline approximating this cubic bezier, and
    the error of approximation.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    with the given parameters.
    """

    spline, error = None, None
    for n in range(1, MAX_N + 1):
        spline = cubic_approx_spline(p, n, max_err)
        if spline is not None:
            break
    else:
        # no break: approximation not found or error exceeds tolerance
        raise ApproxNotFoundError(p, error)
    return spline, error


def curves_to_quadratic(curves, max_errors):
    """Return quadratic splines approximating these cubic beziers, and
    the respective errors of approximation.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    for all curves with the given parameters.
    """

    num_curves = len(curves)
    assert len(max_errors) == num_curves

    splines = [None] * num_curves
    errors = [None] * num_curves
    for n in range(1, MAX_N + 1):
        splines = [cubic_approx_spline(c, n, e) for c,e in zip(curves,max_errors)]
        if all(splines):
            break
    else:
        # no break: raise if any spline is None or error exceeds tolerance
        for c, s, error, max_err in zip(curves, splines, errors, max_errors):
            if s is None or error > max_err:
                raise ApproxNotFoundError(c, error)
    return splines, errors
