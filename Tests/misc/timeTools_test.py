from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.timeTools import asctime, timestampNow, epoch_diff
import os
import time
import pytest


def test_asctime():
    assert isinstance(asctime(), basestring)
    assert asctime(time.gmtime(0)) == 'Thu Jan  1 00:00:00 1970'


def test_source_date_epoch():
    os.environ["SOURCE_DATE_EPOCH"] = "150687315"
    assert timestampNow() + epoch_diff == 150687315

    # Check that malformed value fail, any better way?
    os.environ["SOURCE_DATE_EPOCH"] = "ABCDEFGHI"
    with pytest.raises(ValueError):
        timestampNow()

    del os.environ["SOURCE_DATE_EPOCH"]
    assert timestampNow() + epoch_diff != 150687315
