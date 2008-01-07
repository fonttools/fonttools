# robothon 2006
# merge two fonts

from robofab.world import SelectFont, NewFont
from robofab.pens.digestPen import DigestPointPen
from sets import Set

font1 = SelectFont("Select base font")
font2 = SelectFont("Select alternate font")

font1Names = Set(font1.keys())
font2Names = Set(font2.keys())

commonNames = font1Names & font2Names
uncommonNames = font2Names - font1Names

for glyphName in commonNames:
	glyph1 = font1[glyphName]
	pointPen = DigestPointPen()
	glyph1.drawPoints(pointPen)
	digest1 = pointPen.getDigest()
	
	glyph2 = font2[glyphName]
	pointPen = DigestPointPen()
	glyph2.drawPoints(pointPen)
	digest2 = pointPen.getDigest()
	
	if digest1 != digest2:
		print '> alt >', glyphName
		glyph3 = font1.insertGlyph(glyph2, as=glyphName+'.alt')
		glyph3.mark = 1
		glyph3.update()

for glyphName in uncommonNames:
	print '>', glyphName
	glyph = font1.insertGlyph(font2[glyphName])
	glyph.mark = 60
	glyph.update()
	
font1.update()
