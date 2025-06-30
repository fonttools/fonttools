from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Protocol, TypeVar, Union

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from fs.base import FS
    from os import PathLike
    from xml.etree.ElementTree import Element as ElementTreeElement
    from lxml.etree import _Element as LxmlElement

    from fontTools.pens.pointPen import AbstractPointPen
    from fontTools.ufoLib import UFOFormatVersion


T = TypeVar("T")  # Generic type
K = TypeVar("K")  # Generic dict key type
V = TypeVar("V")  # Generic dict value type

GlyphNameToFileNameFunc = Optional[Callable[[str, set[str]], str]]
ElementType = Union[ElementTreeElement, LxmlElement]
IntFloat = Union[int, float]
KerningPair = tuple[str, str]
KerningDict = dict[KerningPair, IntFloat]
KerningGroups = dict[str, Sequence[str]]
KerningNested = dict[str, dict[str, IntFloat]]
PathStr = Union[str, PathLike[str]]
PathOrFS = Union[PathStr, FS]
UFOFormatVersionInput = Optional[Union[int, tuple[int, int], UFOFormatVersion]]
