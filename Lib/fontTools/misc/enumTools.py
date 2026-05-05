"""Enum-related utilities, including backports for older Python versions."""

from __future__ import annotations

from enum import Enum
import sys
from typing import cast


__all__ = ["StrEnum"]

# StrEnum is only available in Python 3.11+
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        """
        Minimal backport of Python 3.11's StrEnum for older versions.

        An Enum where all members are also strings.
        """

        def __str__(self) -> str:
            return cast(str, self.value)
