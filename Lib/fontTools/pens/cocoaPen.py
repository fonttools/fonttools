from fontTools.pens.basePen import BasePen


__all__ = ["CocoaPen"]


class CocoaPen(BasePen):

	def __init__(self, glyphSet, path=None):
		BasePen.__init__(self, glyphSet)
		if path is None:
			from AppKit import NSBezierPath
			path = NSBezierPath.bezierPath()
		self.path = path

	def _moveTo(self, point):
		self.path.moveToPoint_(point)

	def _lineTo(self, point):
		self.path.lineToPoint_(point)

	def _curveToOne(self, point1, point2, point3):
		self.path.curveToPoint_controlPoint1_controlPoint2_(point3, point1, point2)

	def _closePath(self):
		self.path.closePath()
