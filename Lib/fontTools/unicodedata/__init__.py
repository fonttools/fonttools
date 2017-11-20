from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from fontTools.misc.py23 import *

from bisect import bisect_right

try:
    # use unicodedata backport compatible with python2:
    # https://github.com/mikekap/unicodedata2
    from unicodedata2 import *
except ImportError:
    # fall back to built-in unicodedata (possibly outdated)
    from unicodedata import *

from .scripts import SCRIPT_RANGES, SCRIPT_NAMES


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


def script(char):
    code = byteord(char)
    # 'bisect_right(a, x, lo=0, hi=len(a))' returns an insertion point which
    # comes after (to the right of) any existing entries of x in a, and it
    # partitions array a into two halves so that, for the left side
    # all(val <= x for val in a[lo:i]), and for the right side
    # all(val > x for val in a[i:hi]).
    # Our 'SCRIPT_RANGES' is a sorted list of ranges (only their starting
    # breakpoints); we want to use `bisect_right` to look up the range that
    # contains the given codepoint: i.e. whose start is less than or equal
    # to the codepoint. Thus, we subtract -1 from the index returned.
    i = bisect_right(SCRIPT_RANGES, code)
    return SCRIPT_NAMES[i-1]
