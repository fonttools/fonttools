"""fontTools.ufoLib -- a package for dealing with UFO fonts."""

# The structure of UFO font files is defined here:
# http://unifiedfontobject.org/

from fontTools.ufoLib.objects import Font
from fontTools.ufoLib.reader import UFOReader
from fontTools.ufoLib.writer import UFOWriter

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"


__all__ = ["Font", "UFOReader", "UFOWriter"]
