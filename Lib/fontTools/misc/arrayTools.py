#
# This module should move to a more appropriate location
#

import Numeric


def calcBounds(array):
	"""Calculate the bounding rectangle of a 2D array.
	Returns a 4-tuple:
		smallest x, smallest y, largest x, largest y.
	"""
	if len(array) == 0:
		return 0, 0, 0, 0
	xmin, ymin = Numeric.minimum.reduce(array)
	xmax, ymax = Numeric.maximum.reduce(array)
	return xmin, ymin, xmax, ymax


def pointsInRect(array, rect):
	"""Find out which points or array are inside rect. 
	Returns an array with a boolean for each point.
	"""
	if len(array) < 1:
		return []
	lefttop = rect[:2]
	rightbottom = rect[2:]
	condition = Numeric.logical_and(
			Numeric.greater(array, lefttop), 
			Numeric.less(array, rightbottom))
	return Numeric.logical_and.reduce(condition, -1)


def normRect((l, t, r, b)):
	"""XXX doc"""
	return min(l, r), min(t, b), max(l, r), max(t, b)

def scaleRect((l, t, r, b), x, y):
	return l * x, t * y, r * x, b * y

def offsetRect((l, t, r, b), dx, dy):
	return l+dx, t+dy, r+dx, b+dy

def insetRect((l, t, r, b), dx, dy):
	return l+dx, t+dy, r-dx, b-dy

def sectRect((l1, t1, r1, b1), (l2, t2, r2, b2)):
	l, t, r, b = max(l1, l2), max(t1, t2), min(r1, r2), min(b1, b2)
	if l >= r or t >= b:
		return 0, (0, 0, 0, 0)
	return 1, (l, t, r, b)


