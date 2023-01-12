from __future__ import annotations

from typing import Any, Iterator, List, Tuple
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.pointPen import AbstractPointPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.typings import Point, PointType, Transformation


# XXX: used for pens and point pens???
class _PassThruComponentsMixin(object):
    def addComponent(
        self,
        glyphName: str,
        transformation: Transformation,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        if identifier is not None:
            kwargs["identifier"] = identifier
        self._outPen.addComponent(glyphName, transformation, **kwargs)  # type: ignore


class FilterPen(_PassThruComponentsMixin, AbstractPen):

    """Base class for pens that apply some transformation to the coordinates
    they receive and pass them to another pen.

    You can override any of its methods. The default implementation does
    nothing, but passes the commands unmodified to the other pen.

    >>> from fontTools.pens.recordingPen import RecordingPen
    >>> rec = RecordingPen()
    >>> pen = FilterPen(rec)
    >>> v = iter(rec.value)

    >>> pen.moveTo((0, 0))
    >>> next(v)
    ('moveTo', ((0, 0),))

    >>> pen.lineTo((1, 1))
    >>> next(v)
    ('lineTo', ((1, 1),))

    >>> pen.curveTo((2, 2), (3, 3), (4, 4))
    >>> next(v)
    ('curveTo', ((2, 2), (3, 3), (4, 4)))

    >>> pen.qCurveTo((5, 5), (6, 6), (7, 7), (8, 8))
    >>> next(v)
    ('qCurveTo', ((5, 5), (6, 6), (7, 7), (8, 8)))

    >>> pen.closePath()
    >>> next(v)
    ('closePath', ())

    >>> pen.moveTo((9, 9))
    >>> next(v)
    ('moveTo', ((9, 9),))

    >>> pen.endPath()
    >>> next(v)
    ('endPath', ())

    >>> pen.addComponent('foo', (1, 0, 0, 1, 0, 0))
    >>> next(v)
    ('addComponent', ('foo', (1, 0, 0, 1, 0, 0)))
    """

    def __init__(self, outPen: AbstractPen) -> None:
        self._outPen = outPen

    def moveTo(self, pt: Point) -> None:
        self._outPen.moveTo(pt)

    def lineTo(self, pt: Point) -> None:
        self._outPen.lineTo(pt)

    def curveTo(self, *points: Point) -> None:
        self._outPen.curveTo(*points)

    def qCurveTo(self, *points: Point | None) -> None:
        self._outPen.qCurveTo(*points)

    def closePath(self) -> None:
        self._outPen.closePath()

    def endPath(self) -> None:
        self._outPen.endPath()


ContourDescription = Tuple[str, Tuple[Any, ...]]
Contour = List[ContourDescription]


class ContourFilterPen(_PassThruComponentsMixin, RecordingPen):
    """A "buffered" filter pen that accumulates contour data, passes
    it through a ``filterContour`` method when the contour is closed or ended,
    and finally draws the result with the output pen.

    Components are passed through unchanged.
    """

    def __init__(self, outPen: AbstractPen) -> None:
        super(ContourFilterPen, self).__init__()
        self._outPen = outPen

    def closePath(self) -> None:
        super(ContourFilterPen, self).closePath()
        self._flushContour()

    def endPath(self) -> None:
        super(ContourFilterPen, self).endPath()
        self._flushContour()

    def _flushContour(self) -> None:
        result = self.filterContour(self.value)
        if result is not None:
            self.value = result  # type: ignore
        self.replay(self._outPen)
        self.value = []

    def filterContour(self, contour: Contour) -> Iterator[ContourDescription] | None:
        """Subclasses must override this to perform the filtering.

        The contour is a list of pen (operator, operands) tuples.
        Operators are strings corresponding to the AbstractPen methods:
        "moveTo", "lineTo", "curveTo", "qCurveTo", "closePath" and
        "endPath". The operands are the positional arguments that are
        passed to each method.

        If the method doesn't return a value (i.e. returns None), it's
        assumed that the argument was modified in-place.
        Otherwise, the return value is drawn with the output pen.
        """
        return None  # or return contour


class FilterPointPen(_PassThruComponentsMixin, AbstractPointPen):  # type: ignore
    """Baseclass for point pens that apply some transformation to the
    coordinates they receive and pass them to another point pen.

    You can override any of its methods. The default implementation does
    nothing, but passes the commands unmodified to the other pen.

    >>> from fontTools.pens.recordingPen import RecordingPointPen
    >>> rec = RecordingPointPen()
    >>> pen = FilterPointPen(rec)
    >>> v = iter(rec.value)
    >>> pen.beginPath(identifier="abc")
    >>> next(v)
    ('beginPath', (), {'identifier': 'abc'})
    >>> pen.addPoint((1, 2), "line", False)
    >>> next(v)
    ('addPoint', ((1, 2), 'line', False, None), {})
    >>> pen.addComponent("a", (2, 0, 0, 2, 10, -10), identifier="0001")
    >>> next(v)
    ('addComponent', ('a', (2, 0, 0, 2, 10, -10)), {'identifier': '0001'})
    >>> pen.endPath()
    >>> next(v)
    ('endPath', (), {})
    """

    def __init__(self, outPointPen: AbstractPointPen) -> None:
        self._outPen = outPointPen

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        self._outPen.beginPath(identifier, **kwargs)

    def endPath(self) -> None:
        self._outPen.endPath()

    def addPoint(
        self,
        pt: Point,
        segmentType: PointType = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._outPen.addPoint(pt, segmentType, smooth, name, identifier, **kwargs)
