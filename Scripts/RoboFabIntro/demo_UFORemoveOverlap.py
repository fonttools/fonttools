#FLM: UFO Remove Overlap

"""
Remove overlap on all glyphs in a .ufo font.

This script sis more than a little silly, but it
demonstrates how objectsRF and objectsFL can
work hand in hand.
"""

from robofab.objects.objectsRF import OpenFont
from robofab.objects.objectsFL import NewFont
from robofab.interface.all.dialogs import ProgressBar

ufoFont = OpenFont(note="Select a .ufo")
if ufoFont:
	bar = ProgressBar('Removing Overlap...', len(ufoFont))
	flFont = NewFont()
	flGlyph = flFont.newGlyph('OverlapRemover')
	for ufoGlyph in ufoFont:
		flPen = flGlyph.getPointPen()
		ufoGlyph.drawPoints(flPen)
		flGlyph.removeOverlap()
		ufoPen = ufoGlyph.getPointPen()
		ufoGlyph.clear()
		flGlyph.drawPoints(ufoPen)
		flGlyph.clear()
		bar.tick()
	flFont.close(save=0)
	bar.close()
	ufoFont.save(doProgress=True)
