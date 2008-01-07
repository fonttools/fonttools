# robothon06
# prepare glyph for interpolation
# move startpoints
# fix directions
# fix contour order
from robofab.world import CurrentFont
f = CurrentFont()
glyph = f["A"]

glyph.autoContourOrder()
glyph.correctDirection()
for c in glyph.contours:
	c.autoStartSegment()
glyph.update()