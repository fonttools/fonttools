"""Pen multiplexing drawing to one or more pens."""
from __future__ import annotations
from typing import Sequence
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.typings import Point, Transformation


__all__ = ["TeePen"]


class TeePen(AbstractPen):
    """Pen multiplexing drawing to one or more pens.

    Use either as TeePen(pen1, pen2, ...) or TeePen(iterableOfPens)."""

    def __init__(self, *pens: AbstractPen | Sequence[AbstractPen]) -> None:
        if len(pens) == 1:
            pens = pens[0]  # type: ignore
        self.pens: Sequence[AbstractPen] = pens  # type: ignore

    def moveTo(self, p0: Point) -> None:
        for pen in self.pens:
            pen.moveTo(p0)

    def lineTo(self, p1: Point) -> None:
        for pen in self.pens:
            pen.lineTo(p1)

    def qCurveTo(self, *points: Point | None) -> None:
        for pen in self.pens:
            pen.qCurveTo(*points)

    def curveTo(self, *points: Point) -> None:
        for pen in self.pens:
            pen.curveTo(*points)

    def closePath(self) -> None:
        for pen in self.pens:
            pen.closePath()

    def endPath(self) -> None:
        for pen in self.pens:
            pen.endPath()

    def addComponent(self, glyphName: str, transformation: Transformation) -> None:
        for pen in self.pens:
            pen.addComponent(glyphName, transformation)


if __name__ == "__main__":
    from fontTools.pens.basePen import _TestPen

    pen = TeePen(_TestPen(), _TestPen())
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25))
    pen.closePath()

    pen = TeePen([_TestPen(), _TestPen()])
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25))
    pen.closePath()
