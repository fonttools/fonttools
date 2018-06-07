"""ufoLib2 -- a package for dealing with UFO fonts."""

# The structure of UFO font files is defined here:
# http://unifiedfontobject.org/

from ufoLib2.objects import Font
from ufoLib2.reader import UFOReader
from ufoLib2.writer import UFOWriter

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"


__all__ = ["Font", "UFOReader", "UFOWriter"]
