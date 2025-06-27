from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple, TypeVar, Union

if TYPE_CHECKING:
    from fontTools.ufoLib import UFOFormatVersion

T = TypeVar("T")  # Generic type
K = TypeVar("K")  # Generic dict key type
V = TypeVar("V")  # Generic dict value type

UFOFormatVersionInput = Optional[Union[int, Tuple[int, int], UFOFormatVersion]]
