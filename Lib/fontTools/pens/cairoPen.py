"""Pen to draw to a Cairo graphics library context."""

from __future__ import annotations

from typing import Any

from fontTools.pens.basePen import BasePen
from fontTools.annotations import Point, GlyphSetMapping


__all__ = ["CairoPen"]


class CairoPen(BasePen):
    """Pen to draw to a Cairo graphics library context."""

    def __init__(self, glyphSet: GlyphSetMapping, context: Any) -> None:
        BasePen.__init__(self, glyphSet)
        self.context = context

    def _moveTo(self, p: Point) -> None:
        self.context.move_to(*p)

    def _lineTo(self, p: Point) -> None:
        self.context.line_to(*p)

    def _curveToOne(self, p1: Point, p2: Point, p3: Point) -> None:
        self.context.curve_to(*p1, *p2, *p3)

    def _closePath(self) -> None:
        self.context.close_path()
