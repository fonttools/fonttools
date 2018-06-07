from fontTools.ufoLib.objects.component import Component
from fontTools.ufoLib.objects.contour import Contour
from fontTools.ufoLib.objects.point import Point
from fontTools.ufoLib.pointPens.basePen import AbstractPointPen


class GlyphPointPen(AbstractPointPen):
    __slots__ = "_glyph", "_contour"

    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None

    def beginPath(self, identifier=None, **kwargs):
        self._contour = Contour(identifier=identifier)

    def endPath(self):
        self._glyph.contours.append(self._contour)
        self._contour = None

    def addPoint(
        self,
        pt,
        segmentType=None,
        smooth=False,
        name=None,
        identifier=None,
        **kwargs
    ):
        x, y = pt
        self._contour.append(
            Point(
                x,
                y,
                type=segmentType,
                smooth=smooth,
                name=name,
                identifier=identifier,
            )
        )

    def addComponent(self, baseGlyph, transformation, **kwargs):
        component = Component(baseGlyph, transformation, **kwargs)
        self._glyph.components.append(component)
