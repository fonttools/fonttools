from __future__ import annotations

from typing import Any, Callable

from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Transform
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.filterPen import FilterPen, FilterPointPen
from fontTools.pens.pointPen import AbstractPointPen
from fontTools.pens.typings import Point, PointType, Transformation


__all__ = ["RoundingPen", "RoundingPointPen"]


class RoundingPen(FilterPen):
    """
    Filter pen that rounds point coordinates and component XY offsets to integer.

    >>> from fontTools.pens.recordingPen import RecordingPen
    >>> recpen = RecordingPen()
    >>> roundpen = RoundingPen(recpen)
    >>> roundpen.moveTo((0.4, 0.6))
    >>> roundpen.lineTo((1.6, 2.5))
    >>> roundpen.qCurveTo((2.4, 4.6), (3.3, 5.7), (4.9, 6.1))
    >>> roundpen.curveTo((6.4, 8.6), (7.3, 9.7), (8.9, 10.1))
    >>> roundpen.addComponent("a", (1.5, 0, 0, 1.5, 10.5, -10.5))
    >>> recpen.value == [
    ...     ('moveTo', ((0, 1),)),
    ...     ('lineTo', ((2, 3),)),
    ...     ('qCurveTo', ((2, 5), (3, 6), (5, 6))),
    ...     ('curveTo', ((6, 9), (7, 10), (9, 10))),
    ...     ('addComponent', ('a', (1.5, 0, 0, 1.5, 11, -10))),
    ... ]
    True
    """

    def __init__(
        self, outPen: AbstractPen, roundFunc: Callable[[float], int] = otRound
    ) -> None:
        super().__init__(outPen)
        self.roundFunc = roundFunc

    def moveTo(self, pt: Point) -> None:
        self._outPen.moveTo((self.roundFunc(pt[0]), self.roundFunc(pt[1])))

    def lineTo(self, pt: Point) -> None:
        self._outPen.lineTo((self.roundFunc(pt[0]), self.roundFunc(pt[1])))

    def curveTo(self, *points: Point) -> None:
        self._outPen.curveTo(
            *((self.roundFunc(x), self.roundFunc(y)) for x, y in points)
        )

    def qCurveTo(self, *points: Point | None) -> None:
        # XXX: This will fail when `points` actually contains a None.
        self._outPen.qCurveTo(
            *((self.roundFunc(x), self.roundFunc(y)) for x, y in points)  # type: ignore
        )

    def addComponent(  # type: ignore
        self,
        glyphName: str,
        transformation: Transformation,
    ) -> None:
        self._outPen.addComponent(
            glyphName,
            Transform(
                *transformation[:4],
                self.roundFunc(transformation[4]),
                self.roundFunc(transformation[5]),
            ),
        )


class RoundingPointPen(FilterPointPen):
    """
    Filter point pen that rounds point coordinates and component XY offsets to integer.

    >>> from fontTools.pens.recordingPen import RecordingPointPen
    >>> recpen = RecordingPointPen()
    >>> roundpen = RoundingPointPen(recpen)
    >>> roundpen.beginPath()
    >>> roundpen.addPoint((0.4, 0.6), 'line')
    >>> roundpen.addPoint((1.6, 2.5), 'line')
    >>> roundpen.addPoint((2.4, 4.6))
    >>> roundpen.addPoint((3.3, 5.7))
    >>> roundpen.addPoint((4.9, 6.1), 'qcurve')
    >>> roundpen.endPath()
    >>> roundpen.addComponent("a", (1.5, 0, 0, 1.5, 10.5, -10.5))
    >>> recpen.value == [
    ...     ('beginPath', (), {}),
    ...     ('addPoint', ((0, 1), 'line', False, None), {}),
    ...     ('addPoint', ((2, 3), 'line', False, None), {}),
    ...     ('addPoint', ((2, 5), None, False, None), {}),
    ...     ('addPoint', ((3, 6), None, False, None), {}),
    ...     ('addPoint', ((5, 6), 'qcurve', False, None), {}),
    ...     ('endPath', (), {}),
    ...     ('addComponent', ('a', (1.5, 0, 0, 1.5, 11, -10)), {}),
    ... ]
    True
    """

    def __init__(
        self, outPen: AbstractPointPen, roundFunc: Callable[[float], int] = otRound
    ) -> None:
        super().__init__(outPen)
        self.roundFunc = roundFunc

    def addPoint(
        self,
        pt: Point,
        segmentType: PointType = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._outPen.addPoint(
            (self.roundFunc(pt[0]), self.roundFunc(pt[1])),
            segmentType=segmentType,
            smooth=smooth,
            name=name,
            identifier=identifier,
            **kwargs,
        )

    def addComponent(  # type: ignore
        self,
        baseGlyphName: str,
        transformation: Transformation,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        self._outPen.addComponent(
            baseGlyphName,
            Transform(
                *transformation[:4],
                self.roundFunc(transformation[4]),
                self.roundFunc(transformation[5]),
            ),
            identifier,
            **kwargs,
        )
