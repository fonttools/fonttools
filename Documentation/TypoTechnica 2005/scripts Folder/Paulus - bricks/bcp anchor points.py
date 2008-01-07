from robofab.world import CurrentGlyph

myGlyph = CurrentGlyph()

print len(myGlyph)

for myPoint in myGlyph[0].bPoints:
	print myPoint.anchor