# robothon06
# iterate through points

from robofab.world import CurrentFont

font = CurrentFont()
glyph = font['A']
for p in glyph[0].points:
	print p.x, p.y, p.type
