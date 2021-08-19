"""Python 2/3 compat layer leftovers."""

import warnings

from ._py23 import (
    basestring,
    bytechr,
    byteord,
    BytesIO,
    bytesjoin,
    open,
    Py23Error,
    range,
    RecursionError,
    round,
    SimpleNamespace,
    StringIO,
    strjoin,
    Tag,
    tobytes,
    tostr,
    tounicode,
    unichr,
    unicode,
    UnicodeIO,
    xrange,
    zip,
)

warnings.warn(
    "The py23 module has been deprecated and will be removed in a future release. "
    "Please update your code.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "basestring",
    "bytechr",
    "byteord",
    "BytesIO",
    "bytesjoin",
    "open",
    "Py23Error",
    "range",
    "RecursionError",
    "round",
    "SimpleNamespace",
    "StringIO",
    "strjoin",
    "Tag",
    "tobytes",
    "tostr",
    "tounicode",
    "unichr",
    "unicode",
    "UnicodeIO",
    "xrange",
    "zip",
]
