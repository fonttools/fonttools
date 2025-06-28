from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional, Tuple, TypeVar, Union

if TYPE_CHECKING:
    from fontTools.ufoLib import UFOFormatVersion

T = TypeVar("T")  # Generic type
K = TypeVar("K")  # Generic dict key type
V = TypeVar("V")  # Generic dict value type

IntFloat = Union[int, float]
KerningNested = Dict[str, Dict[str, IntFloat]]
UFOFormatVersionInput = Optional[Union[int, Tuple[int, int], UFOFormatVersion]]
