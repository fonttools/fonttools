# robofab manual
#	bPoint object
#	Attribute examples

g = CurrentGlyph()
for aPt in g[0].bPoints:
	print aPt.bcpIn, aPt.bcpOut, aPt.anchor
