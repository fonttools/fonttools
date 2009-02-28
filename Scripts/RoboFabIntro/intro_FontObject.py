#FLM: RoboFab Intro, The Font Object

#
#
#	demo of the RoboFab font object
#
#

import robofab

# Let's talk to some of the font objects.
# CurrentFont and CurrentGlyph are similar to
# the RoboFog functions. They return a font
# or Glyph object respectively. It will be the
# front most font or the front most glyph.
from robofab.world import CurrentFont, CurrentGlyph

# This is a brief intro into Robofabs all singing and
# dancing dialog class. It will produce simple
# dialogs in almost any environment, FontLab, Python IDE, W.
from robofab.interface.all.dialogs import Message

# (make sure you have a font opened in FontLab)

f = CurrentFont()
# so now f is the name of a font object for the current font.

if f == None:
	# let's see what dialog can do, a warning
	Message("You should open a font first, there's nothing to look at now!")
else:
	# and another dialog.
	Message("The current font is %s"%(f.info.postscriptFullName))

	# let's have a look at some of the attributes a RoboFab Font object has
	print "the number of glyphs:", len(f)
	
	# some of the attributes map straight to the FontLab Font class
	# We just straightened the camelCase here and there
	print "full name of this font:", f.info.postscriptFullName
	print "list of glyph names:", f.keys()
	print 'ascender:', f.info.ascender
	print 'descender:', f.info.descender
