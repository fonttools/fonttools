from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.timeTools import asctime
import time


def test_asctime():
    assert isinstance(asctime(), basestring)
    assert asctime(time.gmtime(0)) == 'Thu Jan  1 00:00:00 1970'
