from __future__ import annotations

from typing import Any

from fontTools.annotations import GlyphSetMapping, Point
from fontTools.pens.basePen import BasePen


__all__ = ["WxPen"]


class WxPen(BasePen):
    def __init__(self, glyphSet: GlyphSetMapping, path: Any | None = None) -> None:
        BasePen.__init__(self, glyphSet)
        if path is None:
            import wx

            path = wx.GraphicsRenderer.GetDefaultRenderer().CreatePath()
        self.path = path

    def _moveTo(self, p: Point) -> None:
        self.path.MoveToPoint(*p)

    def _lineTo(self, p: Point) -> None:
        self.path.AddLineToPoint(*p)

    def _curveToOne(self, p1: Point, p2: Point, p3: Point) -> None:
        self.path.AddCurveToPoint(*p1 + p2 + p3)

    def _qCurveToOne(self, p1: Point, p2: Point) -> None:
        self.path.AddQuadCurveToPoint(*p1 + p2)

    def _closePath(self) -> None:
        self.path.CloseSubpath()
