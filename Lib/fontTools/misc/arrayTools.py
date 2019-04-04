#
# Various array and rectangle tools, but mostly rectangles, hence the
# name of this module (not).
#


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import otRound
from numbers import Number
import math
import operator

def calcBounds(array):
    """Return the bounding rectangle of a 2D points array as a tuple:
    (xMin, yMin, xMax, yMax)
    """
    if len(array) == 0:
        return 0, 0, 0, 0
    xs = [x for x, y in array]
    ys = [y for x, y in array]
    return min(xs), min(ys), max(xs), max(ys)

def calcIntBounds(array, round=otRound):
    """Return the integer bounding rectangle of a 2D points array as a
    tuple: (xMin, yMin, xMax, yMax)
    Values are rounded to closest integer towards +Infinity using otRound
    function by default, unless an optional 'round' function is passed.
    """
    return tuple(round(v) for v in calcBounds(array))


def updateBounds(bounds, p, min=min, max=max):
    """Return the bounding recangle of rectangle bounds and point (x, y)."""
    (x, y) = p
    xMin, yMin, xMax, yMax = bounds
    return min(xMin, x), min(yMin, y), max(xMax, x), max(yMax, y)

def pointInRect(p, rect):
    """Return True when point (x, y) is inside rect."""
    (x, y) = p
    xMin, yMin, xMax, yMax = rect
    return (xMin <= x <= xMax) and (yMin <= y <= yMax)

def pointsInRect(array, rect):
    """Find out which points or array are inside rect.
    Returns an array with a boolean for each point.
    """
    if len(array) < 1:
        return []
    xMin, yMin, xMax, yMax = rect
    return [(xMin <= x <= xMax) and (yMin <= y <= yMax) for x, y in array]

def vectorLength(vector):
    """Return the length of the given vector."""
    x, y = vector
    return math.sqrt(x**2 + y**2)

def asInt16(array):
    """Round and cast to 16 bit integer."""
    return [int(math.floor(i+0.5)) for i in array]


def normRect(rect):
    """Normalize the rectangle so that the following holds:
        xMin <= xMax and yMin <= yMax
    """
    (xMin, yMin, xMax, yMax) = rect
    return min(xMin, xMax), min(yMin, yMax), max(xMin, xMax), max(yMin, yMax)

def scaleRect(rect, x, y):
    """Scale the rectangle by x, y."""
    (xMin, yMin, xMax, yMax) = rect
    return xMin * x, yMin * y, xMax * x, yMax * y

def offsetRect(rect, dx, dy):
    """Offset the rectangle by dx, dy."""
    (xMin, yMin, xMax, yMax) = rect
    return xMin+dx, yMin+dy, xMax+dx, yMax+dy

def insetRect(rect, dx, dy):
    """Inset the rectangle by dx, dy on all sides."""
    (xMin, yMin, xMax, yMax) = rect
    return xMin+dx, yMin+dy, xMax-dx, yMax-dy

def sectRect(rect1, rect2):
    """Return a boolean and a rectangle. If the input rectangles intersect, return
    True and the intersecting rectangle. Return False and (0, 0, 0, 0) if the input
    rectangles don't intersect.
    """
    (xMin1, yMin1, xMax1, yMax1) = rect1
    (xMin2, yMin2, xMax2, yMax2) = rect2
    xMin, yMin, xMax, yMax = (max(xMin1, xMin2), max(yMin1, yMin2),
                              min(xMax1, xMax2), min(yMax1, yMax2))
    if xMin >= xMax or yMin >= yMax:
        return False, (0, 0, 0, 0)
    return True, (xMin, yMin, xMax, yMax)

def unionRect(rect1, rect2):
    """Return the smallest rectangle in which both input rectangles are fully
    enclosed. In other words, return the total bounding rectangle of both input
    rectangles.
    """
    (xMin1, yMin1, xMax1, yMax1) = rect1
    (xMin2, yMin2, xMax2, yMax2) = rect2
    xMin, yMin, xMax, yMax = (min(xMin1, xMin2), min(yMin1, yMin2),
                              max(xMax1, xMax2), max(yMax1, yMax2))
    return (xMin, yMin, xMax, yMax)

def rectCenter(rect0):
    """Return the center of the rectangle as an (x, y) coordinate."""
    (xMin, yMin, xMax, yMax) = rect0
    return (xMin+xMax)/2, (yMin+yMax)/2

def intRect(rect1):
    """Return the rectangle, rounded off to integer values, but guaranteeing that
    the resulting rectangle is NOT smaller than the original.
    """
    (xMin, yMin, xMax, yMax) = rect1
    xMin = int(math.floor(xMin))
    yMin = int(math.floor(yMin))
    xMax = int(math.ceil(xMax))
    yMax = int(math.ceil(yMax))
    return (xMin, yMin, xMax, yMax)


class Vector(object):
    """A math-like vector."""

    def __init__(self, values, keep=False):
        self.values = values if keep else list(values)

    def __getitem__(self, index):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return "Vector(%s)" % self.values

    def _vectorOp(self, other, op):
        if isinstance(other, Vector):
            assert len(self.values) == len(other.values)
            a = self.values
            b = other.values
            return [op(a[i], b[i]) for i in range(len(self.values))]
        if isinstance(other, Number):
            return [op(v, other) for v in self.values]
        raise NotImplementedError

    def _scalarOp(self, other, op):
        if isinstance(other, Number):
            return [op(v, other) for v in self.values]
        raise NotImplementedError

    def _unaryOp(self, op):
        return [op(v) for v in self.values]

    def __add__(self, other):
        return Vector(self._vectorOp(other, operator.add), keep=True)
    def __iadd__(self, other):
        self.values = self._vectorOp(other, operator.add)
        return self
    __radd__ = __add__

    def __sub__(self, other):
        return Vector(self._vectorOp(other, operator.sub), keep=True)
    def __isub__(self, other):
        self.values = self._vectorOp(other, operator.sub)
        return self
    def __rsub__(self, other):
        return other + (-self)

    def __mul__(self, other):
        return Vector(self._scalarOp(other, operator.mul), keep=True)
    def __imul__(self, other):
        self.values = self._scalarOp(other, operator.mul)
        return self
    __rmul__ = __mul__

    def __truediv__(self, other):
        return Vector(self._scalarOp(other, operator.div), keep=True)
    def __itruediv__(self, other):
        self.values = self._scalarOp(other, operator.div)
        return self

    def __pos__(self):
        return Vector(self._unaryOp(operator.pos), keep=True)
    def __neg__(self):
        return Vector(self._unaryOp(operator.neg), keep=True)
    def __round__(self):
        return Vector(self._unaryOp(round), keep=True)
    def toInt(self):
        return self.__round__()

    def __eq__(self, other):
        if type(other) == Vector:
            return self.values == other.values
        else:
            return self.values == other
    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        return any(self.values)
    __nonzero__ = __bool__

    def __abs__(self):
        return math.sqrt(sum([x*x for x in self.values]))
    def dot(self, other):
        a = self.values
        b = other.values if type(other) == Vector else b
        assert len(a) == len(b)
        return sum([a[i] * b[i] for i in range(len(a))])


def pairwise(iterable, reverse=False):
    """Iterate over current and next items in iterable, optionally in
    reverse order.

    >>> tuple(pairwise([]))
    ()
    >>> tuple(pairwise([], reverse=True))
    ()
    >>> tuple(pairwise([0]))
    ((0, 0),)
    >>> tuple(pairwise([0], reverse=True))
    ((0, 0),)
    >>> tuple(pairwise([0, 1]))
    ((0, 1), (1, 0))
    >>> tuple(pairwise([0, 1], reverse=True))
    ((1, 0), (0, 1))
    >>> tuple(pairwise([0, 1, 2]))
    ((0, 1), (1, 2), (2, 0))
    >>> tuple(pairwise([0, 1, 2], reverse=True))
    ((2, 1), (1, 0), (0, 2))
    >>> tuple(pairwise(['a', 'b', 'c', 'd']))
    (('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a'))
    >>> tuple(pairwise(['a', 'b', 'c', 'd'], reverse=True))
    (('d', 'c'), ('c', 'b'), ('b', 'a'), ('a', 'd'))
    """
    if not iterable:
        return
    if reverse:
        it = reversed(iterable)
    else:
        it = iter(iterable)
    first = next(it, None)
    a = first
    for b in it:
        yield (a, b)
        a = b
    yield (a, first)


def _test():
    """
    >>> import math
    >>> calcBounds([])
    (0, 0, 0, 0)
    >>> calcBounds([(0, 40), (0, 100), (50, 50), (80, 10)])
    (0, 10, 80, 100)
    >>> updateBounds((0, 0, 0, 0), (100, 100))
    (0, 0, 100, 100)
    >>> pointInRect((50, 50), (0, 0, 100, 100))
    True
    >>> pointInRect((0, 0), (0, 0, 100, 100))
    True
    >>> pointInRect((100, 100), (0, 0, 100, 100))
    True
    >>> not pointInRect((101, 100), (0, 0, 100, 100))
    True
    >>> list(pointsInRect([(50, 50), (0, 0), (100, 100), (101, 100)], (0, 0, 100, 100)))
    [True, True, True, False]
    >>> vectorLength((3, 4))
    5.0
    >>> vectorLength((1, 1)) == math.sqrt(2)
    True
    >>> list(asInt16([0, 0.1, 0.5, 0.9]))
    [0, 0, 1, 1]
    >>> normRect((0, 10, 100, 200))
    (0, 10, 100, 200)
    >>> normRect((100, 200, 0, 10))
    (0, 10, 100, 200)
    >>> scaleRect((10, 20, 50, 150), 1.5, 2)
    (15.0, 40, 75.0, 300)
    >>> offsetRect((10, 20, 30, 40), 5, 6)
    (15, 26, 35, 46)
    >>> insetRect((10, 20, 50, 60), 5, 10)
    (15, 30, 45, 50)
    >>> insetRect((10, 20, 50, 60), -5, -10)
    (5, 10, 55, 70)
    >>> intersects, rect = sectRect((0, 10, 20, 30), (0, 40, 20, 50))
    >>> not intersects
    True
    >>> intersects, rect = sectRect((0, 10, 20, 30), (5, 20, 35, 50))
    >>> intersects
    1
    >>> rect
    (5, 20, 20, 30)
    >>> unionRect((0, 10, 20, 30), (0, 40, 20, 50))
    (0, 10, 20, 50)
    >>> rectCenter((0, 0, 100, 200))
    (50.0, 100.0)
    >>> rectCenter((0, 0, 100, 199.0))
    (50.0, 99.5)
    >>> intRect((0.9, 2.9, 3.1, 4.1))
    (0, 2, 4, 5)
    """

if __name__ == "__main__":
    import sys
    import doctest
    sys.exit(doctest.testmod().failed)
