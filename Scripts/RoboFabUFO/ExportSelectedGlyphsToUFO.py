#FLM: Export selected glyphs to UFO


"""
	Dump the selected glyph to a .glif as part of a UFO.
	It saves the .glif through a GlyphSet and updates the contents.plist.
	
	EvB 08
"""


from robofab.glifLib import GlyphSet
from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import Message, GetFolder
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
import os

f = CurrentFont()
g = CurrentGlyph()

f.save()

ufoPath = None
ufoPath = f.path.replace(".vfb", ".ufo")
if not os.path.exists(ufoPath):
	ufoPath = GetFolder("Select a UFO to save the GLIF in:")
	if ufoPath.find(".ufo") == -1:
		Message("You need to select an UFO. Quitting.")
		ufoPath = None

if ufoPath is not None:
	todo = f.selection
	print "selection", todo
	if g is not None:
		todo.append(g.name)
	for c in todo:
		g = f[c]
		path = os.path.join(os.path.dirname(ufoPath), os.path.basename(ufoPath), "glyphs")
		print "saving glyph %s in %s"%(g.name, path)
		gs = GlyphSet(path, glyphNameToFileNameFunc=glyphNameToShortFileName)
		gs.writeGlyph(g.name, g, g.drawPoints)
		gs.writeContents()

print 'done'