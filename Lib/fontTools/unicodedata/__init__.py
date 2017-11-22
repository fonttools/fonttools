from __future__ import (
    print_function, division, absolute_import, unicode_literals)
from fontTools.misc.py23 import *

from bisect import bisect_right

try:
    # use unicodedata backport compatible with python2:
    # https://github.com/mikekap/unicodedata2
    from unicodedata2 import *
except ImportError:  # pragma: no cover
    # fall back to built-in unicodedata (possibly outdated)
    from unicodedata import *

from . import Blocks, Scripts, ScriptExtensions


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
    "block",
    "script",
    "script_extension",
]


def script(char):
    """ Return the four-letter script code assigned to the Unicode character
    'char' as string.

    >>> script("a")
    'Latn'
    >>> script(",")
    'Zyyy'
    >>> script(unichr(0x10FFFF))
    'Zzzz'
    """
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
    i = bisect_right(Scripts.RANGES, code)
    return Scripts.VALUES[i-1]


def script_extension(char):
    """ Return the script extension property assigned to the Unicode character
    'char' as a set of string.

    >>> script_extension("a") == {'Latn'}
    True
    >>> script_extension(unichr(0x060C)) == {'Arab', 'Syrc', 'Thaa'}
    True
    >>> script_extension(unichr(0x10FFFF)) == {'Zzzz'}
    True
    """
    code = byteord(char)
    i = bisect_right(ScriptExtensions.RANGES, code)
    value = ScriptExtensions.VALUES[i-1]
    if value is None:
        # code points not explicitly listed for Script Extensions
        # have as their value the corresponding Script property value
        return {script(char)}
    return value


def script_name(code):
    """ Return the long, human-readable script name given a four-letter
    Unicode script code.

    Raises KeyError if no matching name is found.
    """
    return Scripts.NAMES[code].replace("_", " ")


def block(char):
    """ Return the block property assigned to the Unicode character 'char'
    as a string.

    >>> block("a")
    'Basic Latin'
    >>> block(unichr(0x060C))
    'Arabic'
    >>> block(unichr(0xEFFFF))
    'No_Block'
    """
    code = byteord(char)
    i = bisect_right(Blocks.RANGES, code)
    return Blocks.VALUES[i-1]
