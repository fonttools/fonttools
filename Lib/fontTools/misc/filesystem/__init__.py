"""Minimal, stdlib-only replacement for `pyfilesystem2` API for use by `fontTools.ufoLib`.

External users should not use this module directly.
"""

from __future__ import annotations
from . import base
from . import copy
from . import errors
from . import info
from . import osfs
from . import path
from . import subfs
from . import tempfs
from . import tools
from . import walk
from . import zipfs

__all__ = [
    "base",
    "copy",
    "errors",
    "info",
    "osfs",
    "path",
    "subfs",
    "tempfs",
    "tools",
    "walk",
    "zipfs",
]
