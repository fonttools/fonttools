#FLM: Add remove .sc in selected glyphnames

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import ProgressBar

myFont = CurrentFont()

myGlyphs = myFont.selection

myBar = ProgressBar('Changing names...', len(myGlyphs))
for myGlyph in myGlyphs:
	if myFont[myGlyph].name[-3:] == '.sc':
		myFont[myGlyph].name = myFont[myGlyph].name[:-3]
	else:
		myFont[myGlyph].name += '.sc'
	myFont[myGlyph].update()
	myBar.tick()
myBar.close()
print "done"