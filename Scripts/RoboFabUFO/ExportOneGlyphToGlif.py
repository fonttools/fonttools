#FLM: Glyph to Glif, not in UFO

"""
Dump the selected glyph to a Glif as a seperate, individual file.
This is not saved through a GlyphSet and any contents.plist in the
same directory will not be updated. If that's what you need use
DumpOneGlyphToUFO.py

"""


from robofab.glifLib import writeGlyphToString
from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import PutFile
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
import os

f = CurrentFont()
g = CurrentGlyph()

if g is not None:
	todo = [g.name]
else:
	todo = f.selection

for c in todo:
	g = f[c]
	result = True
	data = writeGlyphToString(g.name, g, g.drawPoints)
	filename = glyphNameToShortFileName(g.name, None)
	file = PutFile("Save this glif as:")
	if file is not None:
		path = os.path.join(os.path.dirname(file), filename)
		print "saving to", path
		f = open(path, "w")
		f.write(data)
		f.close()
		

print 'done'