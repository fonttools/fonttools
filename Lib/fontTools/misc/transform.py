"""Affine 2D transformation class."""


_EPSILON = 1e-15
_ONE_EPSILON = 1 - _EPSILON
_MINUS_ONE_EPSILON = -1 + _EPSILON


def _normSinCos(v):
	if abs(v) < _EPSILON:
		v = 0
	elif v > _ONE_EPSILON:
		v = 1
	elif v < _MINUS_ONE_EPSILON:
		v = -1
	return v


class Transform:
	
	"""2x2 transformation matrix plus offset, a.k.a. Affine transform.
	Transform instances are "immutable": all transforming methods, eg.
	rotate(), return a new Transform instance."""
	
	def __init__(self, xx=1, xy=0, yx=0, yy=1, dx=0, dy=0):
		self.__affine = xx, xy, yx, yy, dx, dy
	
	def transformPoint(self, (x, y)):
		"""Transform a point."""
		xx, xy, yx, yy, dx, dy = self.__affine
		return (xx*x + yx*y + dx, xy*x + yy*y + dy)
	
	def translate(self, x=0, y=0):
		return self.transform((1, 0, 0, 1, x, y))
	
	def scale(self, x=1, y=None):
		if y is None:
			y = x
		return self.transform((x, 0, 0, y, 0, 0))
	
	def rotate(self, angle):
		import math
		c = _normSinCos(math.cos(angle))
		s = _normSinCos(math.sin(angle))
		return self.transform((c, s, -s, c, 0, 0))
	
	def skew(self, x=0, y=0):
		import math
		return self.transform((1, math.tan(y), math.tan(x), 1, 0, 0))
	
	def transform(self, other):
		xx1, xy1, yx1, yy1, dx1, dy1 = other
		xx2, xy2, yx2, yy2, dx2, dy2 = self.__affine
		return self.__class__(
				xx1*xx2 + xy1*yx2,
				xx1*xy2 + xy1*yy2,
				yx1*xx2 + yy1*yx2,
				yx1*xy2 + yy1*yy2,
				xx2*dx1 + yx2*dy1 + dx2,
				xy2*dx1 + yy2*dy1 + dy2)
	
	def reverseTransform(self, other):
		xx1, xy1, yx1, yy1, dx1, dy1 = self.__affine
		xx2, xy2, yx2, yy2, dx2, dy2 = other
		return self.__class__(
				xx1*xx2 + xy1*yx2,
				xx1*xy2 + xy1*yy2,
				yx1*xx2 + yy1*yx2,
				yx1*xy2 + yy1*yy2,
				xx2*dx1 + yx2*dy1 + dx2,
				xy2*dx1 + yy2*dy1 + dy2)
	
	def inverse(self):
		"Return the inverse transform."
		if self.__affine == (1, 0, 0, 1, 0, 0):
			return self
		xx, xy, yx, yy, dx, dy = self.__affine
		det = float(xx*yy - yx*xy)
		xx, xy, yx, yy = yy/det, -xy/det, -yx/det, xx/det
		dx, dy = -xx*dx - yx*dy, -xy*dx - yy*dy
		return self.__class__(xx, xy, yx, yy, dx, dy)
	
	def toPS(self):
		return "[%s %s %s %s %s %s]" % self.__affine
	
	def __len__(self):
		return 6
	
	def __getitem__(self, index):
		return self.__affine[index]
	
	def __getslice__(self, i, j):
		return self.__affine[i:j]
	
	def __cmp__(self, other):
		xx1, xy1, yx1, yy1, dx1, dy1 = self.__affine
		xx2, xy2, yx2, yy2, dx2, dy2 = other
		return cmp((xx1, xy1, yx1, yy1, dx1, dy1),
				(xx2, xy2, yx2, yy2, dx2, dy2))
	
	def __hash__(self):
		return hash(self.__affine)
	
	def __repr__(self):
		return "<%s [%s %s %s %s %s %s]>" % ((self.__class__.__name__,)
				 + tuple(map(str, self.__affine)))


Identity = Transform()

def Offset(x=0, y=0):
	return Transform(1, 0, 0, 1, x, y)

def Scale(x, y=None):
	if y is None:
		y = x
	return Transform(x, 0, 0, y, 0, 0)
