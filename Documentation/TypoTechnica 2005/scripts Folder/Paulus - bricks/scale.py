from robofab.world import CurrentFont, CurrentGlyph

myFont = CurrentFont()
# myGlyph = CurrentGlyph()

mySelection=['Eth', 'Lslash', 'Scaron', 'Yacute', 'Thorn', 'Zcaron', 'dollar', 'percent', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Adieresis', 'Aring', 'Ccedilla', 'Eacute', 'Ntilde', 'Odieresis', 'Udieresis', 'cent', 'sterling', 'AE', 'Oslash', 'yen', 'florin', 'Agrave', 'Atilde', 'Otilde', 'OE', 'Ydieresis', 'currency', 'perthousand', 'Acircumflex', 'Ecircumflex', 'Aacute', 'Edieresis', 'Egrave', 'Iacute', 'Icircumflex', 'Idieresis', 'Igrave', 'Oacute', 'Ocircumflex', 'Ograve', 'Uacute', 'Ucircumflex', 'Ugrave']

for myGlyph in mySelection:
	myFont[myGlyph].scale((1,0.9), center=(0,0))
	myFont[myGlyph].mark = 26
	
myFont.update()
