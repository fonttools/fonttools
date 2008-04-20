#FLM: Selected glyphs from all fonts to UFO


"""
	Get the name of the current glyph,
	then for each open font, export that glyph to UFO.	
	It saves the .glif through a GlyphSet and updates the contents.plist.
	
	This script is useful when you're working on several interpolation
	masters as separate vfb source files.
	
	EvB 08	
"""


from robofab.glifLib import GlyphSet
from robofab.world import CurrentFont, CurrentGlyph, AllFonts
from robofab.interface.all.dialogs import Message, GetFolder
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
import os

f = CurrentFont()
g = CurrentGlyph()

f.save()

todo = f.selection
print "selection", todo
if g is not None:
	todo.append(g.name)
		
for f in AllFonts():
	ufoPath = None
	print "f.path", f, f.path
	if f.path is None:
		# huh, in case there is a ghost font.
		print "skipping", f
		continue
	ufoPath = f.path.replace(".vfb", ".ufo")
	if not os.path.exists(ufoPath):
		ufoPath = GetFolder("Select a UFO to save the GLIF in:")
		if ufoPath.find(".ufo") == -1:
			Message("You need to select an UFO. Quitting.")
			ufoPath = None
	if ufoPath is None:
		continue
	for c in todo:
		if c not in f:
			print "font is missing", c
			continue
		g = f[c]
		path = os.path.join(os.path.dirname(ufoPath), os.path.basename(ufoPath), "glyphs")
		print "saving glyph %s in %s"%(g.name, path)
		gs = GlyphSet(path, glyphNameToFileNameFunc=glyphNameToShortFileName)
		gs.writeGlyph(g.name, g, g.drawPoints)
		gs.writeContents()

print 'done'