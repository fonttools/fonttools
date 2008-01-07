#FLM: Copy all glyphs to other font

# werkt helaas nog steeds niet...

from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import SelectFont

mySource = CurrentFont()
myDest = SelectFont('Select a destination font:')

if myDest:
	for myGlyph in mySource:
		myGlyphname = myGlyph.name
		if myDest.has_key(myGlyphname):
			myDest.removeGlyph(myGlyphname)
			myDest[myGlyphname].appendGlyph(mySource[myGlyphname])
			# myDest[myGlyphname].mark = 52
			myDest.update()

print "Done"
