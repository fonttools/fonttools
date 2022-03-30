# import enum
# from string import ascii_letters, digits, printable
# from typing import Any, Dict, Optional, Tuple

# import ufoLib2.objects
# from fontTools.pens.pointPen import ReverseContourPointPen
# from hypothesis import strategies as st
# from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

# # XXX: generate glyph (Tests/pens/recordingPen_test.py -> _TestGlyph) instead
# #      of command stream and draw that into recordingpens? TestGlyph (has contours,
# #      components and contour vars) plus TestPointPen
# # - segment @composite of (zero or more offcurves, type point) so we can keep having one add_point method?

# st_glyph_name = st.text(ascii_letters + digits + "._")
# st_coordinate = st.floats() | st.integers()
# st_point = st.tuples(st_coordinate, st_coordinate)
# st_identifier = st.none() | st.text(printable)
# st_point_name = st.none() | st.text(printable)
# st_transformation = st.tuples(
#     st_coordinate,
#     st_coordinate,
#     st_coordinate,
#     st_coordinate,
#     st_coordinate,
#     st_coordinate,
# )
# st_kwargs = st.dictionaries(
#     st.text(printable).filter(
#         lambda x: x
#         not in {
#             "pt",
#             "segmentType",
#             "smooth",
#             "name",
#             "identifier",
#             "kwargs",
#             "baseGlyphName",
#             "transformation",
#         }
#     ),
#     st.none() | st.booleans() | st.integers() | st.text(printable),
# )


# class PenState(enum.Enum):
#     IDLE = "idle"
#     DRAWING = "drawing"


# class PointSegmentPointTest(RuleBasedStateMachine):
#     """Tests roundtripping points to segments and back.

#     NOTE: Segment pens drop point names, identifiers and kwargs.
#     """

#     def __init__(self) -> None:
#         super().__init__()
#         self.state: PenState = PenState.IDLE
#         self.fresh_path: bool = False
#         self.offcurves: int = 0
#         self.glyph1 = ufoLib2.objects.Glyph()
#         self.pen1 = self.glyph1.getPointPen()
#         self.glyph2 = ufoLib2.objects.Glyph()
#         self.pen2 = ReverseContourPointPen(
#             ReverseContourPointPen(self.glyph2.getPointPen())
#         )

#     @precondition(lambda self: self.state is PenState.IDLE)
#     @rule(identifier=st_identifier, kwargs=st_kwargs)
#     def begin_path(self, identifier: Optional[str], kwargs: Dict[str, Any]) -> None:
#         self.pen1.beginPath(identifier, **kwargs)
#         self.pen2.beginPath(identifier, **kwargs)
#         self.state = PenState.DRAWING
#         self.fresh_path = True
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.DRAWING and self.offcurves == 0)
#     @rule()
#     def end_path(self) -> None:
#         self.pen1.endPath()
#         self.pen2.endPath()
#         self.state = PenState.IDLE
#         self.fresh_path = False
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.DRAWING)
#     @rule(
#         pt=st_point,
#         name=st_point_name,
#         identifier=st_identifier,
#         kwargs=st_kwargs,
#     )
#     def add_point_off(
#         self,
#         pt: Tuple[float, float],
#         name: Optional[str],
#         identifier: Optional[str],
#         kwargs: Dict[str, Any],
#     ) -> None:
#         self.pen1.addPoint(pt, name=name, identifier=identifier, **kwargs)
#         self.pen2.addPoint(pt, name=name, identifier=identifier, **kwargs)
#         self.fresh_path = False
#         self.offcurves += 1

#     @precondition(lambda self: self.state is PenState.DRAWING and self.fresh_path)
#     @rule(
#         pt=st_point,
#         smooth=st.booleans(),
#         name=st_point_name,
#         identifier=st_identifier,
#         kwargs=st_kwargs,
#     )
#     def add_point_move(
#         self,
#         pt: Tuple[float, float],
#         smooth: bool,
#         name: Optional[str],
#         identifier: Optional[str],
#         kwargs: Dict[str, Any],
#     ) -> None:
#         self.pen1.addPoint(pt, "move", smooth, name, identifier, **kwargs)
#         self.pen2.addPoint(pt, "move", smooth, name, identifier, **kwargs)
#         self.fresh_path = False
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.DRAWING and self.offcurves == 0)
#     @rule(
#         pt=st_point,
#         smooth=st.booleans(),
#         name=st_point_name,
#         identifier=st_identifier,
#         kwargs=st_kwargs,
#     )
#     def add_point_line(
#         self,
#         pt: Tuple[float, float],
#         smooth: bool,
#         name: Optional[str],
#         identifier: Optional[str],
#         kwargs: Dict[str, Any],
#     ) -> None:
#         self.pen1.addPoint(pt, "line", smooth, name, identifier, **kwargs)
#         self.pen2.addPoint(pt, "line", smooth, name, identifier, **kwargs)
#         self.fresh_path = False
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.DRAWING)
#     @rule(
#         pt=st_point,
#         smooth=st.booleans(),
#         name=st_point_name,
#         identifier=st_identifier,
#         kwargs=st_kwargs,
#     )
#     def add_point_qcurve(
#         self,
#         pt: Tuple[float, float],
#         smooth: bool,
#         name: Optional[str],
#         identifier: Optional[str],
#         kwargs: Dict[str, Any],
#     ) -> None:
#         self.pen1.addPoint(pt, "qcurve", smooth, name, identifier, **kwargs)
#         self.pen2.addPoint(pt, "qcurve", smooth, name, identifier, **kwargs)
#         self.fresh_path = False
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.DRAWING)
#     @rule(
#         pt=st_point,
#         smooth=st.booleans(),
#         name=st_point_name,
#         identifier=st_identifier,
#         kwargs=st_kwargs,
#     )
#     def add_point_curve(
#         self,
#         pt: Tuple[float, float],
#         smooth: bool,
#         name: Optional[str],
#         identifier: Optional[str],
#         kwargs: Dict[str, Any],
#     ) -> None:
#         self.pen1.addPoint(pt, "curve", smooth, name, identifier, **kwargs)
#         self.pen2.addPoint(pt, "curve", smooth, name, identifier, **kwargs)
#         self.fresh_path = False
#         self.offcurves = 0

#     @precondition(lambda self: self.state is PenState.IDLE)
#     @rule(baseGlyphName=st_glyph_name, transformation=st_transformation)
#     def add_component(
#         self,
#         baseGlyphName: str,
#         transformation: Tuple[float, float, float, float, float, float],
#     ) -> None:
#         self.pen1.addComponent(baseGlyphName, transformation)
#         self.pen2.addComponent(baseGlyphName, transformation)

#     # Pens may flush contours to storage only after a path ended.
#     @precondition(lambda self: self.state is PenState.IDLE)
#     @invariant()
#     def pens_agree(self):
#         assert self.glyph1.contours == self.glyph2.contours
#         assert self.glyph1.components == self.glyph2.components


# pentest = PointSegmentPointTest.TestCase
