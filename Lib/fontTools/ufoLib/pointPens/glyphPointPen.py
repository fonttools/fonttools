from ufoLib2.objects.component import Component
from ufoLib2.objects.contour import Contour
from ufoLib2.objects.point import Point
from ufoLib2.pointPens.basePen import AbstractPointPen


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
