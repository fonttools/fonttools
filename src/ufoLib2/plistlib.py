from __future__ import absolute_import

# TODO: rewrite plistlib in cython

try:  # python 3
    from plistlib import load as _load, loads as _loads, FMT_XML as _FMT_XML
    from plistlib import dump, dumps

    # default to XML if no explicit 'fmt' is provided, for backward
    # compatiblity with python2's plistlib which doesn't support binary plist

    def load(fp, fmt=_FMT_XML, **kwargs):
        return _load(fp, fmt=fmt, **kwargs)

    def loads(value, fmt=_FMT_XML, **kwargs):
        return _loads(value, fmt=fmt, **kwargs)


except ImportError:  # python 2
    from plistlib import readPlist as load, readPlistFromString as loads
    from plistlib import writePlist as dump, writePlistToString as dumps
