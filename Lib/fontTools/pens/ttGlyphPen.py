from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from array import array
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._g_l_y_f import GlyphComponent
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


__all__ = ["TTGlyphPen"]


class TTGlyphPen(BasePen):
    """Pen used for drawing to a TrueType glyph."""

    def __init__(self, glyphSet):
        self.points = []
        self.endPts = []
        self.types = []
        self.components = []

    def _addPoint(self, pt, onCurve):
        self.points.append([int(coord) for coord in pt])
        self.types.append(onCurve)

    def _lineTo(self, pt):
        self._addPoint(pt, 1)

    def _moveTo(self, pt):
        assert (not self.points) or (self.endPts[-1] == len(self.points) - 1), (
            '"move"-type point must begin a new contour.')
        self.lineTo(pt)

    def _qCurveToOne(self, pt1, pt2):
        self._addPoint(pt1, 0)
        self._addPoint(pt2, 1)

    def _closePath(self):
        endPt = len(self.points) - 1

        # ignore anchors
        if endPt == 0 or (self.endPts and endPt == self.endPts[-1] + 1):
            self.points.pop()
            self.types.pop()
            return

        self.endPts.append(endPt)

    def _endPath(self):
        # TrueType contours are always "closed"
        self.closePath()

    def addComponent(self, glyphName, transformation):
        self.components.append((glyphName, transformation))

    def glyph(self):
        glyph = Glyph()

        components = []
        for glyphName, transformation in self.components:
            if self.points:
                # can't have both, so decompose the glyph
                tpen = TransformPen(self, transformation)
                self.glyphSet[glyphName].draw(tpen)
                continue

            component = GlyphComponent()
            component.glyphName = glyphName
            component.transform = (transformation[:2], transformation[2:4])
            component.x, component.y = [int(n) for n in transformation[4:]]
            component.flags = 0
            components.append(component)

        glyph.coordinates = GlyphCoordinates(self.points)
        glyph.endPtsOfContours = self.endPts
        glyph.flags = array("B", self.types)

        if components:
            glyph.components = components
            glyph.numberOfContours = -1
        else:
            glyph.numberOfContours = len(glyph.endPtsOfContours)

        glyph.program = ttProgram.Program()
        glyph.program.fromBytecode("")

        return glyph
