"""Type information for use across fontTools.

NOTE: The file is called `typings` because removing the "s" would make import clash with
the std-lib import.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, Tuple

# Python's type system currently cannot express a sequence of two. See
# https://github.com/python/mypy/issues/8441.
Point = Sequence[float]
"""A point is a sequence of two numbers."""

Transformation = Tuple[float, float, float, float, float, float]

GlyphSet = Mapping[str, Any]
"""A mapping of glyph names to glyph objects."""

PointType = Optional[str]
PointDescription = Tuple[
    Optional[Point], PointType, bool, Optional[str], Optional[Mapping[str, Any]]
]
"""A point description in a tuple, bundling the point, point type, smooth attribute,
optional name and other kwargs."""
