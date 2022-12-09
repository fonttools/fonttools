"""Pen multiplexing drawing to one or more pens."""
from typing import Optional, Tuple
from fontTools.pens.basePen import AbstractPen, PenPoint


__all__ = ["TeePen"]


class TeePen(AbstractPen):
	"""Pen multiplexing drawing to one or more pens.

	Use either as TeePen(pen1, pen2, ...) or TeePen(iterableOfPens)."""

	def __init__(self, *pens) -> None:
		if len(pens) == 1:
			pens = pens[0]
		self.pens = pens

	def moveTo(self, p0: PenPoint) -> None:
		for pen in self.pens:
			pen.moveTo(p0)

	def lineTo(self, p1: PenPoint) -> None:
		for pen in self.pens:
			pen.lineTo(p1)

	def qCurveTo(self, *points: Optional[PenPoint]) -> None:
		for pen in self.pens:
			pen.qCurveTo(*points)

	def curveTo(self, *points: PenPoint) -> None:
		for pen in self.pens:
			pen.curveTo(*points)

	def closePath(self) -> None:
		for pen in self.pens:
			pen.closePath()

	def endPath(self) -> None:
		for pen in self.pens:
			pen.endPath()

	def addComponent(
		self,
		glyphName: str,
		transformation: Tuple[float, float, float, float, float, float],
	) -> None:
		for pen in self.pens:
			pen.addComponent(glyphName, transformation)


if __name__ == "__main__":
	from fontTools.pens.basePen import _TestPen
	pen = TeePen(_TestPen(), _TestPen())
	pen.moveTo((0, 0))
	pen.lineTo((0, 100))
	pen.curveTo((50, 75), (60, 50), (50, 25))
	pen.closePath()
