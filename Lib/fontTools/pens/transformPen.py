from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast, TYPE_CHECKING

from fontTools.pens.filterPen import FilterPen, FilterPointPen
from fontTools.misc.transform import Transform

if TYPE_CHECKING:
    from fontTools.annotations import Point, TransformInput
    from fontTools.pens.basePen import AbstractPen
    from fontTools.pens.pointPen import AbstractPointPen

__all__ = ["TransformPen", "TransformPointPen"]


class TransformPen(FilterPen):
    """Pen that transforms all coordinates using a Affine transformation,
    and passes them to another pen.
    """

    def __init__(self, outPen: AbstractPen, transformation: TransformInput) -> None:
        """The 'outPen' argument is another pen object. It will receive the
        transformed coordinates. The 'transformation' argument can either
        be a six-tuple, or a fontTools.misc.transform.Transform object.
        """
        super(TransformPen, self).__init__(outPen)
        if not hasattr(transformation, "transformPoint"):
            transformation = Transform(*transformation)
        else:
            transformation = cast(Transform, transformation)
        self._transformation = transformation
        self._transformPoint = transformation.transformPoint
        self._stack: list[Any] = []

    def moveTo(self, pt: Point) -> None:
        self._outPen.moveTo(self._transformPoint(pt))

    def lineTo(self, pt: Point) -> None:
        self._outPen.lineTo(self._transformPoint(pt))

    def curveTo(self, *points: Point) -> None:
        self._outPen.curveTo(*self._transformPoints(points))

    def qCurveTo(self, *points: Point | None) -> None:
        pointSeq: Sequence[Point | None]
        if points[-1] is None:
            transformed = self._transformPoints(cast(Sequence["Point"], points[:-1]))
            pointSeq = transformed + [None]
        else:
            pointSeq = self._transformPoints(cast(Sequence["Point"], points))
        self._outPen.qCurveTo(*pointSeq)

    def _transformPoints(self, points: Sequence[Point]) -> list[Point]:
        transformPoint = self._transformPoint
        return [transformPoint(pt) for pt in points]

    def closePath(self) -> None:
        self._outPen.closePath()

    def endPath(self) -> None:
        self._outPen.endPath()

    def addComponent(self, glyphName: str, transformation: TransformInput) -> None:  # type: ignore[override]
        transformation = self._transformation.transform(transformation)
        self._outPen.addComponent(glyphName, transformation)


class TransformPointPen(FilterPointPen):
    """PointPen that transforms all coordinates using a Affine transformation,
    and passes them to another PointPen.

    For example::

        >>> from fontTools.pens.recordingPen import RecordingPointPen
        >>> rec = RecordingPointPen()
        >>> pen = TransformPointPen(rec, (2, 0, 0, 2, -10, 5))
        >>> v = iter(rec.value)
        >>> pen.beginPath(identifier="contour-0")
        >>> next(v)
        ('beginPath', (), {'identifier': 'contour-0'})

        >>> pen.addPoint((100, 100), "line")
        >>> next(v)
        ('addPoint', ((190, 205), 'line', False, None), {})

        >>> pen.endPath()
        >>> next(v)
        ('endPath', (), {})

        >>> pen.addComponent("a", (1, 0, 0, 1, -10, 5), identifier="component-0")
        >>> next(v)
        ('addComponent', ('a', <Transform [2 0 0 2 -30 15]>), {'identifier': 'component-0'})
    """

    def __init__(
        self, outPointPen: AbstractPointPen, transformation: TransformInput
    ) -> None:
        """The 'outPointPen' argument is another point pen object.
        It will receive the transformed coordinates.
        The 'transformation' argument can either be a six-tuple, or a
        fontTools.misc.transform.Transform object.
        """
        super().__init__(outPointPen)
        if not hasattr(transformation, "transformPoint"):
            transformation = Transform(*transformation)
        else:
            transformation = cast(Transform, transformation)
        self._transformation = transformation
        self._transformPoint = transformation.transformPoint

    def addPoint(  # type: ignore[override]
        self,
        pt: Point,
        segmentType: str | None = None,
        smooth: bool = False,
        name: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._outPen.addPoint(
            self._transformPoint(pt), segmentType, smooth, name, **kwargs
        )

    def addComponent(  # type: ignore[override]
        self,
        baseGlyphName: str,
        transformation: TransformInput,
        **kwargs: Any,
    ) -> None:
        transformation = self._transformation.transform(transformation)
        self._outPen.addComponent(baseGlyphName, transformation, **kwargs)


if __name__ == "__main__":
    from fontTools.pens.basePen import _TestPen

    pen = TransformPen(_TestPen(None), (2, 0, 0.5, 2, -10, 0))
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25), (0, 0))
    pen.closePath()
