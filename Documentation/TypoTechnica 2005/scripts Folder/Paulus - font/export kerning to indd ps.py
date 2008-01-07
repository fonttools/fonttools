#FLM: Export kerning naar tagged text PS

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

myDict = {"Eth": "<0x00D0>", "eth": "<0x00F0>", "Lslash": "<0x0141>", "lslash": "<0x0142>", "Scaron": "<0x0160>", "scaron": "<0x0161>", "Yacute": "<0x00DD>", "yacute": "<0x00FD>", "Thorn": "<0x00DE>", "thorn": "<0x00FE>", "Zcaron": "<0x017D>", "zcaron": "<0x017E>", "brokenbar": "<0x00A6>", "minus": "<0x2212>", "multiply": "<0x00D7>", "space": " ", "exclam": "!", "quotedbl": "\"", "numbersign": "#", "dollar": "$", "percent": "%", "ampersand": "&", "quotesingle": "'", "parenleft": "(", "parenright": ")", "asterisk": "*", "plus": "+", "comma": ",", "hyphen": "-", "period": ".", "slash": "/", "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "colon": ":", "semicolon": ";", "less": "\<", "equal": "=", "greater": "\>", "question": "?", "at": "@", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "H": "H", "I": "I", "J": "J", "K": "K", "L": "L", "M": "M", "N": "N", "O": "O", "P": "P", "Q": "Q", "R": "R", "S": "S", "T": "T", "U": "U", "V": "V", "W": "W", "X": "X", "Y": "Y", "Z": "Z", "bracketleft": "[", "backslash": "\\\\", "bracketright": "]", "asciicircum": "^", "underscore": "_", "grave": "`", "a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f", "g": "g", "h": "h", "i": "i", "j": "j", "k": "k", "l": "l", "m": "m", "n": "n", "o": "o", "p": "p", "q": "q", "r": "r", "s": "s", "t": "t", "u": "u", "v": "v", "w": "w", "x": "x", "y": "y", "z": "z", "braceleft": "{", "bar": "|", "braceright": "}", "asciitilde": "~", "Adieresis": "<0x00C4><0x00C4>", "Aring": "<0x00C5>", "Ccedilla": "<0x00C7>", "Eacute": "<0x00C9>", "Ntilde": "<0x00D1>", "Odieresis": "<0x00D6>", "Udieresis": "<0x00DC>", "aacute": "<0x00E1>", "agrave": "<0x00E0>", "acircumflex": "<0x00E2>", "adieresis": "<0x00E4>", "atilde": "<0x00E3>", "aring": "<0x00E5>", "ccedilla": "<0x00E7>", "eacute": "<0x00E9>", "egrave": "<0x00E8>", "ecircumflex": "<0x00EA>", "edieresis": "<0x00EB>", "iacute": "<0x00ED>", "igrave": "<0x00EC>", "icircumflex": "<0x00EE>", "idieresis": "<0x00EF>", "ntilde": "<0x00F1>", "oacute": "<0x00F3>", "ograve": "<0x00F2>", "ocircumflex": "<0x00F4>", "odieresis": "<0x00F6>", "otilde": "<0x00F5>", "uacute": "<0x00FA>", "ugrave": "<0x00F9>", "ucircumflex": "<0x00FB>", "udieresis": "<0x00FC>", "dagger": "<0x2020>", "degree": "<0x00B0>", "cent": "<0x00A2>", "sterling": "<0x00A3>", "section": "<0x00A7>", "bullet": "<0x2022>", "paragraph": "<0x00B6>", "germandbls": "<0x00DF>", "registered": "<0x00AE>", "copyright": "<0x00A9>", "trademark": "<0x2122>", "acute": "<0x00B4>", "dieresis": "<0x00A8>", "notequal": "<0x2260>", "AE": "<0x00C6>", "Oslash": "<0x00D8>", "plusminus": "<0x00B1>", "lessequal": "<0x2264>", "greaterequal": "<0x2265>", "yen": "<0x00A5>", "ordfeminine": "<0x00AA>", "ordmasculine": "<0x00BA>", "ae": "<0x00E6>", "oslash": "<0x00F8>", "questiondown": "<0x00BF>", "exclamdown": "<0x00A1>", "florin": "<0x0192>", "guillemotleft": "<0x00AB>", "guillemotright": "<0x00BB>", "ellipsis": "<0x2026>", "uni00A0": "<pSG:178><0xFFFD><pSG:>", "Agrave": "<0x00C0>", "Atilde": "<0x00C3>", "Otilde": "<0x00D5>", "OE": "<0x0152>", "oe": "<0x0153>", "endash": "<0x2013>", "emdash": "<0x2014>", "quotedblleft": "<0x201C>", "quotedblright": "<0x201D>", "quoteleft": "<0x2018>", "quoteright": "<0x2019>", "divide": "<0x00F7>", "ydieresis": "<0x00FF>", "Ydieresis": "<0x0178>", "Euro": "<0x20AC>", "guilsinglleft": "<0x2039>", "guilsinglright": "<0x203A>", "fi": "<0xFB01>", "fl": "<0xFB02>", "daggerdbl": "<0x2021>", "periodcentered": "<0x00B7>", "quotesinglbase": "<0x201A>", "quotedblbase": "<0x201E>", "perthousand": "<0x2030>", "Acircumflex": "<0x00C2>", "Ecircumflex": "<0x00CA>", "Aacute": "<0x00C1>", "Edieresis": "<0x00CB>", "Egrave": "<0x00C8>", "Iacute": "<0x00CD>", "Icircumflex": "<0x00CE>", "Idieresis": "<0x00CF>", "Igrave": "<0x00CC>", "Oacute": "<0x00D3>", "Ocircumflex": "<0x00D4>", "apple": "<pSG:215><0xFFFD><pSG:>", "Ograve": "<0x00D2>", "Uacute": "<0x00DA>", "Ucircumflex": "<0x00DB>", "Ugrave": "<0x00D9>", "dotlessi": "<0x0131>", "circumflex": "<0x02C6>", "tilde": "<0x02DC>", "macron": "<0x00AF>", "breve": "<0x02D8>", "dotaccent": "<0x02D9>", "ring": "<0x02DA>", "cedilla": "<0x00B8>", "hungarumlaut": "<0x02DD>", "ogonek": "<0x02DB>", "caron": "<0x02C7>", "currency": "<0x00A4>", "onehalf": "<0x00BD>", "onequarter": "<0x00BC>", "onesuperior": "<0x00B9>", "threequarters": "<0x00BE>", "threesuperior": "<0x00B3>", "twosuperior": "<0x00B2>", "mu": "<0x00B5>", "nbspace": "<pSG:178><0xFFFD><pSG:>", "fraction": "<0x2044>", "logicalnot": "<0x00AC>"}

myFont = CurrentFont()
myKerning = myFont.kerning
myFontfam = myFont.info.familyName
myFontstyle = myFont.info.styleName

myPath = GetFolder()

if myPath:
	myPath += ":" + myFontfam + "-" + myFontstyle + "_kern.txt"
		
	myFile = open(myPath, "w")
	myFile.write("<ASCII-MAC>" + chr(10))
	myFile.write("<vsn:2.000000><fset:InDesign-Roman><ctable:=<Black:COLOR:CMYK:Process:0.000000,0.000000,0.000000,1.000000>>" + chr(10))
	
	myBar = ProgressBar('Exporting kerning...', len(myKerning))
	for myPair in myKerning:
		myComb = str(myPair).split()
		myLeft=myComb[0][2:-2]
		myRight=myComb[1][1:-2]
		if myDict.has_key(myLeft) and myDict.has_key(myRight):
		
			myLine = "<pstyle:><pga:BaseLine><ct:" + myFontstyle + "><cs:11.000000><cl:14.100000><cf:" + myFontfam + ">" + myDict[myLeft] + myDict[myRight] + "<ct:><cs:><cl:><cf:><ct:Regular><cs:5.000000><cl:14.100000><cf:Andale Mono>  " + str(myKerning[myPair]) + chr(10) + "<ct:><cs:><cl:><cf:><pga:>"
			myFile.write(myLine)
			myBar.tick()
	myFile.close()
	myBar.close()
	print "Generated kerning file for", myFontfam, myFontstyle
print "Done"


