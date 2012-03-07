from fontTools.pens.basePen import AbstractPen, BasePen
from robofab.misc.bezierTools import splitLine, splitCubic


from sets import Set

class MarginPen(BasePen):

	"""
		Pen to calculate the margins at a given height or width.

			- isHorizontal = True: slice the glyph at y=value.
			- isHorizontal = False: slice the glyph at x=value.
		
		>>> f = CurrentFont()
		>>> g = CurrentGlyph()
		>>> pen = MarginPen(f, 200, isHorizontal=True)
		>>> g.draw(pen)
		>>> print pen.getMargins()
		(75.7881, 181.9713)

		>>> pen = MarginPen(f, 200, isHorizontal=False)
		>>> g.draw(pen)
		>>> print pen.getMargins()
		(26.385, 397.4469)
		>>> print pen.getAll()
		[75.7881, 181.9713]

		>>> pen = MarginPen(f, 200, isHorizontal=False)
		>>> g.draw(pen)
		>>> print pen.getMargins()
		(26.385, 397.4469)
		>>> print pen.getAll()
		[26.385, 171.6137, 268.0, 397.4469]
				
		Possible optimisation:
		Initialise the pen object with a list of points we want to measure,
		then draw the glyph once, but do the splitLine() math for all measure points.
		
	"""

	def __init__(self, glyphSet, value, isHorizontal=True):
		BasePen.__init__(self, glyphSet)
		self.value = value
		self.hits = {}
		self.filterDoubles = True
		self.contourIndex = None
		self.startPt = None
		self.isHorizontal = isHorizontal
		
	def _moveTo(self, pt):
		self.currentPt = pt
		self.startPt = pt
		if self.contourIndex is None:
			self.contourIndex = 0
		else:
			self.contourIndex += 1

	def _lineTo(self, pt):
		if self.filterDoubles:
			if pt == self.currentPt:
				return
		hits = splitLine(self.currentPt, pt, self.value, self.isHorizontal)
		if len(hits)>1:
			# result will be 2 tuples of 2 coordinates
			# first two points: start to intersect
			# second two points: intersect to end
			# so, second point in first tuple is the intersect
			# then, the first coordinate of that point is the x.
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] = []
			if self.isHorizontal:
				self.hits[self.contourIndex].append(round(hits[0][-1][0], 4))
			else:
				self.hits[self.contourIndex].append(round(hits[0][-1][1], 4))
		if self.isHorizontal and pt[1] == self.value:
			# it could happen
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] =	[]
			self.hits[self.contourIndex].append(pt[0])
		elif (not self.isHorizontal) and (pt[0] == self.value):
			# it could happen
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] =	[]
			self.hits[self.contourIndex].append(pt[1])
		self.currentPt = pt

	def _curveToOne(self, pt1, pt2, pt3):
		hits = splitCubic(self.currentPt, pt1, pt2, pt3, self.value, self.isHorizontal)
		for i in range(len(hits)-1):
			# a number of intersections is possible. Just take the 
			# last point of each segment.
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] = []
			if self.isHorizontal:
				self.hits[self.contourIndex].append(round(hits[i][-1][0], 4))
			else:
				self.hits[self.contourIndex].append(round(hits[i][-1][1], 4))
		if self.isHorizontal and pt3[1] == self.value:
			# it could happen
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] = []
			self.hits[self.contourIndex].append(pt3[0])
		if (not self.isHorizontal) and (pt3[0] == self.value):
			# it could happen
			if not self.contourIndex in self.hits:
				self.hits[self.contourIndex] = []
			self.hits[self.contourIndex].append(pt3[1])
		self.currentPt = pt3
		
	def _closePath(self):
		if self.currentPt != self.startPt:
			self._lineTo(self.startPt)
		self.currentPt = self.startPt = None
	
	def _endPath(self):
		self.currentPt = None

	def addComponent(self, baseGlyph, transformation):
		if self.glyphSet is None:
			return
		if baseGlyph in self.glyphSet:
			glyph = self.glyphSet[baseGlyph]
		if glyph is not None:
			glyph.draw(self)
		
	def getMargins(self):
		"""Return the extremes of the slice for all contours combined, i.e. the whole glyph."""
		allHits = []
		for index, pts in self.hits.items():
			allHits.extend(pts)
		if allHits:
			return min(allHits), max(allHits)
		return None
		
	def getContourMargins(self):
		"""Return the extremes of the slice for each contour."""
		allHits = {}
		for index, pts in self.hits.items():
			unique = list(Set(pts))
			unique.sort()
			allHits[index] = unique
		return allHits
		
	def getAll(self):
		"""Return all the slices."""
		allHits = []
		for index, pts in self.hits.items():
			allHits.extend(pts)
		unique = list(Set(allHits))
		unique = list(unique)
		unique.sort()
		return unique
		
		
if __name__ == "__main__":

	def makeTestGlyph():
		# make a simple glyph that we can test the pens with.
		from robofab.objects.objectsRF import RGlyph
		testGlyph = RGlyph()
		testGlyph.name = "testGlyph"
		testGlyph.width = 1000
		pen = testGlyph.getPen()
		pen.moveTo((100, 100))
		pen.lineTo((900, 100))
		pen.lineTo((900, 800))
		pen.lineTo((100, 800))
		# a curve
		pen.curveTo((120, 700), (120, 300), (100, 100))
		pen.closePath()
		return testGlyph
		
	def controlBoundsPenTest():
		testGlyph = makeTestGlyph()
		glyphSet = {}
		value = 200
		isHorizontal = True
		testPen = MarginPen(glyphSet, value, isHorizontal)
		testGlyph.draw(testPen)
		assert testPen.getAll() == [107.5475, 200.0, 300.0]
		
	controlBoundsPenTest()