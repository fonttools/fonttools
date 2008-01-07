
# deletes horizontal hint with position -135 in all glyphs

# myGlyph = fl.glyph

myFont = fl.font
myGlyphs = fl.font.glyphs

for g in range (0,len(myGlyphs)):
	myGlyph = myFont[g]
	myHints = myGlyph.hhints
	for h in range(0,len(myHints)):
		# print myGlyph, len(myHints)
		if myHints[h].position == -124:
			del myHints[h]
			fl.UpdateGlyph(-1)
			break
print "done"