from fontTools.pens.basePen import AbstractPen


__all__ = ["TransformPen"]


class TransformPen(AbstractPen):

	"""Pen that passes transforms all coordinates, and passes them
	to another pen.
	"""

	def __init__(self, outPen, transformation):
		if not hasattr(transformation, "transformPoint"):
			from fontTools.misc.transform import Transform
			transformation = Transform(*transformation)
		self._transformation = transformation
		self._transformPoint = transformation.transformPoint
		self._outPen = outPen
		self._stack = []

	def moveTo(self, pt):
		self._outPen.moveTo(self._transformPoint(pt))

	def lineTo(self, pt):
		self._outPen.lineTo(self._transformPoint(pt))

	def curveTo(self, *points):
		self._outPen.curveTo(*self._transformPoints(points))

	def qCurveTo(self, *points):
		if points[-1] is None:
			points = self._transformPoints(points[:-1]) + [None]
		else:
			points = self._transformPoints(points)
		self._outPen.qCurveTo(*points)

	def _transformPoints(self, points):
		new = []
		transformPoint = self._transformPoint
		for pt in points:
			new.append(transformPoint(pt))
		return new

	def closePath(self):
		self._outPen.closePath()

	def addComponent(self, glyphName, transformation):
		transformation = self._transformation.transform(transformation)
		self._outPen.addComponent(glyphName, transformation)


if __name__ == "__main__":
	from fontTools.pens.basePen import _TestPen
	pen = TransformPen(_TestPen(None), (2, 0, 0.5, 2, -10, 0))
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.curveTo((50, 75), (60, 50), (50, 25), (0, 0))
	pen.closePath()
