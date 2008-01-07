# robothon 06
# set guidelines on the average x, y of all selected points
# in the current glyph.
# useful for working on symetric glyphs.

from robofab.world import CurrentGlyph 

g = CurrentGlyph()

# remove all old guides first
g.clearHGuides()
g.clearVGuides()

# this is where we'll be storing some data
guides = {}
average = {}

# iterate through the points, find the selected points
# and their associated off-curve points.
for c in g:
	for pt in c.bPoints:
			if pt.selected:
					average[(pt.anchor[0], pt.anchor[1])] = 1
					guides[(pt.anchor[0], pt.anchor[1])] = 1
					guides[(pt.anchor[0]+pt.bcpIn[0], pt.anchor[1]+pt.bcpIn[1])] = 1
					guides[(pt.anchor[0]+pt.bcpOut[0], pt.anchor[1]+pt.bcpOut[1])] = 1
					
# calculate an average position
x = None
y = None
for (px, py) in average.keys():
	if x is None:
		x = px
	else:
		x += px
	if y is None:
		y = py
	else:
		y += py


# if we found values, set some guides
if len(average.keys()) > 0:	
	ax = float(x) / len(average.keys())
	ay = float(y) / len(average.keys())

	# first, guides for the average
	# attention: a vertical guide has a horizontal value
	g.appendVGuide(ax)
	# attention: a horizontal guide has a vertical value
	g.appendHGuide(ay)
	
	# then some guides for the off-curves
	if len(guides.keys()) > 0:
		for gx, gy in guides.keys():
			g.appendVGuide(gx)
			g.appendHGuide(gy)
		
	g.update()
	
else:
	print "no points selected"
	g.update()
