"""fontTools.ufoLib -- a package for dealing with UFO fonts."""

# The structure of UFO font files is defined here:
# http://unifiedfontobject.org/

from fontTools.ufoLib.objects import Font
from fontTools.ufoLib.reader import UFOReader
from fontTools.ufoLib.writer import UFOWriter


__all__ = ["Font", "UFOReader", "UFOWriter"]
