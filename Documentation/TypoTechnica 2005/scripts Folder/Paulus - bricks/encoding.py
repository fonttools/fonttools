from robofab.world import CurrentFont

myFont = fl.font
myrfFont = CurrentFont()
myEncoding = myFont.encoding

print
for myItem in range (0, len(myEncoding)):
	if myFont.FindGlyph(myEncoding[myItem].name) is not -1:
		# print myItem, myEncoding[myItem].name, hex(myEncoding[myItem].unicode)
		myGlyphname = myEncoding[myItem].name
		myGlyph = myrfFont[myGlyphname]
		print myItem, myGlyphname, myGlyph.unicode
print

