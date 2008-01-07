from robofab.world import CurrentFont

myFont = CurrentFont()
myflFont = fl.font
myEncoding = myflFont.encoding

myList = [""] * len(myEncoding)

print ""
for myGlyph in myFont:
	myGlyphname = myGlyph.name
	myIndex = myEncoding.FindName(myGlyphname)
	if myIndex is not -1:
		myList[myIndex] = myGlyph.unicode

for myItem in range (0, len(myList)):
	if myList[myItem] is not "":
		myHex = hex(myItem)[-2:]
		myHex = myHex.replace("x", "0")
		print "\u" + str(myList[myItem]) + "\\'" + myHex