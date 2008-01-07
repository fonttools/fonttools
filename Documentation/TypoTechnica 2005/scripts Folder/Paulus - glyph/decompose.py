#FLM: Decompose composites

from robofab.world import CurrentFont, CurrentGlyph

myFont = CurrentFont()
myGlyph = CurrentGlyph()

if myGlyph.components:
	for c in range(0,len(myGlyph.components)):
		myGlyph.components[0].decompose()
	myGlyph.update()
print "Done"