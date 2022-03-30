# from string import ascii_letters, digits, printable
# from typing import Any, Dict, Optional, Tuple, NamedTuple

# from fontTools.pens.pointPen import AbstractPointPen
# from hypothesis import strategies as st

# # XXX: generate glyph (Tests/pens/recordingPen_test.py -> _TestGlyph) instead
# #      of command stream and draw that into recordingpens? TestGlyph (has contours,
# #      components and contour vars) plus TestPointPen
# # - segment @composite of (zero or more offcurves, type point) so we can keep having one add_point method?

# glyph_names = st.text(ascii_letters + digits + "._")
# coordinates = st.floats() | st.integers()
# points = st.tuples(coordinates, coordinates)
# identifiers = st.none() | st.text(printable)
# point_names = st.none() | st.text(printable)
# transformations = st.tuples(
#     coordinates,
#     coordinates,
#     coordinates,
#     coordinates,
#     coordinates,
#     coordinates,
# )
# kwargs = st.dictionaries(
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

# class Contour(NamedTuple):
#     identifier: Optional[str]
#     points: List[Point]


# class TestPointPen(AbstractPointPen):
#     __slots__ = "current_contour", "contours", "components"

#     def __init__(self) -> None:
#         self.current_contour: List[Contour] = None
#         self.contours: "Glyph" = glyph
#         self.components: List[Contour] = None

#     def beginPath(self, identifier: Optional[str] = None, **kwargs: Any) -> None:
#         self._contour = Contour(identifier=identifier)

#     def endPath(self) -> None:
#         if self._contour is None:
#             raise ValueError("Call beginPath first.")
#         self._glyph.contours.append(self._contour)
#         self._contour = None

#     def addPoint(
#         self,
#         pt: Tuple[float, float],
#         segmentType: Optional[str] = None,
#         smooth: bool = False,
#         name: Optional[str] = None,
#         identifier: Optional[str] = None,
#         **kwargs: Any,
#     ) -> None:
#         if self._contour is None:
#             raise ValueError("Call beginPath first.")
#         x, y = pt
#         self._contour.append(
#             Point(
#                 x, y, type=segmentType, smooth=smooth, name=name, identifier=identifier
#             )
#         )

#     def addComponent(
#         self,
#         baseGlyph: str,
#         transformation: Transform,
#         identifier: Optional[str] = None,
#         **kwargs: Any,
#     ) -> None:
#         component = Component(baseGlyph, transformation, identifier=identifier)
#         self._glyph.components.append(component)
