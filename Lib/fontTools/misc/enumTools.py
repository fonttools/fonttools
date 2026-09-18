"""Enum-related utilities.

Deprecated: this module only re-exports enum.StrEnum for backward compatibility;
import it from the standard library enum module instead.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["StrEnum"]
