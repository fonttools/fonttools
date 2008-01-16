#FLM: RoboFab Intro, Font and Glyph Lib

#
#
#	demo of glyph properties
#
#

from robofab.world import OpenFont

# This is a specific test of some features which are probably
# still only supported in one glyph in the DemoFont.ufo,
# which you can find the robofab/Data/ folder. Here is goes.

f = OpenFont(None, "")

for c in f:
	if not c.properties.isEmpty():
		print c.properties.dump()
	
# This prints the available GlyphProperties objects.
# Not very impressive at the moment, but it means
# that at least they're getting stored with the glyphs
# and that they can be read and interpreted.
