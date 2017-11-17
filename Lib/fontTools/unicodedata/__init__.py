from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from fontTools.misc.py23 import *

import functools

try:
    # use unicodedata backport compatible with python2:
    # https://github.com/mikekap/unicodedata2
    from unicodedata2 import *
except ImportError:
    # fall back to built-in unicodedata (possibly outdated)
    from unicodedata import *

from .scripts import SCRIPT_RANGES


__all__ = [
    # names from built-in unicodedata module
    "lookup",
    "name",
    "decimal",
    "digit",
    "numeric",
    "category",
    "bidirectional",
    "combining",
    "east_asian_width",
    "mirrored",
    "decomposition",
    "normalize",
    "unidata_version",
    "ucd_3_2_0",
    # additonal functions
    "script",
]


def _memoize(func):
    # Decorator that caches a function's return value each time it is
    # called, and returns the cached value if called later with the same
    # argument.
    cache = func.cache = {}

    @functools.wraps(func)
    def wrapper(arg):
        if arg not in cache:
            cache[arg] = func(arg)
        return cache[arg]
    return wrapper


@_memoize
def script(char):
    """For the unicode character 'char' return the script name."""
    code = byteord(char)
    return _binary_search_range(code, SCRIPT_RANGES, default="Unknown")


def _binary_search_range(code, ranges, default=None):
    left = 0
    right = len(ranges) - 1
    while right >= left:
        mid = (left + right) >> 1
        if code < ranges[mid][0]:
            right = mid - 1
        elif code > ranges[mid][1]:
            left = mid + 1
        else:
            return ranges[mid][2]
    return default
