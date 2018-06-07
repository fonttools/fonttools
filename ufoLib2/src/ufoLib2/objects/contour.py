import attr
from typing import Optional
from ufoLib2.pointPens.converterPens import PointToSegmentPen
import warnings


@attr.s(slots=True)
class Contour(object):
    _points = attr.ib(default=attr.Factory(list), type=list)
    identifier = attr.ib(default=None, repr=False, type=Optional[str])

    # TODO: use collections.abc?

    def __delitem__(self, index):
        del self._points[index]

    def __getitem__(self, index):
        return self._points[index]

    def __setitem__(self, index, point):
        self._points[index] = point

    def __iter__(self):
        return iter(self._points)

    def __len__(self):
        return len(self._points)

    def append(self, point):
        self._points.append(point)

    def clear(self):
        self._points.clear()

    def index(self, point):
        return self._points.index(point)

    def insert(self, index, point):
        self._points.insert(index, point)

    def remove(self, point):
        self._points.remove(point)

    def reverse(self):
        self._points.reverse()

    # TODO: rotate method?

    @property
    def open(self):
        if not self._points:
            return True
        return self._points[0].type == "move"

    # -----------
    # Pen methods
    # -----------

    def draw(self, pen):
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        try:
            pointPen.beginPath(identifier=self.identifier)
            for p in self._points:
                pointPen.addPoint(
                    (p.x, p.y),
                    segmentType=p.type,
                    smooth=p.smooth,
                    name=p.name,
                    identifier=p.identifier,
                )
        except TypeError:
            pointPen.beginPath()
            for p in self._points:
                pointPen.addPoint(
                    (p.x, p.y),
                    segmentType=p.type,
                    smooth=p.smooth,
                    name=p.name,
                )
            warnings.warn(
                "The pointPen needs an identifier kwarg. "
                "Identifiers have been discarded.",
                UserWarning,
            )
        pointPen.endPath()
