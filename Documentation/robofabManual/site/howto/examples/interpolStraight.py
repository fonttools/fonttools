# robofab manual
# 	Interpolate howto
#	Straight Interpolating examples


from robofab.world import OpenFont
minFont = OpenFont(pathToMinFont)
maxFont = OpenFont(pathToMaxFont)
# or any other way you like to get two font objects

inbetweenFont = OpenFont(pathToInbetweenFont)
# so now we have 3 font objects, right?

inbetweenFont.interpolate(.5, minFont, maxFont)
# presto, inbetweenFont is now 50% of one and 50% of the other

inbetweenFont.interpolate((.92, .12), minFont, maxFont)
# presto, inbetweenFont is now horizontally
# vertically interpolated in different ways.
