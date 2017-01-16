from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import pad


def test_pad():
    assert len(pad(b'abcd', 4)) == 4
    assert len(pad(b'abcde', 2)) == 6
    assert len(pad(b'abcde', 4)) == 8
    assert pad(b'abcdef', 4) == b'abcdef\x00\x00'
    assert pad(b'abcdef', 1) == b'abcdef'
