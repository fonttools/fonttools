#FLM: RoboFab Intro, Contours, Segments and Points

#
#
#	demo of RoboFab contour, segments and points
#
#

# In RoboFab, glyphs are constructed mainly from a list
# of contours. These contours are constructed from lists
# of segments, which are construted from a list of points.
# Kind of makes sense, doesn't it? This demo will briefly
# run through printing some info about the contours in
# a glyph and it will show how to do a few things to contours.
# You should really check out the documentation for a complete
# list of everything that can be done with and to contours,
# segments and points. There are far too many things to list
# in this intro. Ok. Here we go!

from robofab.world import CurrentGlyph

# (you will need t have a font open in FontLab for this demo)
glyph = CurrentGlyph()

# Before we get into changing any of these objects,
# let's print a little info about them.

print "This glyph has %s contours"%len(glyph.contours)
# a glyph has a list of contours
for contour in glyph.contours:
	# every contour has an index,
	print "-contour index %s"%contour.index
	# a direction,
	print "--clockwise: %s"%contour.clockwise
	# and a list of segments
	print "--%s segments"%len(contour.segments)
	for segment in contour.segments:
		# every segment has an index,
		print "---segment %s"%segment.index
		# a type,
		print "---type: %s"%segment.type
		# a list of points,
		print "---%s points"%len(segment.points)
		# which includes one on curve point,
		onCurve = segment.onCurve
		print "---onCurve point at: (%s, %s)"%(onCurve.x, onCurve.y)
		# and possibly some off curve points
		print "---%s offCurve points"%len(segment.offCurve)

# Now, contours, segments and points all have
# unique methods of their own, but for now let's
# just look at contour methods.

for contour in glyph.contours:
	# you can move the contour
	contour.move((314, 159))
	# you can scale the contour
	# and you can even set the center
	# of the scale
	contour.scale((2, .5), center=(100, 100))
	# you can reverse the direction
	contour.reverseContour()
	# and there are many more!

# as always, update the glyph
glyph.update()

