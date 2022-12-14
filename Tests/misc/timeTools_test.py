from fontTools.misc.timeTools import (
    asctime,
    timestampNow,
    timestampToString,
    timestampFromString,
    epoch_diff,
)
import os
import time
import locale
import pytest


def test_asctime():
    assert isinstance(asctime(), str)
    assert asctime(time.gmtime(0)) == "Thu Jan  1 00:00:00 1970"


def test_source_date_epoch():
    os.environ["SOURCE_DATE_EPOCH"] = "150687315"
    assert timestampNow() + epoch_diff == 150687315

    # Check that malformed value fail, any better way?
    os.environ["SOURCE_DATE_EPOCH"] = "ABCDEFGHI"
    with pytest.raises(ValueError):
        timestampNow()

    del os.environ["SOURCE_DATE_EPOCH"]
    assert timestampNow() + epoch_diff != 150687315


# test for issue #1838
def test_date_parsing_with_locale():
    l = locale.getlocale(locale.LC_TIME)
    try:
        locale.setlocale(locale.LC_TIME, "de_DE.utf8")
    except locale.Error:
        pytest.skip("Locale de_DE not available")

    try:
        assert timestampFromString(timestampToString(timestampNow()))
    finally:
        locale.setlocale(locale.LC_TIME, l)
