#FLM: Invert Selection

"""Invert the selected segments in the current glyph"""

from robofab.world import CurrentGlyph

glyph = CurrentGlyph()
for contour in glyph.contours:
	notSelected = []
	for segment in contour.segments:
		if not segment.selected:
			notSelected.append(segment.index)
	contour.selected = False
	for index in notSelected:
		contour[index].selected = True
glyph.update()