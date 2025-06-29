from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, TypeVar, Union
    from collections.abc import Callable
    from fs.base import FS
    from os import PathLike
    from xml.etree.ElementTree import Element as ElementTreeElement
    from lxml.etree import _Element as LxmlElement

    from fontTools.ufoLib import UFOFormatVersion

T = TypeVar("T")  # Generic type
K = TypeVar("K")  # Generic dict key type
V = TypeVar("V")  # Generic dict value type

GlyphNameToFileNameFunc = Optional[Callable[[str, set[str]], str]]
ElementType = Union[ElementTreeElement, LxmlElement]
IntFloat = Union[int, float]
KerningNested = dict[str, dict[str, IntFloat]]
PathStr = Union[str, PathLike[str]]
PathOrFS = Union[PathStr, FS]
UFOFormatVersionInput = Optional[Union[int, tuple[int, int], UFOFormatVersion]]
