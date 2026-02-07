"""Calculate the area of a glyph."""

from __future__ import annotations

from typing import TYPE_CHECKING
from fontTools.pens.basePen import BasePen

if TYPE_CHECKING:
    from fontTools.annotations import GlyphSetMapping, Point

__all__ = ["AreaPen"]


class AreaPen(BasePen):
    def __init__(self, glyphset: GlyphSetMapping | None = None) -> None:
        BasePen.__init__(self, glyphset)
        self.value: float = 0

    def _moveTo(self, p0: Point) -> None:
        self._p0 = self._startPoint = p0

    def _lineTo(self, p1: Point) -> None:
        x0, y0 = self._p0
        x1, y1 = p1
        self.value -= (x1 - x0) * (y1 + y0) * 0.5
        self._p0 = p1

    def _qCurveToOne(self, p1: Point, p2: Point) -> None:
        # https://github.com/Pomax/bezierinfo/issues/44
        p0 = self._p0
        x0, y0 = p0[0], p0[1]
        x1, y1 = p1[0] - x0, p1[1] - y0
        x2, y2 = p2[0] - x0, p2[1] - y0
        self.value -= (x2 * y1 - x1 * y2) / 3
        self._lineTo(p2)
        self._p0 = p2

    def _curveToOne(self, p1: Point, p2: Point, p3: Point) -> None:
        # https://github.com/Pomax/bezierinfo/issues/44
        p0 = self._p0
        x0, y0 = p0[0], p0[1]
        x1, y1 = p1[0] - x0, p1[1] - y0
        x2, y2 = p2[0] - x0, p2[1] - y0
        x3, y3 = p3[0] - x0, p3[1] - y0
        self.value -= (x1 * (-y2 - y3) + x2 * (y1 - 2 * y3) + x3 * (y1 + 2 * y2)) * 0.15
        self._lineTo(p3)
        self._p0 = p3

    def _closePath(self) -> None:
        self._lineTo(self._startPoint)
        del self._p0, self._startPoint

    def _endPath(self) -> None:
        if self._p0 != self._startPoint:
            # Area is not defined for open contours.
            raise NotImplementedError
        del self._p0, self._startPoint
