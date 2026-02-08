"""Pen recording operations that can be accessed or replayed."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING
from collections.abc import Generator, Iterable, Sequence

from fontTools.pens.basePen import AbstractPen, DecomposingPen
from fontTools.pens.pointPen import AbstractPointPen, DecomposingPointPen

if TYPE_CHECKING:
    from fontTools.annotations import (
        DSLocation,
        Identifier,
        Point,
        PointName,
        SegmentType,
        TransformInput,
    )
    from fontTools.misc.transform import DecomposedTransform

RecordingOp = tuple[str, Sequence[Any]]
RecordingOps = Iterable[RecordingOp]
PenRecordingValue = list[tuple[str, tuple[Any, ...]]]
PointPenRecordingValue = list[tuple[str, tuple[Any, ...], dict[str, Any]]]

__all__ = [
    "replayRecording",
    "RecordingPen",
    "DecomposingRecordingPen",
    "DecomposingRecordingPointPen",
    "RecordingPointPen",
    "lerpRecordings",
]


def replayRecording(recording: RecordingOps, pen: Any) -> None:
    """Replay a recording, as produced by RecordingPen or DecomposingRecordingPen,
    to a pen.

    Note that recording does not have to be produced by those pens.
    It can be any iterable of tuples of method name and tuple-of-arguments.
    Likewise, pen can be any objects receiving those method calls.
    """
    for operator, operands in recording:
        getattr(pen, operator)(*operands)


class RecordingPen(AbstractPen):
    """Pen recording operations that can be accessed or replayed.

    The recording can be accessed as pen.value; or replayed using
    pen.replay(otherPen).

    :Example:
        .. code-block::

            from fontTools.ttLib import TTFont
            from fontTools.pens.recordingPen import RecordingPen

            glyph_name = 'dollar'
            font_path = 'MyFont.otf'

            font = TTFont(font_path)
            glyphset = font.getGlyphSet()
            glyph = glyphset[glyph_name]

            pen = RecordingPen()
            glyph.draw(pen)
            print(pen.value)
    """

    def __init__(self) -> None:
        self.value: PenRecordingValue = []

    def moveTo(self, p0: Point) -> None:
        self.value.append(("moveTo", (p0,)))

    def lineTo(self, p1: Point) -> None:
        self.value.append(("lineTo", (p1,)))

    def qCurveTo(self, *points: Point) -> None:  # type: ignore[override]
        self.value.append(("qCurveTo", points))

    def curveTo(self, *points: Point) -> None:
        self.value.append(("curveTo", points))

    def closePath(self) -> None:
        self.value.append(("closePath", ()))

    def endPath(self) -> None:
        self.value.append(("endPath", ()))

    def addComponent(self, glyphName: str, transformation: TransformInput) -> None:
        self.value.append(("addComponent", (glyphName, transformation)))

    def addVarComponent(
        self, glyphName: str, transformation: DecomposedTransform, location: DSLocation
    ) -> None:
        self.value.append(("addVarComponent", (glyphName, transformation, location)))

    def replay(self, pen: Any) -> None:
        replayRecording(self.value, pen)

    draw = replay


class DecomposingRecordingPen(DecomposingPen, RecordingPen):
    """Same as RecordingPen, except that it doesn't keep components
    as references, but draws them decomposed as regular contours.

    The constructor takes a required 'glyphSet' positional argument,
    a dictionary of glyph objects (i.e. with a 'draw' method) keyed
    by thir name; other arguments are forwarded to the DecomposingPen's
    constructor::

        >>> class SimpleGlyph(object):
        ...     def draw(self, pen):
        ...         pen.moveTo((0, 0))
        ...         pen.curveTo((1, 1), (2, 2), (3, 3))
        ...         pen.closePath()
        >>> class CompositeGlyph(object):
        ...     def draw(self, pen):
        ...         pen.addComponent('a', (1, 0, 0, 1, -1, 1))
        >>> class MissingComponent(object):
        ...     def draw(self, pen):
        ...         pen.addComponent('foobar', (1, 0, 0, 1, 0, 0))
        >>> class FlippedComponent(object):
        ...     def draw(self, pen):
        ...         pen.addComponent('a', (-1, 0, 0, 1, 0, 0))
        >>> glyphSet = {
        ...    'a': SimpleGlyph(),
        ...    'b': CompositeGlyph(),
        ...    'c': MissingComponent(),
        ...    'd': FlippedComponent(),
        ... }
        >>> for name, glyph in sorted(glyphSet.items()):
        ...     pen = DecomposingRecordingPen(glyphSet)
        ...     try:
        ...         glyph.draw(pen)
        ...     except pen.MissingComponentError:
        ...         pass
        ...     print("{}: {}".format(name, pen.value))
        a: [('moveTo', ((0, 0),)), ('curveTo', ((1, 1), (2, 2), (3, 3))), ('closePath', ())]
        b: [('moveTo', ((-1, 1),)), ('curveTo', ((0, 2), (1, 3), (2, 4))), ('closePath', ())]
        c: []
        d: [('moveTo', ((0, 0),)), ('curveTo', ((-1, 1), (-2, 2), (-3, 3))), ('closePath', ())]

        >>> for name, glyph in sorted(glyphSet.items()):
        ...     pen = DecomposingRecordingPen(
        ...         glyphSet, skipMissingComponents=True, reverseFlipped=True,
        ...     )
        ...     glyph.draw(pen)
        ...     print("{}: {}".format(name, pen.value))
        a: [('moveTo', ((0, 0),)), ('curveTo', ((1, 1), (2, 2), (3, 3))), ('closePath', ())]
        b: [('moveTo', ((-1, 1),)), ('curveTo', ((0, 2), (1, 3), (2, 4))), ('closePath', ())]
        c: []
        d: [('moveTo', ((0, 0),)), ('lineTo', ((-3, 3),)), ('curveTo', ((-2, 2), (-1, 1), (0, 0))), ('closePath', ())]
    """

    # raises MissingComponentError(KeyError) if base glyph is not found in glyphSet
    skipMissingComponents = False


class RecordingPointPen(AbstractPointPen):
    """PointPen recording operations that can be accessed or replayed.

    The recording can be accessed as pen.value; or replayed using
    pointPen.replay(otherPointPen).

    :Example:
        .. code-block::

            from defcon import Font
            from fontTools.pens.recordingPen import RecordingPointPen

            glyph_name = 'a'
            font_path = 'MyFont.ufo'

            font = Font(font_path)
            glyph = font[glyph_name]

            pen = RecordingPointPen()
            glyph.drawPoints(pen)
            print(pen.value)

            new_glyph = font.newGlyph('b')
            pen.replay(new_glyph.getPointPen())
    """

    def __init__(self) -> None:
        self.value: PointPenRecordingValue = []

    def beginPath(self, identifier: Identifier = None, **kwargs: Any) -> None:
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("beginPath", (), kwargs))

    def endPath(self) -> None:
        self.value.append(("endPath", (), {}))

    def addPoint(
        self,
        pt: Point,
        segmentType: SegmentType = None,
        smooth: bool = False,
        name: PointName = None,
        identifier: Identifier = None,
        **kwargs: Any,
    ) -> None:
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("addPoint", (pt, segmentType, smooth, name), kwargs))

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: TransformInput,
        identifier: Identifier = None,
        **kwargs: Any,
    ) -> None:
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(("addComponent", (baseGlyphName, transformation), kwargs))

    def addVarComponent(  # type: ignore[override]
        self,
        baseGlyphName: str,
        transformation: DecomposedTransform,
        location: DSLocation,
        identifier: Identifier = None,
        **kwargs: Any,
    ) -> None:
        if identifier is not None:
            kwargs["identifier"] = identifier
        self.value.append(
            ("addVarComponent", (baseGlyphName, transformation, location), kwargs)
        )

    def replay(self, pointPen: Any) -> None:
        for operator, args, kwargs in self.value:
            getattr(pointPen, operator)(*args, **kwargs)

    drawPoints = replay


class DecomposingRecordingPointPen(DecomposingPointPen, RecordingPointPen):
    """Same as RecordingPointPen, except that it doesn't keep components
    as references, but draws them decomposed as regular contours.

    The constructor takes a required 'glyphSet' positional argument,
    a dictionary of pointPen-drawable glyph objects (i.e. with a 'drawPoints' method)
    keyed by thir name; other arguments are forwarded to the DecomposingPointPen's
    constructor::

        >>> from pprint import pprint
        >>> class SimpleGlyph(object):
        ...     def drawPoints(self, pen):
        ...         pen.beginPath()
        ...         pen.addPoint((0, 0), "line")
        ...         pen.addPoint((1, 1))
        ...         pen.addPoint((2, 2))
        ...         pen.addPoint((3, 3), "curve")
        ...         pen.endPath()
        >>> class CompositeGlyph(object):
        ...     def drawPoints(self, pen):
        ...         pen.addComponent('a', (1, 0, 0, 1, -1, 1))
        >>> class MissingComponent(object):
        ...     def drawPoints(self, pen):
        ...         pen.addComponent('foobar', (1, 0, 0, 1, 0, 0))
        >>> class FlippedComponent(object):
        ...     def drawPoints(self, pen):
        ...         pen.addComponent('a', (-1, 0, 0, 1, 0, 0))
        >>> glyphSet = {
        ...    'a': SimpleGlyph(),
        ...    'b': CompositeGlyph(),
        ...    'c': MissingComponent(),
        ...    'd': FlippedComponent(),
        ... }
        >>> for name, glyph in sorted(glyphSet.items()):
        ...     pen = DecomposingRecordingPointPen(glyphSet)
        ...     try:
        ...         glyph.drawPoints(pen)
        ...     except pen.MissingComponentError:
        ...         pass
        ...     pprint({name: pen.value})
        {'a': [('beginPath', (), {}),
               ('addPoint', ((0, 0), 'line', False, None), {}),
               ('addPoint', ((1, 1), None, False, None), {}),
               ('addPoint', ((2, 2), None, False, None), {}),
               ('addPoint', ((3, 3), 'curve', False, None), {}),
               ('endPath', (), {})]}
        {'b': [('beginPath', (), {}),
               ('addPoint', ((-1, 1), 'line', False, None), {}),
               ('addPoint', ((0, 2), None, False, None), {}),
               ('addPoint', ((1, 3), None, False, None), {}),
               ('addPoint', ((2, 4), 'curve', False, None), {}),
               ('endPath', (), {})]}
        {'c': []}
        {'d': [('beginPath', (), {}),
               ('addPoint', ((0, 0), 'line', False, None), {}),
               ('addPoint', ((-1, 1), None, False, None), {}),
               ('addPoint', ((-2, 2), None, False, None), {}),
               ('addPoint', ((-3, 3), 'curve', False, None), {}),
               ('endPath', (), {})]}

        >>> for name, glyph in sorted(glyphSet.items()):
        ...     pen = DecomposingRecordingPointPen(
        ...         glyphSet, skipMissingComponents=True, reverseFlipped=True,
        ...     )
        ...     glyph.drawPoints(pen)
        ...     pprint({name: pen.value})
        {'a': [('beginPath', (), {}),
               ('addPoint', ((0, 0), 'line', False, None), {}),
               ('addPoint', ((1, 1), None, False, None), {}),
               ('addPoint', ((2, 2), None, False, None), {}),
               ('addPoint', ((3, 3), 'curve', False, None), {}),
               ('endPath', (), {})]}
        {'b': [('beginPath', (), {}),
               ('addPoint', ((-1, 1), 'line', False, None), {}),
               ('addPoint', ((0, 2), None, False, None), {}),
               ('addPoint', ((1, 3), None, False, None), {}),
               ('addPoint', ((2, 4), 'curve', False, None), {}),
               ('endPath', (), {})]}
        {'c': []}
        {'d': [('beginPath', (), {}),
               ('addPoint', ((0, 0), 'curve', False, None), {}),
               ('addPoint', ((-3, 3), 'line', False, None), {}),
               ('addPoint', ((-2, 2), None, False, None), {}),
               ('addPoint', ((-1, 1), None, False, None), {}),
               ('endPath', (), {})]}
    """

    # raises MissingComponentError(KeyError) if base glyph is not found in glyphSet
    skipMissingComponents = False


def lerpRecordings(
    recording1: PenRecordingValue, recording2: PenRecordingValue, factor: float = 0.5
) -> Generator[RecordingOp]:
    """Linearly interpolate between two recordings. The recordings
    must be decomposed, i.e. they must not contain any components.

    Factor is typically between 0 and 1. 0 means the first recording,
    1 means the second recording, and 0.5 means the average of the
    two recordings. Other values are possible, and can be useful to
    extrapolate. Defaults to 0.5.

    Returns a generator with the new recording.
    """
    if len(recording1) != len(recording2):
        raise ValueError(
            "Mismatched lengths: %d and %d" % (len(recording1), len(recording2))
        )
    for (op1, args1), (op2, args2) in zip(recording1, recording2):
        if op1 != op2:
            raise ValueError("Mismatched operations: %s, %s" % (op1, op2))
        if op1 == "addComponent":
            raise ValueError("Cannot interpolate components")
        else:
            mid_args = [
                (x1 + (x2 - x1) * factor, y1 + (y2 - y1) * factor)
                for (x1, y1), (x2, y2) in zip(args1, args2)
            ]
        yield (op1, mid_args)


if __name__ == "__main__":
    pen = RecordingPen()
    pen.moveTo((0, 0))
    pen.lineTo((0, 100))
    pen.curveTo((50, 75), (60, 50), (50, 25))
    pen.closePath()
    from pprint import pprint

    pprint(pen.value)
