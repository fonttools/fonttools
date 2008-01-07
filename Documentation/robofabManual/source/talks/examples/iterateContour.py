# robothon06
# get a specific contour and view it
#through point, segment and bPoint structures

from robofab.world import CurrentFont

font = CurrentFont()
glyph = font['A']
contour = glyph[0]
print contour.points
print countours.segments
print contour.bPoints

