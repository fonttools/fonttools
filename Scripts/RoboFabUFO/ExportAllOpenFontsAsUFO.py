#FLM: Export glyphs, features from all open fonts to UFO

"""
	Export all open fonts as UFO
	Iterate through all open fonts, and export UFOs.
	
	Note:
	This script will look for a UFO named <vbf_name_without_extension>.ufo.
	If it can't find this UFO, it will make a new one.
	If it can find the UFO, it will only export:
		glyphs
		feature data
		font.lib
		alignment zones (if the installed robofab supports them)

	Kerning and kerning groups are NOT exported. This is to make it
	easier to edit the glyphs in FontLab, but edit the kerning in the UFO,
	with (for instance) MetricsMachine.
	
	This script is useful for workflows which edit in FontLab,
	but take interpolation, metrics and OTF compilation outside.
	
	When running, the script will first save and close all open fonts.
	Then it will open the vfb's one by one, and export, then close.
	Finally it will open all fonts again.

"""

from robofab.world import AllFonts, OpenFont
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
from robofab.glifLib import GlyphSet
from robofab.objects.objectsFL import RGlyph
from robofab.ufoLib import makeUFOPath, UFOWriter
from robofab.interface.all.dialogs import ProgressBar

try:
	from robofab.objects.objectsFL import PostScriptFontHintValues, postScriptHintDataLibKey
	supportHints = True
except ImportError:
	supportHints = False

import os


paths = []
for f in AllFonts():
	paths.append(f.path)
	f.close()
	
for p in paths:
	ufoPath = p.replace(".vfb", ".ufo")
	if os.path.exists(ufoPath):
		# the ufo exists, only export the glyphs and the features
		print "There is a UFO for this font already, exporting glyphs."
		path = os.path.join(os.path.dirname(ufoPath), os.path.basename(ufoPath), "glyphs")
		f = OpenFont(p)
		
		fl.CallCommand(fl_cmd.FontSortByCodepage)

		gs = GlyphSet(path, glyphNameToFileNameFunc=glyphNameToShortFileName)
		for g in f:
			print "saving glyph %s in %s"%(g.name, path)
			gs.writeGlyph(g.name, g, g.drawPoints)
		gs.writeContents()

		# make a new writer
		u = UFOWriter(ufoPath)
		# font info
		print "exporting font info.."
		u.writeInfo(f.info)
		
		# features
		print "exporting features.."
		glyphOrder = []
		for nakedGlyph in f.naked().glyphs:
			glyph = RGlyph(nakedGlyph)
			glyphOrder.append(glyph.name)
		assert None not in glyphOrder, glyphOrder
		# We make a shallow copy if lib, since we add some stuff for export
		# that doesn't need to be retained in memory.
		fontLib = dict(f.lib)
		
		if supportHints:
			psh = PostScriptFontHintValues(f)
			d = psh.asDict()
			fontLib[postScriptHintDataLibKey] = d

		fontLib["org.robofab.glyphOrder"] = glyphOrder
		f._writeOpenTypeFeaturesToLib(fontLib)
		print "fontLib", fontLib
		u.writeLib(fontLib)
		f.close()

	else:
		print "Making a new UFO at", ufoPath
		f = OpenFont(p)
		f.writeUFO()
		f.close()

for p in paths:
	OpenFont(p)

