# robothon06
# iterate through a glyph's contours

from robofab.world import CurrentFont

font = CurrentFont()
glyph = font['A']
print "glyph has %d contours" % len(glyph)
for contour in glyph.contours:
	print contour
	
	