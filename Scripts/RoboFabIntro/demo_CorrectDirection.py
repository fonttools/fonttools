"""Correct contour direction for all glyphs in the font"""

from robofab.world import OpenFont
from robofab.interface.all.dialogs import ProgressBar

font = OpenFont()
bar = ProgressBar('Correcting contour direction...', len(font))
for glyph in font:
	bar.label(glyph.name)
	glyph.correctDirection()
	glyph.update()
	bar.tick()
font.update()
bar.close()