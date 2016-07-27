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

__all__ = ['curve_to_quadratic', 'curves_to_quadratic']

MAX_N = 100


def calcCubicPoints(a, b, c, d):
    _1 = d
    _2 = (c / 3.0) + d
    _3 = (b + c) / 3.0 + _2
    _4 = a + d + c + b
    return _1, _2, _3, _4

def calcCubicParameters(pt1, pt2, pt3, pt4):
    c = (pt2 -pt1) * 3.0
    b = (pt3 - pt2) * 3.0 - c
    d = pt1
    a = pt4 - d - c - b
    return a, b, c, d

def splitCubicIntoN(pt1, pt2, pt3, pt4, n):
    a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
    segments = []
    dt = 1./n
    delta_2 = dt*dt
    delta_3 = dt * delta_2
    for i in range(n):
        t1 = i * dt
        t1_2 = t1*t1
        t1_3 = t1*t1_2
        # calc new a, b, c and d
        a1 = a * delta_3
        b1 = (3*a*t1 + b) * delta_2
        c1 = (2*b*t1 + c + 3*a*t1_2) * dt
        d1 = a*t1_3 + b*t1_2 + c*t1 + d
        segments.append(calcCubicPoints(a1, b1, c1, d1))
    return segments

def splitCubicIntoTwo(pt1, pt2, pt3, pt4):
    mid = (pt1+3*(pt2+pt3)+pt4)*.125
    deriv3 = (pt4+pt3-pt2-pt1)*.125
    return ((pt1, (pt1+pt2)*.5, mid-deriv3, mid),
            (mid, mid+deriv3, (pt3+pt4)*.5, pt4))

def splitCubicIntoThree(pt1, pt2, pt3, pt4, _27=1/27.):
    mid1 = (pt1*8+pt2*12+pt3*6+pt4)*_27
    deriv1 = (pt4+pt3*3-pt1*4)*_27
    mid2 = (pt1+pt2*6+pt3*12+pt4*8)*_27
    deriv2 = (pt4*4-pt2*3-pt1)*_27
    return ((pt1, (pt1*2+pt2)/3., mid1-deriv1, mid1),
            (mid1, mid1+deriv1, mid2-deriv2, mid2),
            (mid2, mid2+deriv2, (pt3+pt4*2)/3., pt4))


class Cu2QuError(Exception):
    pass


class ApproxNotFoundError(Cu2QuError):
    def __init__(self, curve):
        message = "no approximation found: %s" % curve
        super(Cu2QuError, self).__init__(message)
        self.curve = curve


def dot(v1, v2):
    """Return the dot product of two vectors."""
    return (v1*v2.conjugate()).real


def cubic_approx_control(p, t):
    """Approximate a cubic bezier curve with a quadratic one.
       Returns the candidate control point."""

    p1 = p[0]+(p[1]-p[0])*1.5
    p2 = p[3]+(p[2]-p[3])*1.5
    return p1+(p2-p1)*t


def calc_intersect(a, b, c, d):
    """Calculate the intersection of ab and cd, given a, b, c, d."""

    ab = b - a
    cd = d - c
    p = ab * 1j
    try:
        h = dot(p, a - c) / dot(p, cd)
    except ZeroDivisionError:
        return None
    return c + cd * h


def _cubic_farthest_fit(pt1,pt2,pt3,pt4,tolerance):
    """Returns True if the cubic Bezier p entirely lies within a distance
    tolerance of origin, False otherwise."""

    if abs(pt2) <= tolerance and abs(pt3) <= tolerance:
        return True

    # Split.
    mid = (pt1+3*(pt2+pt3)+pt4)*.125
    if abs(mid) > tolerance:
        return False
    deriv3 = (pt4+pt3-pt2-pt1)*.125
    return (_cubic_farthest_fit(pt1, (pt1+pt2)*.5, mid-deriv3, mid,tolerance) and
            _cubic_farthest_fit(mid, mid+deriv3, (pt3+pt4)*.5, pt4,tolerance))

def cubic_farthest_fit(pt1,pt2,pt3,pt4,tolerance):
    """Returns True if the cubic Bezier p entirely lies within a distance
    tolerance of origin, False otherwise."""

    if abs(pt1) > tolerance or abs(pt4) > tolerance:
        return False

    if abs(pt2) <= tolerance and abs(pt3) <= tolerance:
        return True

    # Split.
    mid = (pt1+3*(pt2+pt3)+pt4)*.125
    if abs(mid) > tolerance:
        return False
    deriv3 = (pt4+pt3-pt2-pt1)*.125
    return (_cubic_farthest_fit(pt1, (pt1+pt2)*.5, mid-deriv3, mid,tolerance) and
            _cubic_farthest_fit(mid, mid+deriv3, (pt3+pt4)*.5, pt4,tolerance))


def cubic_approx_spline(p, n, tolerance):
    """Approximate a cubic bezier curve with a spline of n quadratics.

    Returns None if n is 1 and the cubic's control vectors are parallel, since
    no quadratic exists with this cubic's tangents.
    """

    if n == 1:
        qp1 = calc_intersect(*p)
        if qp1 is None:
            return None
        p0 = p[0]
        p3 = p[3]
        p1 = p0+(qp1-p0)*(2./3)
        p2 =  p3+(qp1-p3)*(2./3)
        if not cubic_farthest_fit(0,
                                  p1-p[1],
                                  p2-p[2],
                                  0, tolerance):
            return None
        return p0, qp1, p3

    spline = [p[0]]
    if n == 2:
        segments = splitCubicIntoTwo(p[0], p[1], p[2], p[3])
    elif n == 3:
        segments = splitCubicIntoThree(p[0], p[1], p[2], p[3])
    else:
        segments = splitCubicIntoN(p[0], p[1], p[2], p[3], n)
    for i in range(len(segments)):
        spline.append(cubic_approx_control(segments[i], i / (n - 1)))
    spline.append(p[3])

    for i in range(1,n+1):
        if i == 1:
            p0,p1,p2 = (spline[0],spline[1],(spline[1]+spline[2])*.5)
        elif i == n:
            p0,p1,p2 = (spline[-3]+spline[-2])*.5,spline[-2],spline[-1]
        else:
            p0,p1,p2 = (spline[i-1]+spline[i])*.5, spline[i], (spline[i]+spline[i+1])*.5

        pt1, pt2, pt3, pt4 = segments[i-1]
        if not cubic_farthest_fit(p0                - pt1,
                                  p0+(p1-p0)*(2./3) - pt2,
                                  p2+(p1-p2)*(2./3) - pt3,
                                  p2                - pt4,
                                  tolerance):
            return None

    return spline


def curve_to_quadratic(p, max_err):
    """Return a quadratic spline approximating this cubic bezier, and
    the error of approximation.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    with the given parameters.
    """

    p = [complex(*P) for P in p]
    spline = None
    for n in range(1, MAX_N + 1):
        spline = cubic_approx_spline(p, n, max_err)
        if spline is not None:
            break
    else:
        # no break: approximation not foun
        raise ApproxNotFoundError(p)
    return [(s.real,s.imag) for s in spline]


def curves_to_quadratic(curves, max_errors):
    """Return quadratic splines approximating these cubic beziers, and
    the respective errors of approximation.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    for all curves with the given parameters.
    """

    curves = [[complex(*P) for P in p] for p in curves]
    num_curves = len(curves)
    assert len(max_errors) == num_curves

    splines = [None] * num_curves
    for n in range(1, MAX_N + 1):
        splines = [cubic_approx_spline(c, n, e) for c,e in zip(curves,max_errors)]
        if all(splines):
            break
    else:
        # no break: raise if any spline is None or error exceeds tolerance
        for c, s in zip(curves, splines):
            if s is None:
                raise ApproxNotFoundError(c)
    return [[(s.real,s.imag) for s in spline] for spline in splines]
