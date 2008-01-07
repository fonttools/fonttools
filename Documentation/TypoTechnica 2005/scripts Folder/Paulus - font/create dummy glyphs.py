#FLM: Create dummy glyphs in selection

from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar

myFont = CurrentFont()
myGlyphs = myFont.selection
myGlyphwidth = 250
myLines = ((100,250,50),)

bar = ProgressBar('Creating dummy glyphs...', len(myGlyphs))
for myGlyph in myGlyphs:
	myFont[myGlyph].width = myGlyphwidth
	for myLine in myLines:
		myPen = myFont[myGlyph].getPen()
		myMargin = myLine[0]
		myHeight = myLine[1]
		myWeight = myLine[2]
		myStrokewidth = myGlyphwidth -  myMargin
		
		myPen.moveTo((myMargin,myHeight))
		myPen.lineTo((myStrokewidth,myHeight))
		myPen.lineTo((myStrokewidth,myHeight+myWeight))
		myPen.lineTo((myMargin,myHeight+myWeight))
		myPen.lineTo((myMargin,myHeight))
		myPen.closePath()
		
		myFont[myGlyph].update()
	bar.tick()
bar.close()
myFont.update()
print "done"