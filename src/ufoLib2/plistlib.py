from __future__ import absolute_import

# TODO: rewrite plistlib in cython

try:  # python 3
    from plistlib import load, dump, loads, dumps
except ImportError:  # python 2
    from plistlib import readPlist as load, readPlistFromString as loads
    from plistlib import writePlist as dump, writePlistToString as dumps
