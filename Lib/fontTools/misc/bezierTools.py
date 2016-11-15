"""fontTools.misc.bezierTools.py -- tools for working with bezier path segments.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

__all__ = [
    "calcQuadraticBounds",
    "calcCubicBounds",
    "splitLine",
    "splitQuadratic",
    "splitCubic",
    "splitQuadraticAtT",
    "splitCubicAtT",
    "solveQuadratic",
    "solveCubic",
]

from fontTools.misc.arrayTools import calcBounds

epsilonDigits = 6
epsilon = 1e-10


def calcQuadraticBounds(pt1, pt2, pt3):
    """Return the bounding rectangle for a qudratic bezier segment.
    pt1 and pt3 are the "anchor" points, pt2 is the "handle".

        >>> calcQuadraticBounds((0, 0), (50, 100), (100, 0))
        (0, 0, 100, 50.0)
        >>> calcQuadraticBounds((0, 0), (100, 0), (100, 100))
        (0.0, 0.0, 100, 100)
    """
    (ax, ay), (bx, by), (cx, cy) = calcQuadraticParameters(pt1, pt2, pt3)
    ax2 = ax*2.0
    ay2 = ay*2.0
    roots = []
    if ax2 != 0:
        roots.append(-bx/ax2)
    if ay2 != 0:
        roots.append(-by/ay2)
    points = [(ax*t*t + bx*t + cx, ay*t*t + by*t + cy) for t in roots if 0 <= t < 1] + [pt1, pt3]
    return calcBounds(points)


def calcCubicBounds(pt1, pt2, pt3, pt4):
    """Return the bounding rectangle for a cubic bezier segment.
    pt1 and pt4 are the "anchor" points, pt2 and pt3 are the "handles".

        >>> calcCubicBounds((0, 0), (25, 100), (75, 100), (100, 0))
        (0, 0, 100, 75.0)
        >>> calcCubicBounds((0, 0), (50, 0), (100, 50), (100, 100))
        (0.0, 0.0, 100, 100)
        >>> print("%f %f %f %f" % calcCubicBounds((50, 0), (0, 100), (100, 100), (50, 0)))
        35.566243 0.000000 64.433757 75.000000
    """
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = calcCubicParameters(pt1, pt2, pt3, pt4)
    # calc first derivative
    ax3 = ax * 3.0
    ay3 = ay * 3.0
    bx2 = bx * 2.0
    by2 = by * 2.0
    xRoots = [t for t in solveQuadratic(ax3, bx2, cx) if 0 <= t < 1]
    yRoots = [t for t in solveQuadratic(ay3, by2, cy) if 0 <= t < 1]
    roots = xRoots + yRoots

    points = [(ax*t*t*t + bx*t*t + cx * t + dx, ay*t*t*t + by*t*t + cy * t + dy) for t in roots] + [pt1, pt4]
    return calcBounds(points)


def splitLine(pt1, pt2, where, isHorizontal):
    """Split the line between pt1 and pt2 at position 'where', which
    is an x coordinate if isHorizontal is False, a y coordinate if
    isHorizontal is True. Return a list of two line segments if the
    line was successfully split, or a list containing the original
    line.

        >>> printSegments(splitLine((0, 0), (100, 100), 50, True))
        ((0, 0), (50, 50))
        ((50, 50), (100, 100))
        >>> printSegments(splitLine((0, 0), (100, 100), 100, True))
        ((0, 0), (100, 100))
        >>> printSegments(splitLine((0, 0), (100, 100), 0, True))
        ((0, 0), (0, 0))
        ((0, 0), (100, 100))
        >>> printSegments(splitLine((0, 0), (100, 100), 0, False))
        ((0, 0), (0, 0))
        ((0, 0), (100, 100))
        >>> printSegments(splitLine((100, 0), (0, 0), 50, False))
        ((100, 0), (50, 0))
        ((50, 0), (0, 0))
        >>> printSegments(splitLine((0, 100), (0, 0), 50, True))
        ((0, 100), (0, 50))
        ((0, 50), (0, 0))
    """
    pt1x, pt1y = pt1
    pt2x, pt2y = pt2

    ax = (pt2x - pt1x)
    ay = (pt2y - pt1y)

    bx = pt1x
    by = pt1y

    a = (ax, ay)[isHorizontal]

    if a == 0:
        return [(pt1, pt2)]
    t = (where - (bx, by)[isHorizontal]) / a
    if 0 <= t < 1:
        midPt = ax * t + bx, ay * t + by
        return [(pt1, midPt), (midPt, pt2)]
    else:
        return [(pt1, pt2)]


def splitQuadratic(pt1, pt2, pt3, where, isHorizontal):
    """Split the quadratic curve between pt1, pt2 and pt3 at position 'where',
    which is an x coordinate if isHorizontal is False, a y coordinate if
    isHorizontal is True. Return a list of curve segments.

        >>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 150, False))
        ((0, 0), (50, 100), (100, 0))
        >>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 50, False))
        ((0, 0), (25, 50), (50, 50))
        ((50, 50), (75, 50), (100, 0))
        >>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 25, False))
        ((0, 0), (12.5, 25), (25, 37.5))
        ((25, 37.5), (62.5, 75), (100, 0))
        >>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 25, True))
        ((0, 0), (7.32233, 14.6447), (14.6447, 25))
        ((14.6447, 25), (50, 75), (85.3553, 25))
        ((85.3553, 25), (92.6777, 14.6447), (100, -7.10543e-15))
        >>> # XXX I'm not at all sure if the following behavior is desirable:
        >>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 50, True))
        ((0, 0), (25, 50), (50, 50))
        ((50, 50), (50, 50), (50, 50))
        ((50, 50), (75, 50), (100, 0))
    """
    a, b, c = calcQuadraticParameters(pt1, pt2, pt3)
    solutions = solveQuadratic(a[isHorizontal], b[isHorizontal],
        c[isHorizontal] - where)
    solutions = sorted([t for t in solutions if 0 <= t < 1])
    if not solutions:
        return [(pt1, pt2, pt3)]
    return _splitQuadraticAtT(a, b, c, *solutions)


def splitCubic(pt1, pt2, pt3, pt4, where, isHorizontal):
    """Split the cubic curve between pt1, pt2, pt3 and pt4 at position 'where',
    which is an x coordinate if isHorizontal is False, a y coordinate if
    isHorizontal is True. Return a list of curve segments.

        >>> printSegments(splitCubic((0, 0), (25, 100), (75, 100), (100, 0), 150, False))
        ((0, 0), (25, 100), (75, 100), (100, 0))
        >>> printSegments(splitCubic((0, 0), (25, 100), (75, 100), (100, 0), 50, False))
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75))
        ((50, 75), (68.75, 75), (87.5, 50), (100, 0))
        >>> printSegments(splitCubic((0, 0), (25, 100), (75, 100), (100, 0), 25, True))
        ((0, 0), (2.29379, 9.17517), (4.79804, 17.5085), (7.47414, 25))
        ((7.47414, 25), (31.2886, 91.6667), (68.7114, 91.6667), (92.5259, 25))
        ((92.5259, 25), (95.202, 17.5085), (97.7062, 9.17517), (100, 1.77636e-15))
    """
    a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
    solutions = solveCubic(a[isHorizontal], b[isHorizontal], c[isHorizontal],
        d[isHorizontal] - where)
    solutions = sorted([t for t in solutions if 0 <= t < 1])
    if not solutions:
        return [(pt1, pt2, pt3, pt4)]
    return _splitCubicAtT(a, b, c, d, *solutions)


def splitQuadraticAtT(pt1, pt2, pt3, *ts):
    """Split the quadratic curve between pt1, pt2 and pt3 at one or more
    values of t. Return a list of curve segments.

        >>> printSegments(splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5))
        ((0, 0), (25, 50), (50, 50))
        ((50, 50), (75, 50), (100, 0))
        >>> printSegments(splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5, 0.75))
        ((0, 0), (25, 50), (50, 50))
        ((50, 50), (62.5, 50), (75, 37.5))
        ((75, 37.5), (87.5, 25), (100, 0))
    """
    a, b, c = calcQuadraticParameters(pt1, pt2, pt3)
    return _splitQuadraticAtT(a, b, c, *ts)


def splitCubicAtT(pt1, pt2, pt3, pt4, *ts):
    """Split the cubic curve between pt1, pt2, pt3 and pt4 at one or more
    values of t. Return a list of curve segments.

        >>> printSegments(splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5))
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75))
        ((50, 75), (68.75, 75), (87.5, 50), (100, 0))
        >>> printSegments(splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5, 0.75))
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75))
        ((50, 75), (59.375, 75), (68.75, 68.75), (77.3438, 56.25))
        ((77.3438, 56.25), (85.9375, 43.75), (93.75, 25), (100, 0))
    """
    a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
    return _splitCubicAtT(a, b, c, d, *ts)


def _splitQuadraticAtT(a, b, c, *ts):
    ts = list(ts)
    segments = []
    ts.insert(0, 0.0)
    ts.append(1.0)
    ax, ay = a
    bx, by = b
    cx, cy = c
    for i in range(len(ts) - 1):
        t1 = ts[i]
        t2 = ts[i+1]
        delta = (t2 - t1)
        # calc new a, b and c
        delta_2 = delta*delta
        a1x = ax * delta_2
        a1y = ay * delta_2
        b1x = (2*ax*t1 + bx) * delta
        b1y = (2*ay*t1 + by) * delta
        t1_2 = t1*t1
        c1x = ax*t1_2 + bx*t1 + cx
        c1y = ay*t1_2 + by*t1 + cy

        pt1, pt2, pt3 = calcQuadraticPoints((a1x, a1y), (b1x, b1y), (c1x, c1y))
        segments.append((pt1, pt2, pt3))
    return segments


def _splitCubicAtT(a, b, c, d, *ts):
    ts = list(ts)
    ts.insert(0, 0.0)
    ts.append(1.0)
    segments = []
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    for i in range(len(ts) - 1):
        t1 = ts[i]
        t2 = ts[i+1]
        delta = (t2 - t1)

        delta_2 = delta*delta
        delta_3 = delta*delta_2
        t1_2 = t1*t1
        t1_3 = t1*t1_2

        # calc new a, b, c and d
        a1x = ax * delta_3
        a1y = ay * delta_3
        b1x = (3*ax*t1 + bx) * delta_2
        b1y = (3*ay*t1 + by) * delta_2
        c1x = (2*bx*t1 + cx + 3*ax*t1_2) * delta
        c1y = (2*by*t1 + cy + 3*ay*t1_2) * delta
        d1x = ax*t1_3 + bx*t1_2 + cx*t1 + dx
        d1y = ay*t1_3 + by*t1_2 + cy*t1 + dy
        pt1, pt2, pt3, pt4 = calcCubicPoints((a1x, a1y), (b1x, b1y), (c1x, c1y), (d1x, d1y))
        segments.append((pt1, pt2, pt3, pt4))
    return segments


#
# Equation solvers.
#

from math import sqrt, acos, cos, pi


def solveQuadratic(a, b, c,
        sqrt=sqrt):
    """Solve a quadratic equation where a, b and c are real.
        a*x*x + b*x + c = 0
    This function returns a list of roots. Note that the returned list
    is neither guaranteed to be sorted nor to contain unique values!
    """
    if abs(a) < epsilon:
        if abs(b) < epsilon:
            # We have a non-equation; therefore, we have no valid solution
            roots = []
        else:
            # We have a linear equation with 1 root.
            roots = [-c/b]
    else:
        # We have a true quadratic equation.  Apply the quadratic formula to find two roots.
        DD = b*b - 4.0*a*c
        if DD >= 0.0:
            rDD = sqrt(DD)
            roots = [(-b+rDD)/2.0/a, (-b-rDD)/2.0/a]
        else:
            # complex roots, ignore
            roots = []
    return roots


def solveCubic(a, b, c, d):
    """Solve a cubic equation where a, b, c and d are real.
        a*x*x*x + b*x*x + c*x + d = 0
    This function returns a list of roots. Note that the returned list
    is neither guaranteed to be sorted nor to contain unique values!

    >>> solveCubic(1, 1, -6, 0)
    [-3.0, -0.0, 2.0]
    >>> solveCubic(-10.0, -9.0, 48.0, -29.0)
    [-2.9, 1.0, 1.0]
    >>> solveCubic(-9.875, -9.0, 47.625, -28.75)
    [-2.911392, 1.0, 1.0]
    >>> solveCubic(1.0, -4.5, 6.75, -3.375)
    [1.5, 1.5, 1.5]
    >>> solveCubic(-12.0, 18.0, -9.0, 1.50023651123)
    [0.5, 0.5, 0.5]
    >>> solveCubic(9.0, 0.0, 0.0, -7.62939453125e-05)
    [-0.0, -0.0, -0.0]
    """
    #
    # adapted from:
    #   CUBIC.C - Solve a cubic polynomial
    #   public domain by Ross Cottrell
    # found at: http://www.strangecreations.com/library/snippets/Cubic.C
    #
    if abs(a) < epsilon:
        # don't just test for zero; for very small values of 'a' solveCubic()
        # returns unreliable results, so we fall back to quad.
        return solveQuadratic(b, c, d)
    a = float(a)
    a1 = b/a
    a2 = c/a
    a3 = d/a

    Q = (a1*a1 - 3.0*a2)/9.0
    R = (2.0*a1*a1*a1 - 9.0*a1*a2 + 27.0*a3)/54.0

    R2 = R*R
    Q3 = Q*Q*Q
    R2 = 0 if R2 < epsilon else R2
    Q3 = 0 if abs(Q3) < epsilon else Q3

    R2_Q3 = R2 - Q3

    if R2 == 0. and Q3 == 0.:
        x = round(-a1/3.0, epsilonDigits)
        return [x, x, x]
    elif R2_Q3 <= epsilon * .5:
        # The epsilon * .5 above ensures that Q3 is not zero.
        theta = acos(max(min(R/sqrt(Q3), 1.0), -1.0))
        rQ2 = -2.0*sqrt(Q)
        a1_3 = a1/3.0
        x0 = rQ2*cos(theta/3.0) - a1_3
        x1 = rQ2*cos((theta+2.0*pi)/3.0) - a1_3
        x2 = rQ2*cos((theta+4.0*pi)/3.0) - a1_3
        x0, x1, x2 = sorted([x0, x1, x2])
        # Merge roots that are close-enough
        if x1 - x0 < epsilon and x2 - x1 < epsilon:
            x0 = x1 = x2 = round((x0 + x1 + x2) / 3., epsilonDigits)
        elif x1 - x0 < epsilon:
            x0 = x1 = round((x0 + x1) / 2., epsilonDigits)
            x2 = round(x2, epsilonDigits)
        elif x2 - x1 < epsilon:
            x0 = round(x0, epsilonDigits)
            x1 = x2 = round((x1 + x2) / 2., epsilonDigits)
        else:
            x0 = round(x0, epsilonDigits)
            x1 = round(x1, epsilonDigits)
            x2 = round(x2, epsilonDigits)
        return [x0, x1, x2]
    else:
        x = pow(sqrt(R2_Q3)+abs(R), 1/3.0)
        x = x + Q/x
        if R >= 0.0:
            x = -x
        x = round(x - a1/3.0, epsilonDigits)
        return [x]


#
# Conversion routines for points to parameters and vice versa
#

def calcQuadraticParameters(pt1, pt2, pt3):
    x2, y2 = pt2
    x3, y3 = pt3
    cx, cy = pt1
    bx = (x2 - cx) * 2.0
    by = (y2 - cy) * 2.0
    ax = x3 - cx - bx
    ay = y3 - cy - by
    return (ax, ay), (bx, by), (cx, cy)


def calcCubicParameters(pt1, pt2, pt3, pt4):
    x2, y2 = pt2
    x3, y3 = pt3
    x4, y4 = pt4
    dx, dy = pt1
    cx = (x2 -dx) * 3.0
    cy = (y2 -dy) * 3.0
    bx = (x3 - x2) * 3.0 - cx
    by = (y3 - y2) * 3.0 - cy
    ax = x4 - dx - cx - bx
    ay = y4 - dy - cy - by
    return (ax, ay), (bx, by), (cx, cy), (dx, dy)


def calcQuadraticPoints(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c
    x1 = cx
    y1 = cy
    x2 = (bx * 0.5) + cx
    y2 = (by * 0.5) + cy
    x3 = ax + bx + cx
    y3 = ay + by + cy
    return (x1, y1), (x2, y2), (x3, y3)


def calcCubicPoints(a, b, c, d):
    ax, ay = a
    bx, by = b
    cx, cy = c
    dx, dy = d
    x1 = dx
    y1 = dy
    x2 = (cx / 3.0) + dx
    y2 = (cy / 3.0) + dy
    x3 = (bx + cx) / 3.0 + x2
    y3 = (by + cy) / 3.0 + y2
    x4 = ax + dx + cx + bx
    y4 = ay + dy + cy + by
    return (x1, y1), (x2, y2), (x3, y3), (x4, y4)


def _segmentrepr(obj):
    """
        >>> _segmentrepr([1, [2, 3], [], [[2, [3, 4], [0.1, 2.2]]]])
        '(1, (2, 3), (), ((2, (3, 4), (0.1, 2.2))))'
    """
    try:
        it = iter(obj)
    except TypeError:
        return "%g" % obj
    else:
        return "(%s)" % ", ".join([_segmentrepr(x) for x in it])


def printSegments(segments):
    """Helper for the doctests, displaying each segment in a list of
    segments on a single line as a tuple.
    """
    for segment in segments:
        print(_segmentrepr(segment))

if __name__ == "__main__":
    import sys
    import doctest
    sys.exit(doctest.testmod().failed)
