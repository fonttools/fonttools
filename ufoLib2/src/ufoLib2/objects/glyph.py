import attr
from typing import Optional, Union
from ufoLib2.objects.anchor import Anchor
from ufoLib2.objects.component import Component
from ufoLib2.objects.contour import Contour
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.image import Image
from ufoLib2.objects.misc import Transformation
from ufoLib2.objects.point import Point
from ufoLib2.pointPens.converterPens import (
    PointToSegmentPen,
    SegmentToPointPen,
)
from ufoLib2.pointPens.glyphPointPen import GlyphPointPen


@attr.s(slots=True)
class Glyph(object):
    _name = attr.ib(type=str)
    width = attr.ib(default=0, init=False, type=Union[int, float])
    height = attr.ib(default=0, init=False, type=Union[int, float])
    unicodes = attr.ib(default=attr.Factory(list), init=False, type=list)

    image = attr.ib(
        default=attr.Factory(Image), init=False, repr=False, type=Image
    )
    lib = attr.ib(
        default=attr.Factory(dict), init=False, repr=False, type=dict
    )
    note = attr.ib(default=None, init=False, repr=False, type=Optional[str])

    _anchors = attr.ib(
        default=attr.Factory(list), init=False, repr=False, type=list
    )
    components = attr.ib(
        default=attr.Factory(list), init=False, repr=False, type=list
    )
    contours = attr.ib(
        default=attr.Factory(list), init=False, repr=False, type=list
    )
    _guidelines = attr.ib(
        default=attr.Factory(list), init=False, repr=False, type=list
    )

    def __len__(self):
        return len(self.contours)

    def __getitem__(self, index):
        return self.contours[index]

    def __contains__(self, contour):
        return contour in self.contours

    def __iter__(self):
        return iter(self.contours)

    @property
    def anchors(self):
        return self._anchors

    @anchors.setter
    def anchors(self, value):
        self.clearAnchors()
        for anchor in value:
            self.appendAnchor(anchor)

    @property
    def guidelines(self):
        return self._guidelines

    @guidelines.setter
    def guidelines(self, value):
        self.clearGuidelines()
        for guideline in value:
            self.appendGuideline(guideline)

    @property
    def name(self):
        return self._name

    @property
    def unicode(self):
        if self.unicodes:
            return self.unicodes[0]
        return None

    @unicode.setter
    def unicode(self, value):
        if value is None:
            self.unicodes = []
        else:
            if self.unicodes:
                if self.unicodes[0] == value:
                    return
                try:
                    self.unicodes.remove(value)
                except ValueError:
                    pass
                self.unicodes.insert(0, value)
            else:
                self.unicodes.append(value)

    def clear(self):
        del self._anchors[:]
        del self.components[:]
        del self.contours[:]
        del self._guidelines[:]
        self.image.clear()

    def clearAnchors(self):
        del self._anchors[:]

    def clearContours(self):
        del self.contours[:]

    def clearComponents(self):
        del self.components[:]

    def clearGuidelines(self):
        del self._guidelines[:]

    def removeComponent(self, component):
        self.components.remove(component)

    def appendAnchor(self, anchor):
        if not isinstance(anchor, Anchor):
            anchor = Anchor(**anchor)
        self.anchors.append(anchor)

    def appendGuideline(self, guideline):
        if not isinstance(guideline, Guideline):
            guideline = Guideline(**guideline)
        self._guidelines.append(guideline)

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        for contour in self.contours:
            contour.drawPoints(pointPen)
        for component in self.components:
            component.drawPoints(pointPen)

    def getPen(self):
        pen = SegmentToPointPen(self.getPointPen())
        return pen

    def getPointPen(self):
        pointPen = GlyphPointPen(self)
        return pointPen

    # lib wrapped attributes

    @property
    def markColor(self):
        return self.lib.get("public.markColor")

    @markColor.setter
    def markColor(self, value):
        if value is not None:
            self.lib["public.markColor"] = value
        elif "public.markColor" in self.lib:
            del self.lib["public.markColor"]

    @property
    def verticalOrigin(self):
        return self.lib.get("public.verticalOrigin")

    @verticalOrigin.setter
    def verticalOrigin(self, value):
        if value is not None:
            self.lib["public.verticalOrigin"] = value
        elif "public.verticalOrigin" in self.lib:
            del self.lib["public.verticalOrigin"]


class GlyphClasses(object):
    Anchor = Anchor
    Component = Component
    Contour = Contour
    Glyph = Glyph
    Guideline = Guideline
    Image = Image
    Point = Point

    Transformation = Transformation
