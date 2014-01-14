from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.arrayTools import updateBounds, pointInRect, unionRect
from fontTools.misc.bezierTools import calcCubicBounds, calcQuadraticBounds
from fontTools.pens.basePen import BasePen


__all__ = ["BoundsPen", "ControlBoundsPen"]


class ControlBoundsPen(BasePen):

	"""Pen to calculate the "control bounds" of a shape. This is the
	bounding box of all control points, so may be larger than the
	actual bounding box if there are curves that don't have points
	on their extremes.

	When the shape has been drawn, the bounds are available as the
	'bounds' attribute of the pen object. It's a 4-tuple:
		(xMin, yMin, xMax, yMax)
	"""

	def __init__(self, glyphSet):
		BasePen.__init__(self, glyphSet)
		self.bounds = None

	def _moveTo(self, pt):
		bounds = self.bounds
		if bounds:
			self.bounds = updateBounds(bounds, pt)
		else:
			x, y = pt
			self.bounds = (x, y, x, y)

	def _lineTo(self, pt):
		self.bounds = updateBounds(self.bounds, pt)

	def _curveToOne(self, bcp1, bcp2, pt):
		bounds = self.bounds
		bounds = updateBounds(bounds, bcp1)
		bounds = updateBounds(bounds, bcp2)
		bounds = updateBounds(bounds, pt)
		self.bounds = bounds

	def _qCurveToOne(self, bcp, pt):
		bounds = self.bounds
		bounds = updateBounds(bounds, bcp)
		bounds = updateBounds(bounds, pt)
		self.bounds = bounds


class BoundsPen(ControlBoundsPen):

	"""Pen to calculate the bounds of a shape. It calculates the
	correct bounds even when the shape contains curves that don't
	have points on their extremes. This is somewhat slower to compute
	than the "control bounds".

	When the shape has been drawn, the bounds are available as the
	'bounds' attribute of the pen object. It's a 4-tuple:
		(xMin, yMin, xMax, yMax)
	"""

	def _curveToOne(self, bcp1, bcp2, pt):
		bounds = self.bounds
		bounds = updateBounds(bounds, pt)
		if not pointInRect(bcp1, bounds) or not pointInRect(bcp2, bounds):
			bounds = unionRect(bounds, calcCubicBounds(
					self._getCurrentPoint(), bcp1, bcp2, pt))
		self.bounds = bounds

	def _qCurveToOne(self, bcp, pt):
		bounds = self.bounds
		bounds = updateBounds(bounds, pt)
		if not pointInRect(bcp, bounds):
			bounds = unionRect(bounds, calcQuadraticBounds(
					self._getCurrentPoint(), bcp, pt))
		self.bounds = bounds


if __name__ == "__main__":
	def draw(pen):
		pen.moveTo((0, 0))
		pen.lineTo((0, 100))
		pen.qCurveTo((50, 75), (60, 50), (50, 25), (0, 0))
		pen.curveTo((-50, 25), (-60, 50), (-50, 75), (0, 100))
		pen.closePath()

	pen = ControlBoundsPen(None)
	draw(pen)
	print(pen.bounds)

	pen = BoundsPen(None)
	draw(pen)
	print(pen.bounds)
