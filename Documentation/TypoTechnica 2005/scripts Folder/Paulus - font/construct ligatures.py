#FLM: Construct ligatures based on dictionary

from robofab.world import CurrentFont

myFont = CurrentFont()

# myDict = {"fi": ["f", "i"], "fl": ["f", "l"]}
myDict = {"P": ["X", "Z"], "Q": ["Y", "Z"]}
# myDict = {"fi": ["f", "i"], "fl": ["f", "l"], "germandbls": ["s", "s"]}
# myDict = {"g": ["H", "f"], "h": ["H", "F"], "j": ["H", "I"], "K": ["H", "H"]}

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

print "Done"
