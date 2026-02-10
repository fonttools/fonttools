from __future__ import annotations

from typing import Any, Literal, TYPE_CHECKING, TypeVar
from collections.abc import Callable, Iterable, Mapping, Sequence
from os import PathLike
from xml.etree.ElementTree import Element as ElementTreeElement

from fontTools.misc.filesystem._base import FS
from fontTools.misc.transform import Transform

if TYPE_CHECKING:
    from fontTools.ufoLib import UFOFormatVersion
    from fontTools.ufoLib.glifLib import GLIFFormatVersion
    from lxml.etree import _Element as LxmlElement


# ---------------------------------------------------------------------
# Generic type variables
T = TypeVar("T")  # Generic type
K = TypeVar("K")  # Generic dict key type
V = TypeVar("V")  # Generic dict value type

# ---------------------------------------------------------------------
# Generic tuples
Pair = tuple[T, T]
Triple = tuple[T, T, T]
Quadruple = tuple[T, T, T, T]
Sixtuple = tuple[T, T, T, T, T, T]

# ---------------------------------------------------------------------
# Numeric types
IntFloat = int | float
NestedFloat = float | Iterable["NestedFloat"]

# ---------------------------------------------------------------------
# Names and strings
Identifier = str | None
PointName = str | None
SegmentType = str | None

# ---------------------------------------------------------------------
# Paths and file systems
PathStr = str | PathLike[str]
PathOrFS = PathStr | FS

# ---------------------------------------------------------------------
# Points, vectors, lines, curves
Point = Pair[float]
OptionalPoint = Point | None
Vector = Pair[float]
LinePoints = Pair[Point]
LineComplex = Pair[complex]

QuadraticPoints = Triple[Point]
QuadraticComplex = Triple[complex]
CubicPoints = Quadruple[Point]
CubicComplex = Quadruple[complex]
CurvePoints = QuadraticPoints | CubicPoints

# ---------------------------------------------------------------------
# Rectangles
RectFloat = Quadruple[float]
RectInt = Quadruple[int]

# ---------------------------------------------------------------------
# Transform
TransformFloat = Sixtuple[float]
TransformInput = TransformFloat | Transform

# ---------------------------------------------------------------------
# Segments
Smooth = bool
Kwargs = dict[str, Any]
PointRecord = tuple[OptionalPoint, SegmentType, Smooth, PointName, Kwargs]
PointRecordList = list[PointRecord]
# Allows "implied" on-curve point as None
SegmentPoint = tuple[OptionalPoint, Smooth, PointName, Kwargs]
SegmentPointList = list[SegmentPoint]
SegmentList = list[tuple[SegmentType, SegmentPointList]]
# Does not allow "implied" on-curve point (None)
ResolvedSegmentPoint = tuple[Point, Smooth, PointName, Kwargs]
ResolvedSegmentPointList = list[ResolvedSegmentPoint]
ResolvedSegmentList = list[tuple[SegmentType, ResolvedSegmentPointList]]

# ---------------------------------------------------------------------
# Pen recordnings
PenOperator = str
PenOperands = tuple[Any, ...]
PointPenOperands = tuple[Any, ...]
PointPenKwargs = dict[str, Any]
PenRecordingOp = tuple[PenOperator, PenOperands]
PointPenRecordingOp = tuple[PenOperator, PointPenOperands, PointPenKwargs]
PenRecording = list[PenRecordingOp]
PointPenRecording = list[PointPenRecordingOp]

# ---------------------------------------------------------------------
# Mapping
DSLocation = dict[str, float]
GlyphSetMapping = Mapping[str, Any]

# ---------------------------------------------------------------------
# Kerning
KerningPair = Pair[str]
KerningDict = dict[KerningPair, IntFloat]
KerningGroups = dict[str, Sequence[str]]
KerningNested = dict[str, dict[str, IntFloat]]

# ---------------------------------------------------------------------
# UFO / GLIF
FormatVersion = int | Pair[int]
FormatVersions = Iterable[FormatVersion] | None
UFOFormatVersionInput = int | tuple[int, int] | Literal["UFOFormatVersion"] | None
GLIFFormatVersionInput = int | tuple[int, int] | Literal["GLIFFormatVersion"] | None

# ---------------------------------------------------------------------
# XML
ElementType = ElementTreeElement | Literal["LxmlElement"]

# ---------------------------------------------------------------------
# Functions
GlyphNameToFileNameFunc = Callable[[str, set[str]], str] | None
RoundFunc = Callable[[float], int]
ExtremaFunc = Callable[[float, float], float]
SqrtFunc = Callable[[float], float]
