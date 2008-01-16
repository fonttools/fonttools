#FLM: RoboFab Intro, The Glyph Object

#
#
#	demo of the RoboFab glyph object
#
#

import robofab
from robofab.world import CurrentFont, CurrentGlyph
from robofab.interface.all.dialogs import Message

# (make sure you have a font opened in FontLab)



# this code starts out the same as intro_FontObject
f = CurrentFont()
if f == None:
	Message("You should open a font first, there's nothing to look at now!")
else:
	for g in f:
		print "glyphname:", g.name, ", glyph width:", g.width
		# so now g is a RoboFab Glyph object
		print "this glyph has %d contours" % len(g.contours)
		print "this glyph has %d components" % len(g.components)
		print "this glyph has %d anchors" % len(g.anchors)
		print

# easy huh?
# There are many more attributes and methods.
# Most of these can be used to edit the font data.
# Which makes them not suited for a simple intro as this
# because we don't want to mess up your font.