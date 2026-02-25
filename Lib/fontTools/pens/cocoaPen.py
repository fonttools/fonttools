from typing import Any

from fontTools.pens.basePen import BasePen
from fontTools.annotations import GlyphSetMapping, Point

__all__ = ["CocoaPen"]


class CocoaPen(BasePen):
    def __init__(self, glyphSet: GlyphSetMapping, path: Any = None) -> None:
        BasePen.__init__(self, glyphSet)
        if path is None:
            from AppKit import NSBezierPath

            path = NSBezierPath.bezierPath()
        self.path = path

    def _moveTo(self, p: Point) -> None:
        self.path.moveToPoint_(p)

    def _lineTo(self, p: Point) -> None:
        self.path.lineToPoint_(p)

    def _curveToOne(self, p1: Point, p2: Point, p3: Point) -> None:
        self.path.curveToPoint_controlPoint1_controlPoint2_(p3, p1, p2)

    def _closePath(self) -> None:
        self.path.closePath()
