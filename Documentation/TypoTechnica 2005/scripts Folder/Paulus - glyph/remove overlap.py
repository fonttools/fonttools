#FLM: Remove overlap

from robofab.world import CurrentFont, CurrentGlyph

myFont = CurrentFont()
myGlyph = CurrentGlyph()

if myGlyph:
	myGlyph.removeOverlap()
	myGlyph.update()
print "Done"