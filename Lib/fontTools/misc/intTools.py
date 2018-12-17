"""Misc integer tools."""

from __future__ import print_function, absolute_import, division
from fontTools.misc.py23 import *

__all__ = ['popCount']


def popCount(v):
    """Return number of 1 bits in an integer."""

    if v > 0xFFFFFFFF:
        return popCount(v >> 32) + popCount(v & 0xFFFFFFFF)

    # HACKMEM 169
    y = (v >> 1) & 0xDB6DB6DB
    y = v - y - ((y >> 1) & 0xDB6DB6DB)
    return (((y + (y >> 3)) & 0xC71C71C7) % 0x3F)
