# robofab manual
# 	Point object
#	usage examples

contour = CurrentGlyph()[0]
print contour.points[0]

from random import randint
for p in contour.points:
	p.x += randint(-10,10)
	p.y += randint(-10,10)
c.update()
    