#FLM: Print Measurments

"""print the distance and angle between two selected points"""

from robofab.world import CurrentGlyph
import math

glyph = CurrentGlyph()

selectedPoints = []

for contour in glyph.contours:
	if contour.selected:
		for segment in contour.segments:
			if segment.selected:
				onCurve = segment.onCurve
				point = (onCurve.x, onCurve.y)
				if point not in selectedPoints:
					selectedPoints.append(point)

if len(selectedPoints) == 2:
	xList = [x for x, y in selectedPoints]
	yList = [y for x, y in selectedPoints]
	xList.sort()
	yList.sort()
	xDiff = xList[1] - xList[0]
	yDiff = yList[1] - yList[0]
	ang = round(math.atan2(yDiff, xDiff)*180/math.pi, 3)
	print "x:%s y:%s a:%s"%(xDiff, yDiff, ang)
