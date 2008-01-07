#FLM: Auto starting points

from robofab.world import CurrentGlyph

myGlyph = CurrentGlyph()

myGlyph.correctDirection()
myGlyph.autoContourOrder()
for contour in myGlyph:
	contour.autoStartSegment()
myGlyph.update()

print "done"
