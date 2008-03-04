"""fontTools.misc.bezierTools.py -- tools for working with bezier path segments."""


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
import numpy

epsilon = 1e-12


def calcQuadraticBounds(pt1, pt2, pt3):
	"""Return the bounding rectangle for a qudratic bezier segment.
	pt1 and pt3 are the "anchor" points, pt2 is the "handle".

		>>> calcQuadraticBounds((0, 0), (50, 100), (100, 0))
		(0.0, 0.0, 100.0, 50.0)
		>>> calcQuadraticBounds((0, 0), (100, 0), (100, 100))
		(0.0, 0.0, 100.0, 100.0)
	"""
	a, b, c = calcQuadraticParameters(pt1, pt2, pt3)
	# calc first derivative
	ax, ay = a * 2
	bx, by = b
	roots = []
	if ax != 0:
		roots.append(-bx/ax)
	if ay != 0:
		roots.append(-by/ay)
	points = [a*t*t + b*t + c for t in roots if 0 <= t < 1] + [pt1, pt3]
	return calcBounds(points)


def calcCubicBounds(pt1, pt2, pt3, pt4):
	"""Return the bounding rectangle for a cubic bezier segment.
	pt1 and pt4 are the "anchor" points, pt2 and pt3 are the "handles".

		>>> calcCubicBounds((0, 0), (25, 100), (75, 100), (100, 0))
		(0.0, 0.0, 100.0, 75.0)
		>>> calcCubicBounds((0, 0), (50, 0), (100, 50), (100, 100))
		(0.0, 0.0, 100.0, 100.0)
		>>> calcCubicBounds((50, 0), (0, 100), (100, 100), (50, 0))
		(35.5662432703, 0.0, 64.4337567297, 75.0)
	"""
	a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
	# calc first derivative
	ax, ay = a * 3.0
	bx, by = b * 2.0
	cx, cy = c
	xRoots = [t for t in solveQuadratic(ax, bx, cx) if 0 <= t < 1]
	yRoots = [t for t in solveQuadratic(ay, by, cy) if 0 <= t < 1]
	roots = xRoots + yRoots
	
	points = [(a*t*t*t + b*t*t + c * t + d) for t in roots] + [pt1, pt4]
	return calcBounds(points)


def splitLine(pt1, pt2, where, isHorizontal):
	"""Split the line between pt1 and pt2 at position 'where', which
	is an x coordinate if isHorizontal is False, a y coordinate if
	isHorizontal is True. Return a list of two line segments if the
	line was successfully split, or a list containing the original
	line.

		>>> printSegments(splitLine((0, 0), (100, 100), 50, True))
		((0, 0), (50.0, 50.0))
		((50.0, 50.0), (100, 100))
		>>> printSegments(splitLine((0, 0), (100, 100), 100, True))
		((0, 0), (100, 100))
		>>> printSegments(splitLine((0, 0), (100, 100), 0, True))
		((0, 0), (0.0, 0.0))
		((0.0, 0.0), (100, 100))
		>>> printSegments(splitLine((0, 0), (100, 100), 0, False))
		((0, 0), (0.0, 0.0))
		((0.0, 0.0), (100, 100))
	"""
	pt1, pt2 = numpy.array((pt1, pt2))
	a = (pt2 - pt1)
	b = pt1
	ax = a[isHorizontal]
	if ax == 0:
		return [(pt1, pt2)]
	t = float(where - b[isHorizontal]) / ax
	if 0 <= t < 1:
		midPt = a * t + b
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
		((0.0, 0.0), (25.0, 50.0), (50.0, 50.0))
		((50.0, 50.0), (75.0, 50.0), (100.0, 0.0))
		>>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 25, False))
		((0.0, 0.0), (12.5, 25.0), (25.0, 37.5))
		((25.0, 37.5), (62.5, 75.0), (100.0, 0.0))
		>>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 25, True))
		((0.0, 0.0), (7.32233047034, 14.6446609407), (14.6446609407, 25.0))
		((14.6446609407, 25.0), (50.0, 75.0), (85.3553390593, 25.0))
		((85.3553390593, 25.0), (92.6776695297, 14.6446609407), (100.0, -7.1054273576e-15))
		>>> # XXX I'm not at all sure if the following behavior is desirable:
		>>> printSegments(splitQuadratic((0, 0), (50, 100), (100, 0), 50, True))
		((0.0, 0.0), (25.0, 50.0), (50.0, 50.0))
		((50.0, 50.0), (50.0, 50.0), (50.0, 50.0))
		((50.0, 50.0), (75.0, 50.0), (100.0, 0.0))
	"""
	a, b, c = calcQuadraticParameters(pt1, pt2, pt3)
	solutions = solveQuadratic(a[isHorizontal], b[isHorizontal],
		c[isHorizontal] - where)
	solutions = [t for t in solutions if 0 <= t < 1]
	solutions.sort()
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
		((0.0, 0.0), (12.5, 50.0), (31.25, 75.0), (50.0, 75.0))
		((50.0, 75.0), (68.75, 75.0), (87.5, 50.0), (100.0, 0.0))
		>>> printSegments(splitCubic((0, 0), (25, 100), (75, 100), (100, 0), 25, True))
		((0.0, 0.0), (2.2937927384, 9.17517095361), (4.79804488188, 17.5085042869), (7.47413641001, 25.0))
		((7.47413641001, 25.0), (31.2886200204, 91.6666666667), (68.7113799796, 91.6666666667), (92.52586359, 25.0))
		((92.52586359, 25.0), (95.2019551181, 17.5085042869), (97.7062072616, 9.17517095361), (100.0, 1.7763568394e-15))
	"""
	a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
	solutions = solveCubic(a[isHorizontal], b[isHorizontal], c[isHorizontal],
		d[isHorizontal] - where)
	solutions = [t for t in solutions if 0 <= t < 1]
	solutions.sort()
	if not solutions:
		return [(pt1, pt2, pt3, pt4)]
	return _splitCubicAtT(a, b, c, d, *solutions)


def splitQuadraticAtT(pt1, pt2, pt3, *ts):
	"""Split the quadratic curve between pt1, pt2 and pt3 at one or more
	values of t. Return a list of curve segments.

		>>> printSegments(splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5))
		((0.0, 0.0), (25.0, 50.0), (50.0, 50.0))
		((50.0, 50.0), (75.0, 50.0), (100.0, 0.0))
		>>> printSegments(splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5, 0.75))
		((0.0, 0.0), (25.0, 50.0), (50.0, 50.0))
		((50.0, 50.0), (62.5, 50.0), (75.0, 37.5))
		((75.0, 37.5), (87.5, 25.0), (100.0, 0.0))
	"""
	a, b, c = calcQuadraticParameters(pt1, pt2, pt3)
	return _splitQuadraticAtT(a, b, c, *ts)


def splitCubicAtT(pt1, pt2, pt3, pt4, *ts):
	"""Split the cubic curve between pt1, pt2, pt3 and pt4 at one or more
	values of t. Return a list of curve segments.

		>>> printSegments(splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5))
		((0.0, 0.0), (12.5, 50.0), (31.25, 75.0), (50.0, 75.0))
		((50.0, 75.0), (68.75, 75.0), (87.5, 50.0), (100.0, 0.0))
		>>> printSegments(splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5, 0.75))
		((0.0, 0.0), (12.5, 50.0), (31.25, 75.0), (50.0, 75.0))
		((50.0, 75.0), (59.375, 75.0), (68.75, 68.75), (77.34375, 56.25))
		((77.34375, 56.25), (85.9375, 43.75), (93.75, 25.0), (100.0, 0.0))
	"""
	a, b, c, d = calcCubicParameters(pt1, pt2, pt3, pt4)
	return _splitCubicAtT(a, b, c, d, *ts)


def _splitQuadraticAtT(a, b, c, *ts):
	ts = list(ts)
	segments = []
	ts.insert(0, 0.0)
	ts.append(1.0)
	for i in range(len(ts) - 1):
		t1 = ts[i]
		t2 = ts[i+1]
		delta = (t2 - t1)
		# calc new a, b and c
		a1 = a * delta**2
		b1 = (2*a*t1 + b) * delta
		c1 = a*t1**2 + b*t1 + c
		pt1, pt2, pt3 = calcQuadraticPoints(a1, b1, c1)
		segments.append((pt1, pt2, pt3))
	return segments


def _splitCubicAtT(a, b, c, d, *ts):
	ts = list(ts)
	ts.insert(0, 0.0)
	ts.append(1.0)
	segments = []
	for i in range(len(ts) - 1):
		t1 = ts[i]
		t2 = ts[i+1]
		delta = (t2 - t1)
		# calc new a, b, c and d
		a1 = a * delta**3
		b1 = (3*a*t1 + b) * delta**2
		c1 = (2*b*t1 + c + 3*a*t1**2) * delta
		d1 = a*t1**3 + b*t1**2 + c*t1 + d
		pt1, pt2, pt3, pt4 = calcCubicPoints(a1, b1, c1, d1)
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


def solveCubic(a, b, c, d,
		abs=abs, pow=pow, sqrt=sqrt, cos=cos, acos=acos, pi=pi):
	"""Solve a cubic equation where a, b, c and d are real.
	    a*x*x*x + b*x*x + c*x + d = 0
	This function returns a list of roots. Note that the returned list
	is neither guaranteed to be sorted nor to contain unique values!
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
	R2_Q3 = R*R - Q*Q*Q

	if R2_Q3 < 0:
		theta = acos(R/sqrt(Q*Q*Q))
		rQ2 = -2.0*sqrt(Q)
		x0 = rQ2*cos(theta/3.0) - a1/3.0
		x1 = rQ2*cos((theta+2.0*pi)/3.0) - a1/3.0
		x2 = rQ2*cos((theta+4.0*pi)/3.0) - a1/3.0
		return [x0, x1, x2]
	else:
		if Q == 0 and R == 0:
			x = 0
		else:
			x = pow(sqrt(R2_Q3)+abs(R), 1/3.0)
			x = x + Q/x
		if R >= 0.0:
			x = -x
		x = x - a1/3.0
		return [x]


#
# Conversion routines for points to parameters and vice versa
#

def calcQuadraticParameters(pt1, pt2, pt3):
	pt1, pt2, pt3 = numpy.array((pt1, pt2, pt3))
	c = pt1
	b = (pt2 - c) * 2.0
	a = pt3 - c - b
	return a, b, c


def calcCubicParameters(pt1, pt2, pt3, pt4):
	pt1, pt2, pt3, pt4 = numpy.array((pt1, pt2, pt3, pt4))
	d = pt1
	c = (pt2 - d) * 3.0
	b = (pt3 - pt2) * 3.0 - c
	a = pt4 - d - c - b
	return a, b, c, d


def calcQuadraticPoints(a, b, c):
	pt1 = c
	pt2 = (b * 0.5) + c
	pt3 = a + b + c
	return pt1, pt2, pt3


def calcCubicPoints(a, b, c, d):
	pt1 = d
	pt2 = (c / 3.0) + d
	pt3 = (b + c) / 3.0 + pt2
	pt4 = a + d + c + b
	return pt1, pt2, pt3, pt4


def _segmentrepr(obj):
	"""
		>>> _segmentrepr([1, [2, 3], [], [[2, [3, 4], numpy.array([0.1, 2.2])]]])
		'(1, (2, 3), (), ((2, (3, 4), (0.1, 2.2))))'
	"""
	try:
		it = iter(obj)
	except TypeError:
		return str(obj)
	else:
		return "(%s)" % ", ".join([_segmentrepr(x) for x in it])


def printSegments(segments):
	"""Helper for the doctests, displaying each segment in a list of
	segments on a single line as a tuple.
	"""
	for segment in segments:
		print _segmentrepr(segment)


if __name__ == "__main__":
	import doctest
	doctest.testmod()
