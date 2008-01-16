#FLM: Kerning Counter

"""print kerning counts for glyphs selected in the font window"""

from robofab.world import CurrentFont

font = CurrentFont()
selectedGlyphs = font.selection
kerning = font.kerning
counts = kerning.occurrenceCount(selectedGlyphs)
for glyphName in selectedGlyphs:
	print "%s: %s pairs"%(glyphName, counts[glyphName])