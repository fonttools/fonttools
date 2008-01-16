#FLM: RoboFab Intro, Simple Drawing

#
#
#	demo of drawing with RoboFab
#
#

import robofab
from robofab.world import CurrentFont, CurrentGlyph

# (make sure you have a font opened in FontLab)



f = CurrentFont()
if f == None:
	Message("You should open a font first, there's nothing to look at now!")
else:
	newGlyph = f.newGlyph('demoDrawGlyph', clear=True)
	newGlyph.width = 1000

	# The drawing is done through a specialised pen object.
	# There are pen objects for different purposes, this one
	# will draw in a FontLab glyph. The point of this is that
	# Robofab glyphs all respond to the standard set of 
	# pen methods, and it is a simple way to re-interpret the 
	# glyph data. 
	
	# Make a new pen with the new glyph we just made
	pen = newGlyph.getPen()
	
	# Tell the pen to draw things
	pen.moveTo((100, 100))
	pen.lineTo((800, 100))
	pen.curveTo((1000, 300), (1000, 600), (800, 800))
	pen.lineTo((100, 800))
	pen.lineTo((100, 100))
	
	# Done drawing: close the path
	pen.closePath()
	
	# Robofab objects still need to tell FontLab to update.
	newGlyph.update()
	f.update()

	# go check the font, it should now contain a new glyph named
	# "demoDrawGlyph" and it should look like a square.
