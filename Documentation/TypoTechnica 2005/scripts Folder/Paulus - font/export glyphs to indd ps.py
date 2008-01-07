#FLM: Export glyphs naar tagged text PS

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

myDict = {"A": ("A", 1), "Aacute": ("<0x00C1>", 2), "Acircumflex": ("<0x00C2>", 3), "Adieresis": ("<0x00C4><0x00C4>", 4), "Agrave": ("<0x00C0>", 5), "Aring": ("<0x00C5>", 6), "Atilde": ("<0x00C3>", 7), "AE": ("<0x00C6>", 8), "B": ("B", 9), "C": ("C", 10), "Ccedilla": ("<0x00C7>", 11), "D": ("D", 12), "Eth": ("<0x00D0>", 13), "E": ("E", 14), "Eacute": ("<0x00C9>", 15), "Ecircumflex": ("<0x00CA>", 16), "Edieresis": ("<0x00CB>", 17), "Egrave": ("<0x00C8>", 18), "F": ("F", 19), "G": ("G", 20), "H": ("H", 21), "I": ("I", 22), "Iacute": ("<0x00CD>", 23), "Icircumflex": ("<0x00CE>", 24), "Idieresis": ("<0x00CF>", 25), "Igrave": ("<0x00CC>", 26), "J": ("J", 27), "K": ("K", 28), "L": ("L", 29), "Lslash": ("<0x0141>", 30), "M": ("M", 31), "N": ("N", 32), "Ntilde": ("<0x00D1>", 33), "O": ("O", 34), "Oacute": ("<0x00D3>", 35), "Ocircumflex": ("<0x00D4>", 36), "Odieresis": ("<0x00D6>", 37), "Ograve": ("<0x00D2>", 38), "Oslash": ("<0x00D8>", 39), "Otilde": ("<0x00D5>", 40), "OE": ("<0x0152>", 41), "P": ("P", 42), "Thorn": ("<0x00DE>", 43), "Q": ("Q", 44), "R": ("R", 45), "S": ("S", 46), "Scaron": ("<0x0160>", 47), "T": ("T", 48), "U": ("U", 49), "Uacute": ("<0x00DA>", 50), "Ucircumflex": ("<0x00DB>", 51), "Udieresis": ("<0x00DC>", 52), "Ugrave": ("<0x00D9>", 53), "V": ("V", 54), "W": ("W", 55), "X": ("X", 56), "Y": ("Y", 57), "Yacute": ("<0x00DD>", 58), "Ydieresis": ("<0x0178>", 59), "Z": ("Z", 60), "Zcaron": ("<0x017D>", 61), "a": ("a", 62), "aacute": ("<0x00E1>", 63), "acircumflex": ("<0x00E2>", 64), "adieresis": ("<0x00E4>", 65), "agrave": ("<0x00E0>", 66), "aring": ("<0x00E5>", 67), "atilde": ("<0x00E3>", 68), "ae": ("<0x00E6>", 69), "b": ("b", 70), "c": ("c", 71), "ccedilla": ("<0x00E7>", 72), "d": ("d", 73), "eth": ("<0x00F0>", 74), "e": ("e", 75), "eacute": ("<0x00E9>", 76), "ecircumflex": ("<0x00EA>", 77), "edieresis": ("<0x00EB>", 78), "egrave": ("<0x00E8>", 79), "f": ("f", 80), "fi": ("<0xFB01>", 81), "fl": ("<0xFB02>", 82), "g": ("g", 83), "h": ("h", 84), "i": ("i", 85), "iacute": ("<0x00ED>", 86), "icircumflex": ("<0x00EE>", 87), "idieresis": ("<0x00EF>", 88), "igrave": ("<0x00EC>", 89), "dotlessi": ("<0x0131>", 90), "j": ("j", 91), "k": ("k", 92), "l": ("l", 93), "lslash": ("<0x0142>", 94), "m": ("m", 95), "n": ("n", 96), "ntilde": ("<0x00F1>", 97), "o": ("o", 98), "oacute": ("<0x00F3>", 99), "ocircumflex": ("<0x00F4>", 100), "odieresis": ("<0x00F6>", 101), "ograve": ("<0x00F2>", 102), "oslash": ("<0x00F8>", 103), "otilde": ("<0x00F5>", 104), "oe": ("<0x0153>", 105), "p": ("p", 106), "thorn": ("<0x00FE>", 107), "q": ("q", 108), "r": ("r", 109), "s": ("s", 110), "scaron": ("<0x0161>", 111), "germandbls": ("<0x00DF>", 112), "t": ("t", 113), "u": ("u", 114), "uacute": ("<0x00FA>", 115), "ucircumflex": ("<0x00FB>", 116), "udieresis": ("<0x00FC>", 117), "ugrave": ("<0x00F9>", 118), "v": ("v", 119), "w": ("w", 120), "x": ("x", 121), "y": ("y", 122), "yacute": ("<0x00FD>", 123), "ydieresis": ("<0x00FF>", 124), "z": ("z", 125), "zcaron": ("<0x017E>", 126), "zero": ("0", 127), "one": ("1", 128), "two": ("2", 129), "three": ("3", 130), "four": ("4", 131), "five": ("5", 132), "six": ("6", 133), "seven": ("7", 134), "eight": ("8", 135), "nine": ("9", 136), "onesuperior": ("<0x00B9>", 137), "twosuperior": ("<0x00B2>", 138), "threesuperior": ("<0x00B3>", 139), "onequarter": ("<0x00BC>", 140), "onehalf": ("<0x00BD>", 141), "threequarters": ("<0x00BE>", 142), "space": (" ", 143), "percent": ("%", 144), "perthousand": ("<0x2030>", 145), "cent": ("<0x00A2>", 146), "Euro": ("<0x20AC>", 147), "florin": ("<0x0192>", 148), "sterling": ("<0x00A3>", 149), "dollar": ("$", 150), "yen": ("<0x00A5>", 151), "currency": ("<0x00A4>", 152), "ampersand": ("&", 153), "comma": (",", 154), "semicolon": (";", 155), "period": (".", 156), "colon": (":", 157), "ellipsis": ("<0x2026>", 158), "exclam": ("!", 159), "question": ("?", 160), "exclamdown": ("<0x00A1>", 161), "questiondown": ("<0x00BF>", 162), "quotedblbase": ("<0x201E>", 163), "quotedblleft": ("<0x201C>", 164), "quotedblright": ("<0x201D>", 165), "quotesinglbase": ("<0x201A>", 166), "quoteleft": ("<0x2018>", 167), "quoteright": ("<0x2019>", 168), "guilsinglleft": ("<0x2039>", 169), "guillemotleft": ("<0x00AB>", 170), "guilsinglright": ("<0x203A>", 171), "guillemotright": ("<0x00BB>", 172), "quotesingle": ("'", 173), "quotedbl": ("\"", 174), "at": ("@", 175), "registered": ("<0x00AE>", 176), "copyright": ("<0x00A9>", 177), "trademark": ("<0x2122>", 178), "mu": ("<0x00B5>", 179), "slash": ("/", 180), "backslash": ("\\\\", 181), "braceleft": ("{", 182), "braceright": ("}", 183), "bracketleft": ("[", 184), "bracketright": ("]", 185), "parenleft": ("(", 186), "parenright": (")", 187), "bar": ("|", 188), "brokenbar": ("<0x00A6>", 189), "asterisk": ("*", 190), "dagger": ("<0x2020>", 191), "daggerdbl": ("<0x2021>", 192), "degree": ("<0x00B0>", 193), "section": ("<0x00A7>", 194), "paragraph": ("<0x00B6>", 195), "ordfeminine": ("<0x00AA>", 196), "ordmasculine": ("<0x00BA>", 197), "bullet": ("<0x2022>", 198), "numbersign": ("#", 199), "plus": ("+", 200), "plusminus": ("<0x00B1>", 201), "minus": ("<0x2212>", 202), "multiply": ("<0x00D7>", 203), "periodcentered": ("<0x00B7>", 204), "divide": ("<0x00F7>", 205), "equal": ("=", 206), "notequal": ("<0x2260>", 207), "less": ("\<", 208), "lessequal": ("<0x2264>", 209), "greaterequal": ("<0x2265>", 210), "greater": ("\>", 211), "logicalnot": ("<0x00AC>", 212), "underscore": ("_", 213), "hyphen": ("-", 214), "endash": ("<0x2013>", 215), "emdash": ("<0x2014>", 216), "logicalnot": ("<0x00AC>", 217), "fraction": ("<0x2044>", 218), "uni00A0": ("<pSG:173><0xFFFD><pSG:>", 220), "asciitilde": ("~", 221), "asciicircum": ("^", 222), "acute": ("<0x00B4>", 223), "grave": ("`", 224), "hungarumlaut": ("<0x02DD>", 225), "breve": ("<0x02D8>", 226), "caron": ("<0x02C7>", 227), "circumflex": ("<0x02C6>", 228), "dieresis": ("<0x00A8>", 229), "dotaccent": ("<0x02D9>", 230), "ring": ("<0x02DA>", 231), "macron": ("<0x00AF>", 232), "tilde": ("<0x02DC>", 233), "cedilla": ("<0x00B8>", 234), "ogonek": ("<0x02DB>", 235)}

# "nbspace": ("<pSG:173><0xFFFD><pSG:>", 219), "apple": ("<pSG:215><0xFFFD><pSG:>", 236

myFont = CurrentFont()
myFontfam = myFont.info.familyName
myFontstyle = myFont.info.styleName

myList = [""]*(len(myDict)+3)
myPagebreak = ""
myPath = GetFolder()

if myPath:
	myPath += ":" + myFontfam + "-" + myFontstyle + ".txt"
	
	for myChar in myFont:
		if myDict.has_key(myChar.name):
			myList[myDict[myChar.name][1]]=myDict[myChar.name][0]

	myFile = open(myPath, "w")
	myFile.write("<ASCII-MAC>" + chr(10))
	myFile.write("<vsn:2.000000><fset:InDesign-Roman><ctable:=<Black:COLOR:CMYK:Process:0.000000,0.000000,0.000000,1.000000>>" + chr(10))
	
	myBar = ProgressBar('Exporting glyphs...', len(myList))
	myLine = myPagebreak + "<pstyle:><ct:Regular><cs:6.000000><cl:12.000000><cf:Andale Mono>" + myFontfam + "-" + myFontstyle + " glyph overview, generated 26 10 2004<cf:><cl:><cs:><ct:>" + chr(10) + "<pstyle:><ct:Regular><cs:6.000000><cl:12.000000><cf:Andale Mono>Version " + str(myFont.info.versionMajor) + "." + str(myFont.info.versionMinor) + ", designed by " + myFont.info.designer + ", " + str(myFont.info.year) + ".<cf:><cl:><cs:><ct:>" + chr(10) + "<pstyle:><ct:Regular><cs:9.000000><cl:14.000000><cf:Andale Mono><cf:><cl:><cs:><ct:>"  + chr(10) + "<pstyle:><cs:54.000000><cl:58.000000><cf:TEFF><ct:Pi> | <ct:><cf:>"
	myFile.write(myLine)	
	for myItem in range(0,len(myList)):
		if myList[myItem]:
			myLine = "<cf:" + myFontfam + "><ct:" + myFontstyle + ">" + myList[myItem] + "<ct:><cf:><cf:TEFF><ct:Pi>| |<ct:><cf:>"
			myFile.write(myLine)
		myBar.tick()
	myFile.write("<cl:><cs:>")
	myPagebreak = "<cnxc:Page>"
	myFile.close()
	myBar.close()
	print "Generated glyph overview for", myFontfam + "-" + myFontstyle
print "Done"
