from string import ascii_letters, digits, printable
from typing import Any, Dict, Optional, Tuple

from fontTools.pens.basePen import PenError
from fontTools.pens.pointPen import (
    PointToSegmentPen,
    SegmentToPointPen,
    ReverseContourPointPen,
    GuessSmoothPointPen,
)
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

# XXX: generate glyph (Tests/pens/recordingPen_test.py -> _TestGlyph) instead
#      of command stream and draw that into recordingpens?

st_glyph_name = st.text(ascii_letters + digits + "._")
st_coordinate = st.floats() | st.integers()
st_point = st.tuples(st_coordinate, st_coordinate)
st_segment_type = st.none() | st.sampled_from(["move", "line", "curve", "qcurve"])
st_identifier = st.none() | st.text(printable)
st_point_name = st.none() | st.text(printable)
st_transformation = st.tuples(
    st_coordinate,
    st_coordinate,
    st_coordinate,
    st_coordinate,
    st_coordinate,
    st_coordinate,
)
st_kwargs = st.dictionaries(
    st.text(printable).filter(
        lambda x: x
        not in {
            "pt",
            "segmentType",
            "smooth",
            "name",
            "identifier",
            "kwargs",
            "baseGlyphName",
            "transformation",
        }
    ),
    st.none() | st.booleans() | st.integers() | st.text(printable),
)


class PointMonkey(RuleBasedStateMachine):
    """Give point pens a good shake to find unexpected crashes, swallowing expected errors."""

    def __init__(self):
        super().__init__()
        self.pen = RecordingPointPen()

    @rule(identifier=st_identifier, kwargs=st_kwargs)
    def begin_path(self, identifier: Optional[str], kwargs: Dict[str, Any]) -> None:
        try:
            self.pen.beginPath(identifier, **kwargs)
        except PenError:
            pass

    @rule()
    def end_path(self) -> None:
        try:
            self.pen.endPath()
        except PenError:
            pass

    @rule(
        pt=st_point,
        segmentType=st_segment_type,
        smooth=st.booleans(),
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point(
        self,
        pt: Tuple[float, float],
        segmentType: Optional[str],
        smooth: bool,
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        try:
            self.pen.addPoint(pt, segmentType, smooth, name, identifier, **kwargs)
        except PenError:
            pass

    @rule(
        baseGlyphName=st_glyph_name,
        transformation=st_transformation,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_component(
        self,
        baseGlyphName: str,
        transformation: Tuple[float, float, float, float, float, float],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        try:
            self.pen.addComponent(baseGlyphName, transformation, identifier, **kwargs)
        except PenError:
            pass


class PointSegmentPointMonkey(PointMonkey):
    # NOTE: Segment pens drop point names,identifiers and kwargs.

    def __init__(self):
        super().__init__()
        self.pen = PointToSegmentPen(SegmentToPointPen(RecordingPointPen()))


class ReverseContourMonkey(PointMonkey):
    def __init__(self):
        super().__init__()
        self.pen = ReverseContourPointPen(ReverseContourPointPen(RecordingPointPen()))


class GuessSmoothPointMonkey(PointMonkey):
    def __init__(self):
        super().__init__()
        self.pen = GuessSmoothPointPen(RecordingPointPen())


p2s2ptest = PointSegmentPointMonkey.TestCase
rctest = ReverseContourMonkey.TestCase
gsptest = GuessSmoothPointMonkey.TestCase


class SegmentMonkey(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.pen = RecordingPen()

    @rule(pt=st_point)
    def moveTo(self, pt: Tuple[float, float]) -> None:
        try:
            self.pen.moveTo(pt)
        except PenError:
            pass

    @rule(pt=st_point)
    def lineTo(self, pt: Tuple[float, float]) -> None:
        try:
            self.pen.lineTo(pt)
        except PenError:
            pass

    @rule(points=st.lists(st_point))
    def curveTo(self, points: Tuple[float, float]) -> None:
        try:
            self.pen.curveTo(*points)
        except PenError:
            pass

    @rule(points=st.lists(st_point))
    def qCurveTo(self, points: Tuple[float, float]) -> None:
        try:
            self.pen.qCurveTo(*points)
        except PenError:
            pass

    @rule()
    def closePath(self) -> None:
        try:
            self.pen.closePath()
        except PenError:
            pass

    @rule()
    def endPath(self) -> None:
        try:
            self.pen.endPath()
        except PenError:
            pass

    @rule(glyphName=st_glyph_name, transformation=st_transformation)
    def addComponent(
        self,
        glyphName: str,
        transformation: Tuple[float, float, float, float, float, float],
    ) -> None:
        try:
            self.pen.addComponent(glyphName, transformation)
        except PenError:
            pass


class SegmentPointSegmentMonkey(SegmentMonkey):
    def __init__(self):
        super().__init__()
        self.pen = SegmentToPointPen(PointToSegmentPen(RecordingPen()))


class SegmentPointSegmentNoSmoothGuessMonkey(SegmentMonkey):
    def __init__(self):
        super().__init__()
        self.pen = SegmentToPointPen(
            PointToSegmentPen(RecordingPen()), guessSmooth=False
        )


s2p2stest = SegmentPointSegmentMonkey.TestCase
s2p2snsgtest = SegmentPointSegmentNoSmoothGuessMonkey.TestCase
