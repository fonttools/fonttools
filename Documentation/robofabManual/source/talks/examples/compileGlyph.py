# robothon06
# Compile a new glyph from a list of accents and required anchors
# Demo of multiple accents chaining together, or "stacking".
# For this example you need to set  up a couple of things
# in your test font:
#	- base glyph "a", with anchor "top" and anchor "bottom"
#	- glyph "dieresis" with anchor "_top" and anchor "top"
#	- glyph "acture" with anchor "_top"
#	- glyph "cedilla" with anchor "_bottom"
#

from robofab.world import CurrentFont
font = CurrentFont()

# this is a list of tuples
# each tuple has the name of the accent as first element
# and the name of the anchor which to use as the second element
accentList = [("dieresis", "top"),
	("acute", "top"),
	("cedilla", "bottom")]

# The accents are compiled in this order, so first
#	"dieresis" connects to "a" using "top" anchor
#	"acute" connects to dieresis, using the next "top" anchor

font.compileGlyph("myCompiledGlyph", "a", accentList)
font.update()

