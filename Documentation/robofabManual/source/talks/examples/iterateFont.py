# robothon06
# iteration through glyphs in a font

from robofab.world import CurrentFont

font = CurrentFont()
print "font has %d glyphs" % len(font)
for glyph in font:
	print glyph

