"""fontTools.pens.basePen.py -- Tools and base classes to build pen objects.

The Pen Protocol

A Pen is a kind of object that standardizes the way how to "draw" outlines:
it is a middle man between an outline and a drawing. In other words:
it is an abstraction for drawing outlines, making sure that outline objects
don't need to know the details about how and where they're being drawn, and
that drawings don't need to know the details of how outlines are stored.

The most basic pattern is this:

    outline.draw(pen)  # 'outline' draws itself onto 'pen'

Pens can be used to render outlines to the screen, but also to construct
new outlines. Eg. an outline object can be both a drawable object (it has a
draw() method) as well as a pen itself: you *build* an outline using pen
methods.

The AbstractPen class defines the Pen protocol.

The BasePen class is a base implementation useful for drawing pens. See the
comments in that class for which methods you need to override.
"""

__all__ = ["AbstractPen", "BasePen"]


class AbstractPen:

	def moveTo(self, pt):
		"""Begin a new sub path, set the current point to 'pt'."""
		raise NotImplementedError

	def lineTo(self, pt):
		"""Draw a straight line."""
		raise NotImplementedError

	def curveTo(self, *points):
		"""Draw a curve with an *arbitrary* number of control points.

		Let n be the number of control points (which is the number of
		arguments to this call minus 1). If n==2, a plain vanilla cubic
		bezier is drawn. If n==1, we fall back to a quadratic segment and
		if n==0 we draw a straight line. It gets interesting when n>2:
		n-1 PostScript-style cubic segments will be drawn as if it were
		one curve.

		The conversion algorithm used for n>2 is inspired by NURB
		splines, and is conceptually equivalent to the TrueType "implied
		points" principle. See also qCurve().
		"""
		raise NotImplementedError

	def qCurveTo(self, *points):
		"""Draw a whole string of quadratic curve segments.

		This implements TrueType-style curves, breaking up curves using
		implied points: between each two consequtive off-curve points,
		there is one 'implied' point exactly in the middle between them.

		'points' is a sequence of at least two points. Just like with
		any segment drawing function, the first and the last point are
		treated as onCurve, the rest as offCurve.
		"""
		raise NotImplementedError

	def closePath(self):
		"""Close the current sub path."""
		pass

	def addComponent(self, glyphName, transformation):
		"""Add a sub glyph."""
		raise NotImplementedError


class BasePen(AbstractPen):

	"""Base class for drawing pens."""

	def __init__(self, glyphSet):
		self.glyphSet = glyphSet
		self.__currentPoint = None

	# must override

	def _moveTo(self, pt):
		raise NotImplementedError

	def _lineTo(self, pt):
		raise NotImplementedError

	def _curveToOne(self, pt1, pt2, pt3):
		raise NotImplementedError

	# may override

	def _closePath(self):
		pass

	def _qCurveToOne(self, pt1, pt2):
		"""This method implements the basic quadratic curve type. The
		default implementation delegates the work to the cubic curve
		function. Optionally override with a native implementation.
		"""
		pt0x, pt0y = self.__currentPoint
		pt1x, pt1y = pt1
		pt2x, pt2y = pt2
		mid1x = pt0x + 0.66666666666666667 * (pt1x - pt0x)
		mid1y = pt0y + 0.66666666666666667 * (pt1y - pt0y)
		mid2x = pt2x + 0.66666666666666667 * (pt1x - pt2x)
		mid2y = pt2y + 0.66666666666666667 * (pt1y - pt2y)
		self._curveToOne((mid1x, mid1y), (mid2x, mid2y), pt2)

	def addComponent(self, glyphName, transformation):
		"""This default implementation simply transforms the points
		of the base glyph and draws it onto self.
		"""
		from fontTools.pens.transformPen import TransformPen
		tPen = TransformPen(self, transformation)
		self.glyphSet[glyphName].draw(tPen)

	# don't override

	def _getCurrentPoint(self):
		"""Return the current point. This is not part of the public
		interface, yet is useful for subclasses.
		"""
		return self.__currentPoint

	def closePath(self):
		self._closePath()
		self.__currentPoint = None

	def moveTo(self, pt):
		self._moveTo(pt)
		self.__currentPoint = pt

	def lineTo(self, pt):
		self._lineTo(pt)
		self.__currentPoint = pt

	def curveTo(self, *points):
		n = len(points) - 1  # 'n' is the number of control points
		assert n >= 0
		if n == 2:
			# The common case, we have exactly two BCP's, so this is a standard
			# cubic bezier.
			self._curveToOne(*points)
			self.__currentPoint = points[-1]
		elif n > 2:
			# n is the number of control points; split curve into n-1 cubic
			# bezier segments. The algorithm used here is inspired by NURB
			# splines and the TrueType "implied point" principle, and ensures
			# the smoothest possible connection between two curve segments,
			# with no disruption in the curvature. It is practical since it
			# allows one to construct multiple bezier segments with a much
			# smaller amount of points.
			pt1, pt2, pt3 = points[0], None, None
			for i in range(2, n+1):
				# calculate points in between control points.
				nDivisions = min(i, 3, n-i+2)
				d = float(nDivisions)
				for j in range(1, nDivisions):
					factor = j / d
					temp1 = points[i-1]
					temp2 = points[i-2]
					temp = (temp2[0] + factor * (temp1[0] - temp2[0]),
					        temp2[1] + factor * (temp1[1] - temp2[1]))
					if pt2 is None:
						pt2 = temp
					else:
						pt3 = (0.5 * (pt2[0] + temp[0]), 0.5 * (pt2[1] + temp[1]))
						self._curveToOne(pt1, pt2, pt3)
						pt1, pt2, pt3 = temp, None, None
			self._curveToOne(pt1, points[-2], points[-1])
			self.__currentPoint = points[-1]
		elif n == 1:
			self._qCurveOne(*points)
		elif n == 0:
			self.lineTo(points[0])
		else:
			raise AssertionError, "can't get there from here"

	def qCurveTo(self, *points):
		n = len(points) - 1  # 'n' is the number of control points
		assert n >= 0
		if n > 0:
			# Split the string of points into discrete quadratic curve segments.
			# Between any two consecutive off-curve points there's an implied
			# on-curve point exactly in the middle. This is where the segment splits.
			_qCurveToOne = self._qCurveToOne
			for i in range(len(points) - 2):
				x, y = points[i]
				nx, ny = points[i+1]
				impliedPt = (0.5 * (x + nx), 0.5 * (y + ny))
				_qCurveToOne(points[i], impliedPt)
				self.__currentPoint = impliedPt
			_qCurveToOne(points[-2], points[-1])
			self.__currentPoint = points[-1]
		else:
			self.lineTo(points[0])


class _TestPen(BasePen):
	def _moveTo(self, pt):
		print "%s %s moveto" % (pt[0], pt[1])
	def _lineTo(self, pt):
		print "%s %s lineto" % (pt[0], pt[1])
	def _curveToOne(self, bcp1, bcp2, pt):
		print "%s %s %s %s %s %s curveto" % (bcp1[0], bcp1[1], bcp2[0], bcp2[1], pt[0], pt[1])
	def _closePath(self):
		print "closepath"


if __name__ == "__main__":
	pen = _TestPen(None)
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.qCurveTo((50, 75), (60, 50), (50, 25), (0, 0))
	pen.closePath()

	pen = _TestPen(None)
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.curveTo((50, 75), (60, 50), (50, 25), (0, 0))
	pen.closePath()
