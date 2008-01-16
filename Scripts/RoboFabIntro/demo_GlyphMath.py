#FLM: Fun with GlyphMath

# this example is meant to run with the RoboFab Demo Font
# as the Current Font. So, if you're doing this in FontLab
# import the Demo Font UFO first.

from robofab.world import CurrentFont
from random import random

f = CurrentFont()
condensedLight = f["a#condensed_light"]
wideLight = f["a#wide_light"]
wideBold = f["a#wide_bold"]

diff = wideLight - condensedLight

destination = f.newGlyph("a#deltaexperiment")
destination.clear()
x = wideBold + (condensedLight-wideLight)*random()

destination.appendGlyph( x)
destination.width = x.width
destination.update()
f.update()