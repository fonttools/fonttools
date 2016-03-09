from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from array import array
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._g_l_y_f import GlyphComponent
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
try:
    from cu2qu import curve_to_quadratic
except ImportError:
    curve_to_quadratic = None
from fontTools.pens.basePen import decomposeSuperBezierSegment


__all__ = ["TTGlyphPen", "C2QGlyphPen"]


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


class C2QGlyphPen(TTGlyphPen):

    def __init__(self, glyphSet, maxError):
        if curve_to_quadratic is None:
            raise ImportError("No module named 'cu2qu'")
        super(C2QGlyphPen, self).__init__(glyphSet)
        self.maxError = maxError
        self.last = None

    def lineTo(self, pt):
        super(C2QGlyphPen, self).lineTo(pt)
        self.last = pt

    def moveTo(self, pt):
        super(C2QGlyphPen, self).moveTo(pt)
        self.last = pt

    def qCurveTo(self, *points):
        super(C2QGlyphPen, self).qCurveTo(*points)
        self.last = points[-1]

    def _curveToQuadratic(self, pt1, pt2, pt3):
        assert self.last is not None
        curve = (self.last, pt1, pt2, pt3)
        quadratic, err = curve_to_quadratic(curve, self.maxError)
        self.qCurveTo(*quadratic[1:])

    def curveTo(self, *points):
        # 'n' is the number of control points
        n = len(points) - 1
        assert n >= 0
        if n == 2:
            # this is the most common case, so we special-case it
            self._curveToQuadratic(*points)
        elif n > 2:
            for segment in decomposeSuperBezierSegment(points):
                self._curveToQuadratic(*segment)
        elif n == 1:
            self.qCurveTo(*points)
        elif n == 0:
            self.lineTo(points[0])

    def closePath(self):
        super(C2QGlyphPen, self).closePath()
        self.last = None
