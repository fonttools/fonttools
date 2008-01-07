#FLM: Draw lines

from robofab.world import CurrentFont

# myLines = ((-10,692,57), (-10,-177,57)) # Fresco kader
myLines = ((-5,-124,48),)


myFont = CurrentFont()
for myGlyph in myFont:

	myGlyphwidth = myFont[myGlyph.name].width
	
	for myLine in myLines:
		myPen = myGlyph.getPen()
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
		
		myGlyph.update()
		
myFont.update()
print "Done"