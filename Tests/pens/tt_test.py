import enum
from string import ascii_letters, digits, printable
from typing import Any, Dict, Optional, Tuple

from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.ttGlyphPen import TTGlyphPen, TTGlyphPointPen
from fontTools.ttLib.tables._g_l_y_f import Glyph
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

st_glyph_name = st.text(ascii_letters + digits + "._")
st_coordinate = st.floats() | st.integers()
st_point = st.tuples(st_coordinate, st_coordinate)
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


class PenState(enum.Enum):
    IDLE = "idle"
    DRAWING = "drawing"


class PointSegmentPointTest(RuleBasedStateMachine):
    """Tests that TTGlyphPen and TTGlyphPointPen behave the same.

    NOTE: Segment pens drop point names, identifiers and kwargs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.state: PenState = PenState.IDLE
        self.fresh_path: bool = False
        self.offcurves: int = 0
        self.components: Dict[str, Glyph] = {}
        self.pen1inner = TTGlyphPen(self.components)
        self.pen1 = PointToSegmentPen(self.pen1inner)
        self.pen2 = TTGlyphPointPen(self.components)

    @precondition(lambda self: self.state is PenState.IDLE)
    @rule(identifier=st_identifier, kwargs=st_kwargs)
    def begin_path(self, identifier: Optional[str], kwargs: Dict[str, Any]) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.beginPath(identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.beginPath(identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.state = PenState.DRAWING
        self.fresh_path = True
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.DRAWING and self.offcurves == 0)
    @rule()
    def end_path(self) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.endPath()
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.endPath()
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.state = PenState.IDLE
        self.fresh_path = False
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.DRAWING)
    @rule(
        pt=st_point,
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point_off(
        self,
        pt: Tuple[float, float],
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.addPoint(pt, name=name, identifier=identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addPoint(pt, name=name, identifier=identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.fresh_path = False
        self.offcurves += 1

    @precondition(lambda self: self.state is PenState.DRAWING and self.fresh_path)
    @rule(
        pt=st_point,
        smooth=st.booleans(),
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point_move(
        self,
        pt: Tuple[float, float],
        smooth: bool,
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.addPoint(pt, "move", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addPoint(pt, "move", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.fresh_path = False
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.DRAWING and self.offcurves == 0)
    @rule(
        pt=st_point,
        smooth=st.booleans(),
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point_line(
        self,
        pt: Tuple[float, float],
        smooth: bool,
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.addPoint(pt, "line", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addPoint(pt, "line", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.fresh_path = False
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.DRAWING)
    @rule(
        pt=st_point,
        smooth=st.booleans(),
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point_qcurve(
        self,
        pt: Tuple[float, float],
        smooth: bool,
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.addPoint(pt, "qcurve", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addPoint(pt, "qcurve", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.fresh_path = False
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.DRAWING)
    @rule(
        pt=st_point,
        smooth=st.booleans(),
        name=st_point_name,
        identifier=st_identifier,
        kwargs=st_kwargs,
    )
    def add_point_curve(
        self,
        pt: Tuple[float, float],
        smooth: bool,
        name: Optional[str],
        identifier: Optional[str],
        kwargs: Dict[str, Any],
    ) -> None:
        e1 = None
        e2 = None
        try:
            self.pen1.addPoint(pt, "curve", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addPoint(pt, "curve", smooth, name, identifier, **kwargs)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2
        self.fresh_path = False
        self.offcurves = 0

    @precondition(lambda self: self.state is PenState.IDLE)
    @rule(baseGlyphName=st_glyph_name, transformation=st_transformation)
    def add_component(
        self,
        baseGlyphName: str,
        transformation: Tuple[float, float, float, float, float, float],
    ) -> None:
        e1 = None
        e2 = None
        self.components[baseGlyphName] = Glyph()
        try:
            self.pen1.addComponent(baseGlyphName, transformation)
        except (Exception, ArithmeticError) as e:
            e1 = e
        try:
            self.pen2.addComponent(baseGlyphName, transformation)
        except (Exception, ArithmeticError) as e:
            e2 = e
        if e1 is not None or e2 is not None:
            assert e1 == e2

    # Pens may flush contours to storage only after a path ended.
    @precondition(lambda self: self.state is PenState.IDLE)
    @invariant()
    def pens_agree(self):
        assert self.pen1inner.glyph() == self.pen2.glyph()


pentest = PointSegmentPointTest.TestCase
