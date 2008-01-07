from robofab.world import CurrentGlyph, CurrentFont

myFont = CurrentFont()
# myGlyph = CurrentGlyph()

myDict = {"fi": ["f", "i"], "fl": ["f", "l"]}

for myLig in myDict:
	for myBasechar in myDict[myLig]:
		myDest = myFont[myLig]
		mySource = myFont[myBasechar]
		myDest.appendGlyph(mySource)
		myWidth = mySource.width
		for contour in myDest.contours:
			contour.move((-myWidth, 0))
	
	myDest.leftMargin = myFont[myDict[myLig][0]].leftMargin
	myDest.rightMargin = myFont[myDict[myLig][-1]].rightMargin
	
	myDest.update()
