from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from array import array
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._g_l_y_f import GlyphComponent
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


__all__ = ["TTGlyphPen"]


class TTGlyphPen(AbstractPen):
    """Pen used for drawing to a TrueType glyph."""

    def __init__(self, glyphSet):
        self.glyphSet = glyphSet
        self.init()

    def init(self):
        self.points = []
        self.endPts = []
        self.types = []
        self.components = []

    def _addPoint(self, pt, onCurve):
        self.points.append(pt)
        self.types.append(onCurve)

    def _popPoint(self):
        self.points.pop()
        self.types.pop()

    def _isClosed(self):
        return (
            (not self.points) or
            (self.endPts and self.endPts[-1] == len(self.points) - 1))

    def lineTo(self, pt):
        self._addPoint(pt, 1)

    def moveTo(self, pt):
        assert self._isClosed(), '"move"-type point must begin a new contour.'
        self._addPoint(pt, 1)

    def qCurveTo(self, *points):
        assert len(points) >= 1
        for pt in points[:-1]:
            self._addPoint(pt, 0)

        # last point is None if there are no on-curve points
        if points[-1] is not None:
            self._addPoint(points[-1], 1)

    def closePath(self):
        endPt = len(self.points) - 1

        # ignore anchors (one-point paths)
        if endPt == 0 or (self.endPts and endPt == self.endPts[-1] + 1):
            self._popPoint()
            return

        # if first and last point on this path are the same, remove last
        startPt = 0
        if self.endPts:
            startPt = self.endPts[-1] + 1
        if self.points[startPt] == self.points[endPt]:
            self._popPoint()
            endPt -= 1

        self.endPts.append(endPt)

    def endPath(self):
        # TrueType contours are always "closed"
        self.closePath()

    def addComponent(self, glyphName, transformation):
        self.components.append((glyphName, transformation))

    def glyph(self, componentFlags=0x4):
        assert self._isClosed(), "Didn't close last contour."

        components = []
        for glyphName, transformation in self.components:
            if self.points:
                # can't have both, so decompose the glyph
                tpen = TransformPen(self, transformation)
                self.glyphSet[glyphName].draw(tpen)
                continue

            component = GlyphComponent()
            component.glyphName = glyphName
            if transformation[:4] != (1, 0, 0, 1):
                component.transform = (transformation[:2], transformation[2:4])
            component.x, component.y = transformation[4:]
            component.flags = componentFlags
            components.append(component)

        glyph = Glyph()
        glyph.coordinates = GlyphCoordinates(self.points)
        glyph.endPtsOfContours = self.endPts
        glyph.flags = array("B", self.types)
        self.init()

        if components:
            glyph.components = components
            glyph.numberOfContours = -1
        else:
            glyph.numberOfContours = len(glyph.endPtsOfContours)
            glyph.program = ttProgram.Program()
            glyph.program.fromBytecode(b"")

        return glyph
