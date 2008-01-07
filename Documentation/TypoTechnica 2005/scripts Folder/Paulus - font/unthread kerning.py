#FLM: Unthread kerning and export as AFM files

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

theUppercase = ("Eth", "Lslash", "Scaron", "Yacute", "Thorn", "Zcaron", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "Adieresis", "Aring", "Ccedilla", "Eacute", "Ntilde", "Odieresis", "Udieresis", "AE", "Oslash", "Agrave", "Atilde", "Otilde", "OE", "Ydieresis", "Acircumflex", "Ecircumflex", "Aacute", "Edieresis", "Egrave", "Iacute", "Icircumflex", "Idieresis", "Igrave", "Oacute", "Ocircumflex", "Ograve", "Uacute", "Ucircumflex", "Ugrave")

theLowercase = ("eth", "lslash", "scaron", "yacute", "thorn", "zcaron", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "aacute", "agrave", "acircumflex", "adieresis", "atilde", "aring", "ccedilla", "eacute", "egrave", "ecircumflex", "edieresis", "iacute", "igrave", "icircumflex", "idieresis", "ntilde", "oacute", "ograve", "ocircumflex", "odieresis", "otilde", "uacute", "ugrave", "ucircumflex", "udieresis", "germandbls", "mu", "ae", "oslash", "oe", "ydieresis", "fi", "fl", "dotlessi")

theFigures = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")

thePunctuation = ("exclam", "numbersign", "dollar", "percent", "ampersand", "less", "greater", "question", "questiondown", "exclamdown", "perthousand", "onehalf", "onequarter", "onesuperior", "threequarters", "threesuperior", "twosuperior", "brokenbar", "minus", "multiply", "space", "quotedbl", "quotesingle", "parenleft", "parenright", "asterisk", "plus", "comma", "hyphen", "period", "slash", "colon", "semicolon", "equal", "at", "bracketleft", "backslash", "bracketright", "asciicircum", "underscore", "grave", "braceleft", "bar", "braceright", "asciitilde", "dagger", "degree", "cent", "sterling", "section", "bullet", "paragraph", "registered", "copyright", "trademark", "acute", "dieresis", "plusminus", "yen", "ordfeminine", "ordmasculine", "logicalnot", "florin", "guillemotleft", "guillemotright", "ellipsis", "uni00A0", "endash", "emdash", "quotedblleft", "quotedblright", "quoteleft", "quoteright", "divide", "fraction", "Euro", "guilsinglleft", "guilsinglright", "daggerdbl", "periodcentered", "quotesinglbase", "quotedblbase", "circumflex", "tilde", "macron", "breve", "dotaccent", "ring", "cedilla", "hungarumlaut", "ogonek", "caron", "currency")

# myCollection = {"uc": theUppercase, "lc": theLowercase, "fig": theFigures, "inp": thePunctuation}
# myCollection = {"rest": theUppercase + theLowercase + thePunctuation, "fig": theFigures,}
myCollection = {"uc": theUppercase, "lc": theLowercase, "rest": thePunctuation + theFigures,}

myDict = {}

myFolder = GetFolder()
myFont = CurrentFont()
myflFont = fl.font
myKerning = myFont.kerning

if myFolder:
	myBar = ProgressBar('Unthreading kerning...', len(myKerning))
	for myPair in myKerning:
		myComb = str(myPair).split()
		myLeft = myComb[0][2:-2]
		myRight = myComb[1][1:-2]
		myLeftid = ""
		myRightid = ""
		
		for myGroup in myCollection:
			if myLeft in myCollection[myGroup]:
				myLeftid = str(myGroup)
			if myRight in myCollection[myGroup]:
				myRightid = str(myGroup)
				
		if myRightid == "" or myLeftid == "":
			myLeftid = "! UNKNOWN GLYPH"
			
		myClass =  myLeftid + "-" + myRightid
		myLine = "KPX " + myLeft + " " + myRight + " " + str(myKerning[myPair])
	
		if myDict.has_key(myClass):
			myDict[myClass].append(myLine)
		else:
			myDict[myClass] = [myLine]
			
		myBar.tick()
	
	myBar.close()
	
	myBar = ProgressBar('Writing...', len(myDict))
	
	for myClass in myDict:
		myPath = myFolder + ":" + myClass + "_kerning.afm"
		myFile = open(myPath, "w")
		
		myFile.write("StartFontMetrics 2.0" + chr(10))
		myFile.write("Comment Copyright Paul van der Laan - Unthread kerning script" + chr(10))
		myFile.write("Comment UniqueID " + str(myflFont.unique_id) + chr(10))
		myFile.write("Comment Panose 2 11 9 3 4 0 0 2 0 4" + chr(10))
		myFile.write("FullName " + myflFont.full_name + chr(10))
		myFile.write("FontName " + myflFont.font_name + chr(10))
		myFile.write("FamilyName " + myflFont.family_name + chr(10))
		myFile.write("Weight " + myflFont.weight + chr(10))
		myFile.write("Notice " + chr(10))
		myFile.write("Version " + str(myflFont.version) + chr(10))
		myFile.write("IsFixedPitch false" + chr(10))
		myFile.write("ItalicAngle " + str(myflFont.italic_angle) + chr(10))
		myFile.write("FontBBox -79 -261 1172 865" + chr(10))
		myFile.write("Ascender " + str(myflFont.ascender[0]) + chr(10))
		myFile.write("Descender " + str(myflFont.descender[0]) + chr(10))
		myFile.write("XHeight " + str(myflFont.x_height[0]) + chr(10))
		myFile.write("CapHeight " + str(myflFont.cap_height[0]) + chr(10))
		myFile.write("UnderlinePosition " + str(myflFont.underline_position) + chr(10))
		myFile.write("UnderlineThickness " + str(myflFont.underline_thickness) + chr(10))
		myFile.write("EncodingScheme FontSpecific" + chr(10))
		myFile.write("StartCharMetrics " + str(len(myFont)) + chr(10))
		
		myChar = 1
		for myGlyph in myFont:
			myLine = "C " + str(myChar) + " ; WX "+ str(myGlyph.width) + " ; N " + str(myGlyph.name) + " ; B " + str(myGlyph.box)[1:-1] + chr(10)
			myFile.write(myLine)
			myChar += 1
			
		myFile.write("EndCharMetrics" + chr(10))
		myFile.write("StartKernData" + chr(10))
		myFile.write("StartKernPairs " + str(len(myDict[myClass])) + chr(10))
		
		for myPair in myDict[myClass]:
			myFile.write(myPair + chr(10))
			
		myFile.write("EndKernPairs" + chr(10))
		myFile.write("EndKernData" + chr(10))
		myFile.write("EndFontMetrics" + chr(10))
		
		myFile.close()
		print "Generated", myPath
		myBar.tick()
		
	myBar.close()
			
print "Done"