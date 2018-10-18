"""The module contains miscellaneous helpers.
It's not considered part of the public ufoLib API.
"""
from __future__ import absolute_import, unicode_literals
import sys
import warnings
import functools
from datetime import datetime
from fontTools.misc.py23 import tounicode


if hasattr(datetime, "timestamp"):  # python >= 3.3

    def datetimeAsTimestamp(dt):
        return dt.timestamp()

else:
    from datetime import tzinfo, timedelta

    ZERO = timedelta(0)

    class UTC(tzinfo):

        def utcoffset(self, dt):
            return ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return ZERO

    utc = UTC()

    EPOCH = datetime.fromtimestamp(0, tz=utc)

    def datetimeAsTimestamp(dt):
        return (dt - EPOCH).total_seconds()


# TODO: should import from fontTools.misc.py23
try:
	long = long
except NameError:
	long = int

integerTypes = (int, long)
numberTypes = (int, float, long)


def deprecated(msg=""):
    """Decorator factory to mark functions as deprecated with given message.

    >>> @deprecated("Enough!")
    ... def some_function():
    ...    "I just print 'hello world'."
    ...    print("hello world")
    >>> some_function()
    hello world
    >>> some_function.__doc__ == "I just print 'hello world'."
    True
    """

    def deprecated_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                "{} function is a deprecated. {}".format(func.__name__, msg),
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return deprecated_decorator


def fsdecode(path, encoding=sys.getfilesystemencoding()):
    return tounicode(path, encoding=encoding)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
