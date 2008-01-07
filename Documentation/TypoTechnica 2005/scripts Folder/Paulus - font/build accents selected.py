#FLM: Build accents for selected glyphs

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import ProgressBar

myFont = CurrentFont()

myGlyphs = myFont.selection

myBar = ProgressBar('Building accents...', len(myGlyphs))
for myGlyph in myGlyphs:
	myFont.generateGlyph(myGlyph, replace=True, printErrors=True)
	myFont[myGlyph].update()
	myBar.tick()
myBar.close()
print "done"