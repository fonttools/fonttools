#FLM: Single Glyph from a UFO

"""Import one glyph from a .ufo, 
	i.e. a single .glif file.
"""

from robofab.world import CurrentFont
from robofab.objects.objectsRF import OpenFont
from robofab.interface.all.dialogs import SelectGlyph, Message

flFont = CurrentFont()
if flFont is None:
	Message("Please have a FontLab destination font ready..")
else:
	# pick a .ufo
	rfFont = OpenFont()
	if rfFont is not None:
		# pick a glyph in the .ufo
		rfGlyph = SelectGlyph(rfFont)
		if rfGlyph is not None:
			# make a new glyph in the FL font
			flGlyph = flFont.newGlyph(rfGlyph.name, clear=True)
			# draw the glyph into the FL font
			pen = flGlyph.getPointPen()
			rfGlyph.drawPoints(pen)
			# set the width, unicodes and lib
			flGlyph.width = rfGlyph.width
			flGlyph.unicodes = rfGlyph.unicodes
			flGlyph.lib = rfGlyph.lib
			flGlyph.note = rfGlyph.note
			flGlyph.update()
			flFont.update()
