from fontTools.pens.basePen import BasePen


__all__ = ["CocoaPen"]


class CocoaPen(BasePen):

	def __init__(self, glyphSet, path=None):
		BasePen.__init__(self, glyphSet)
		if path is None:
			from AppKit import NSBezierPath
			path = NSBezierPath.bezierPath()
		self.path = path

	def _moveTo(self, (x, y)):
		self.path.moveToPoint_((x, y))

	def _lineTo(self, (x, y)):
		self.path.lineToPoint_((x, y))

	def _curveToOne(self, (x1, y1), (x2, y2), (x3, y3)):
		self.path.curveToPoint_controlPoint1_controlPoint2_((x3, y3), (x1, y1), (x2, y2))

	def _closePath(self):
		self.path.closePath()
