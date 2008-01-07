#FLM: Remove overlap

myFont = fl.font
myGlyphs = fl.font.glyphs

for g in range (0,len(myGlyphs)):
	myGlyph = myFont[g]
	myGlyph.RemoveOverlap()
	fl.UpdateGlyph(-1)
print "done"