"""Pen multiplexing drawing to one or more pens."""

from __future__ import annotations

from typing import Iterable

from fontTools.annotations import Point, TransformInput
from fontTools.pens.basePen import AbstractPen


__all__ = ["TeePen"]


class TeePen(AbstractPen):
    """Pen multiplexing drawing to one or more pens.

    Use either as TeePen(pen1, pen2, ...) or TeePen(iterableOfPens)."""

    def __init__(self, *pens: AbstractPen) -> None:
        if len(pens) == 1:
            self.pens: AbstractPen | tuple[AbstractPen, ...] = pens[0]
        else:
            self.pens = pens

    def _iterPens(self) -> Iterable[AbstractPen]:
        # Handle exposed single or tuple of pen objects
        pens = self.pens
        if isinstance(pens, tuple):
            return pens
        return (pens,)

    def moveTo(self, p0: Point) -> None:
        for pen in self._iterPens():
            pen.moveTo(p0)

    def lineTo(self, p1: Point) -> None:
        for pen in self._iterPens():
            pen.lineTo(p1)

    def qCurveTo(self, *points: Point | None) -> None:
        for pen in self._iterPens():
            pen.qCurveTo(*points)

    def curveTo(self, *points: Point) -> None:
        for pen in self._iterPens():
            pen.curveTo(*points)

    def closePath(self) -> None:
        for pen in self._iterPens():
            pen.closePath()

    def endPath(self) -> None:
        for pen in self._iterPens():
            pen.endPath()

    def addComponent(self, glyphName: str, transformation: TransformInput) -> None:
        for pen in self._iterPens():
            pen.addComponent(glyphName, transformation)


if __name__ == "__main__":
    from fontTools.pens.basePen import _TestPen

    pen = TeePen(_TestPen(), _TestPen())
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25))
    pen.closePath()
