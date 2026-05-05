from __future__ import annotations

from typing import Any
from fontTools.annotations import GlyphSetMapping, Point
from fontTools.pens.basePen import BasePen


__all__ = ["QtPen"]


class QtPen(BasePen):
    def __init__(self, glyphSet: GlyphSetMapping, path: Any | None = None):
        BasePen.__init__(self, glyphSet)
        if path is None:
            from PyQt5.QtGui import QPainterPath

            path = QPainterPath()
        self.path = path

    def _moveTo(self, p: Point) -> None:
        self.path.moveTo(*p)

    def _lineTo(self, p: Point) -> None:
        self.path.lineTo(*p)

    def _curveToOne(self, p1: Point, p2: Point, p3: Point) -> None:
        self.path.cubicTo(*p1, *p2, *p3)

    def _qCurveToOne(self, p1: Point, p2: Point) -> None:
        self.path.quadTo(*p1, *p2)

    def _closePath(self) -> None:
        self.path.closeSubpath()
