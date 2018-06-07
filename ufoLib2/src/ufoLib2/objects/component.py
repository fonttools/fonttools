import attr
from typing import Optional
from ufoLib2.objects.misc import Transformation
from ufoLib2.pointPens.converterPens import PointToSegmentPen
import warnings


def _to_transformation(v):
    if not isinstance(v, Transformation):
        return Transformation(*v)
    return v


@attr.s(slots=True)
class Component(object):
    baseGlyph = attr.ib(type=str)
    _transformation = attr.ib(convert=_to_transformation, type=Transformation)
    identifier = attr.ib(default=None, type=Optional[str])

    @property
    def transformation(self):
        return self._transformation

    @transformation.setter
    def transformation(self, value):
        self._transformation = _to_transformation(value)

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        try:
            pointPen.addComponent(
                self.baseGlyph,
                self._transformation,
                identifier=self.identifier,
            )
        except TypeError:
            pointPen.addComponent(self.baseGlyph, self._transformation)
            warnings.warn(
                "The addComponent method needs an identifier kwarg. "
                "The component's identifier value has been discarded.",
                UserWarning,
            )
