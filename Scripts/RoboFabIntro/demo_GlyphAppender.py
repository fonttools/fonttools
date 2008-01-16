#FLM: Glyph Appender

"""Add a glyph to the current glyph"""

from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import SelectGlyph

glyph = CurrentGlyph()
font = CurrentFont()

# select a glyph to add
selected = SelectGlyph(font)
# make sure that we are not trying add the current glyph to itself
if selected.name != glyph.name:
	# preserve the current state
	fl.SetUndo()
	# add the selected glyph to the current glyph
	glyph.appendGlyph(selected)
	# always update the glyph!
	glyph.update()
	# and, just to be safe, update the font... 
	font.update()
