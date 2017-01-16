from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.sfnt import calcChecksum


def test_calcChecksum():
    assert calcChecksum(b"abcd") == 1633837924
    assert calcChecksum(b"abcdxyz") == 3655064932
