from fontTools.pens.basePen import BasePen, PenGlyphSet, PenPoint
from typing import Any, Dict, Optional

__all__ = ["CocoaPen"]


class CocoaPen(BasePen):

	def __init__(self, glyphSet: PenGlyphSet, path: Optional[Any] = None) -> None:
		BasePen.__init__(self, glyphSet)
		if path is None:
			from AppKit import NSBezierPath
			path = NSBezierPath.bezierPath()
		self.path = path

	def _moveTo(self, p: PenPoint) -> None:
		self.path.moveToPoint_(p)

	def _lineTo(self, p: PenPoint) -> None:
		self.path.lineToPoint_(p)

	def _curveToOne(self, p1: PenPoint, p2: PenPoint, p3: PenPoint) -> None:
		self.path.curveToPoint_controlPoint1_controlPoint2_(p3, p1, p2)

	def _closePath(self) -> None:
		self.path.closePath()
