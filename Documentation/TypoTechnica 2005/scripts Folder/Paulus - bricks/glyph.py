from robofab.world import CurrentGlyph, CurrentFont

myFont = CurrentFont()
# myGlyph = CurrentGlyph()

myDict = {"fi": ["f", "i"], "fl": ["f", "l"]}

for myLig in myDict:
	for myBasechar in myDict[myLig]:
		print myLig, myBasechar


mySource = myFont["f"]
myDest = myFont["e"]

myDest.appendGlyph(mySource)

myDest.update()
