# robofab manual
#	Font object
#	Iterate through the font object
#	to get to the glyphs.

f = CurrentFont()
for glyph in f:
	print glyph.name

