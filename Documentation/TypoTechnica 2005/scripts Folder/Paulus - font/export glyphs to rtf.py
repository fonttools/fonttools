#FLM: Export glyphs naar RTF

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

mySize = 16
myLeading = 22

myFont = CurrentFont()
myflFont = fl.font
myEncoding = myflFont.encoding

myFontfam = myFont.info.familyName
myFontstyle = myFont.info.styleName
myList = [""] * len(myEncoding)

myPagebreak = ""
myPath = GetFolder()

if myPath:
	myPath += ":" + myFontfam + "-" + myFontstyle + ".rtf"
	
	for myGlyph in myFont:
		myGlyphname = myGlyph.name
		myIndex = myEncoding.FindName(myGlyphname)
		if myIndex is not -1:
			myList[myIndex] = myGlyph.unicode

	myFile = open(myPath, "w")
	myFile.write("{\\rtf1\\mac\\ansicpg1252" + chr(13) + "{\\fonttbl\\f0\\fnil\\cpg819 " + myFontfam + "-" + myFontstyle + ";}" + chr(13) + "\\f0\\sl-" + str(myLeading*20) + "\\fs" + str(mySize*2) + chr(13))

	myBar = ProgressBar('Exporting glyphs...', len(myList))
	for myItem in range (0, len(myList)):
		if myList[myItem]:
			myHex = hex(myItem)[-2:]
			myHex = myHex.replace("x", "0")
			myWord = "\u" + str(myList[myItem]) + "\\'" + myHex + " "
			myFile.write(myWord)
		myBar.tick()
	myPagebreak = "\page "
	myFile.write("}")
	myFile.close()
	myBar.close()
	print "Generated glyph overview for", myFontfam + "-" + myFontstyle
print "Done"
