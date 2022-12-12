"""Pen to draw to a Cairo graphics library context."""

from typing import Any, Dict, Optional
from fontTools.pens.basePen import BasePen, PenError, PenGlyphSet, PenPoint


__all__ = ["CairoPen"]


class CairoPen(BasePen):
    """Pen to draw to a Cairo graphics library context."""

    def __init__(self, glyphSet: PenGlyphSet = None, context: Optional[Any] = None) -> None:
        BasePen.__init__(self, glyphSet)
        if context is None:
            raise PenError("Must supply a context")
        self.context = context

    def _moveTo(self, p: PenPoint) -> None:
        self.context.move_to(*p)

    def _lineTo(self, p: PenPoint) -> None:
        self.context.line_to(*p)

    def _curveToOne(self, p1: PenPoint, p2: PenPoint, p3: PenPoint) -> None:
        self.context.curve_to(*p1, *p2, *p3)

    def _closePath(self) -> None:
        self.context.close_path()
