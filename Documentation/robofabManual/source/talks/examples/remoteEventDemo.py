# robothon06
# demo of executing python in FontLab
# sent from an outside program
# using AppleEvents. MacOS only.

from robofab.tools.remote import runFontLabRemote

pythonCode = """
from robofab.world import CurrentGlyph
from robofab.tools.remote import transmitGlyph
g = CurrentGlyph
transmitGlyph(g)
"""

print runFontLabRemote(pythonCode)