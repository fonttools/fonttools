#
# Various array and rectangle tools, but mostly rectangles, hence the
# name of this module (not).
#


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import math

def calcBounds(array):
    """Return the bounding rectangle of a 2D points array as a tuple:
    (xMin, yMin, xMax, yMax)
    """
    if len(array) == 0:
        return 0, 0, 0, 0
    xs = [x for x, y in array]
    ys = [y for x, y in array]
    return min(xs), min(ys), max(xs), max(ys)

def calcIntBounds(array):
    """Return the integer bounding rectangle of a 2D points array as a
    tuple: (xMin, yMin, xMax, yMax)
    """
    xMin, yMin, xMax, yMax = calcBounds(array)
    xMin = int(math.floor(xMin))
    xMax = int(math.ceil(xMax))
    yMin = int(math.floor(yMin))
    yMax = int(math.ceil(yMax))
    return xMin, yMin, xMax, yMax


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
    import doctest
    doctest.testmod()
