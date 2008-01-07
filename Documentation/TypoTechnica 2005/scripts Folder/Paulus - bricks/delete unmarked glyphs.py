

from robofab.world import CurrentFont

myFont = CurrentFont()

for myGlyph in myFont:
	myGlyphname = myGlyph.name
	if myGlyph.mark == 0:
		myFont.removeGlyph(myGlyphname)
myFont.update()
print "done"
