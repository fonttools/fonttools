"""Python 2/3 compat layer leftovers."""

__all__ = [
    "basestring",
    "unicode",
    "unichr",
    "byteord",
    "bytechr",
    "strjoin",
    "bytesjoin",
    "tobytes",
    "tostr",
    "tounicode",
    "Tag",
]

basestring = str
unichr = chr
unicode = str


def bytechr(n):
    return bytes([n])


def byteord(c):
    return c if isinstance(c, int) else ord(c)


def strjoin(iterable, joiner=""):
    return tostr(joiner).join(iterable)


def tobytes(s, encoding="ascii", errors="strict"):
    if not isinstance(s, bytes):
        return s.encode(encoding, errors)
    else:
        return s


def tounicode(s, encoding="ascii", errors="strict"):
    if not isinstance(s, unicode):
        return s.decode(encoding, errors)
    else:
        return s


tostr = tounicode


class Tag(str):
    @staticmethod
    def transcode(blob):
        if isinstance(blob, bytes):
            blob = blob.decode("latin-1")
        return blob

    def __new__(self, content):
        return str.__new__(self, self.transcode(content))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        return str.__eq__(self, self.transcode(other))

    def __hash__(self):
        return str.__hash__(self)

    def tobytes(self):
        return self.encode("latin-1")


def bytesjoin(iterable, joiner=b""):
    return tobytes(joiner).join(tobytes(item) for item in iterable)


if __name__ == "__main__":
    import doctest, sys

    sys.exit(doctest.testmod().failed)
