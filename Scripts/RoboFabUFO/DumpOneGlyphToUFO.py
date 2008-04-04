#FLM: Export Selected Glyph to UFO


"""Dump the selected glyph to a .glif as part of a UFO.
It saves the .glif through a GlyphSet and updates the contents.plist.
"""


from robofab.glifLib import GlyphSet
from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import Message, GetFolder
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
import os


if os.name == "mac":
	LOCAL_ENCODING = "macroman"
else:
	LOCAL_ENCODING = "latin-1"


f = CurrentFont()
g = CurrentGlyph()

if g is not None:
	todo = [g.name]
else:
	todo = f.selection
for c in todo:
	if f is None:
		continue
	g = f[c]
	result = True
	file = GetFolder("Select a UFO to save the GLIF in:")
	if file is None:
		continue
	if file.find(".ufo") == -1:
		Message("You need to select an UFO. Quitting.")
	else:
		path = os.path.join(os.path.dirname(file), os.path.basename(file), "glyphs")
		print "saving glyph %s in %s"%(g.name.encode(LOCAL_ENCODING), path)
		gs = GlyphSet(path, glyphNameToFileNameFunc=glyphNameToShortFileName)
		gs.writeGlyph(g.name, g, g.drawPoints)
		gs.writeContents()

print 'done'