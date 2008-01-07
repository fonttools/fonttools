#FLM: Batch export glyphs to rtf

#	Paul van der Laan, 2004/11/02


from robofab.interface.all.dialogs import GetFolder, ProgressBar
from robofab.world import RFont, OpenFont
import os

mySize = 16
myLeading = 22


# Een functie om een map met files door te zoeken op vfb files
def collectSources(root):
	files = []
	ext = ['.vfb']
	names = os.listdir(root)
	for n in names:
		if os.path.splitext(n)[1] in ext:
			files.append(os.path.join(root, n))
	return files

# main loop
mySource = GetFolder()
if mySource is not None:
	myPath = mySource + ":glyph overview.rtf"
	myrtfFile = open(myPath, "w")
	myrtfFile.write("{\\rtf1\\mac\\ansicpg1252" + chr(13))
	myPagebreak = ""
	
	myFiles = collectSources(mySource)
	for myFile in myFiles:
		myFont = None
		try:
			myFont = OpenFont(myFile)
			myflFont = fl.font
			myEncoding = myflFont.encoding
			myFontfam = myFont.info.familyName
			myFontstyle = myFont.info.styleName
			myList = [""] * len(myEncoding)
			
			for myGlyph in myFont:
				myGlyphname = myGlyph.name
				myIndex = myEncoding.FindName(myGlyphname)
				if myIndex is not -1:
					myList[myIndex] = myGlyph.unicode
			
			if myFont.info.designer is None:
				myFont.info.designer = "-"
			if myFont.info.year is None:
				myFont.info.year = "1452"
			
			myBar = ProgressBar('Exporting glyphs...', len(myList))
			myLine = myPagebreak + "{\\fonttbl\\f0\\fnil\\cpg819 " + myFontfam + "-" + myFontstyle + ";}" + chr(13) + "\\f0\\sl-" + str(myLeading*20) + "\\fs" + str(mySize*2) + chr(13) + "\\par "
			myrtfFile.write(myLine)
			for myItem in range (0, len(myList)):
				if myList[myItem]:
					myHex = hex(myItem)[-2:]
					myHex = myHex.replace("x", "0")
					myWord = "\u" + str(myList[myItem]) + "\\'" + myHex + " "
					myrtfFile.write(myWord)
				myBar.tick()
			myPagebreak = "\page" + chr(13)
			myBar.close()
		finally:
			if myFont is not None:
				myFont.close(False)
		print "Generated glyph overview for", myFontfam + "-" + myFontstyle
	myrtfFile.write(chr(13) + "}")
	myrtfFile.close()
print "Done"



# \f0\fnil\fcharset77 AndaleMono;# \f1\fswiss\fcharset77 Helvetica;# \f2\fnil\fcharset77 Georgia;
