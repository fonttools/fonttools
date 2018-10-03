"""The module contains miscellaneous helpers.
It's not considered part of the public ufoLib API.
"""
from __future__ import absolute_import, unicode_literals
import warnings
import functools


def deprecated(msg=""):
    """Decorator factory to mark functions as deprecated with given message.

    >>> @deprecated("Enough!")
    ... def some_function():
    ...    "I just print 'hello world'."
    ...    print("hello world")
    >>> some_function()
    hello world
    >>> some_function.__doc__
    "I just print 'hello world'."
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


if __name__ == "__main__":
    import doctest

    doctest.testmod()
