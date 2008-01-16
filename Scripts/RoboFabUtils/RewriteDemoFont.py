"""Read all glyphs from the demo font, and write them out again.
This is useful for testing round-tripping stability, but also to
update the font when the GLIF format changes. The third application
is to update the contents.plist file in case glyphs have been added
or removed.
"""


import os
from robofab.test.testSupport import getDemoFontPath
from robofab.glifLib import GlyphSet
from robofab.pens.adapterPens import GuessSmoothPointPen

ufoPath = getDemoFontPath()
glyphSet = GlyphSet(os.path.join(ufoPath, "glyphs"))
glyphSet.rebuildContents()  # ignore existing contents.plist, rebuild from dir listing
for name in glyphSet.keys():
	g = glyphSet[name]
	g.drawPoints(None)  # force all attrs to be loaded
	def drawPoints(pen):
		pen = GuessSmoothPointPen(pen)
		g.drawPoints(pen)
	glyphSet.writeGlyph(name, g, drawPoints)

glyphSet.writeContents()  # write out contents.plist

