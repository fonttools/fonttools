from ufoLib.pointPen import AbstractPointPen

class DigestPointPen(AbstractPointPen):

	"""This calculates a tuple representing the structure and values in a glyph:

		- including coordinates
		- including components

	>>> from robofab.pens.digestPen import DigestPointPen
	>>> pen = DigestPointPen()
	>>> g = CurrentGlyph()
	>>> g.drawPoints(pen)
	>>> pen.getDigest()
	('beginPath', ((25, 425), 'line', False, None),((25, 0), 'line', False, None),((95, 0), 'line', False, None),((95, 425), 'line', False, None), 'endPath',
	 'beginPath', ((25, 595), 'line', False, None),((25, 491), 'line', False, None),((95, 491), 'line', False, None),((95, 595), 'line', False, None), 'endPath')
	
	"""

	def __init__(self, ignoreSmoothAndName=False):
		self._data = []
		self.ignoreSmoothAndName = ignoreSmoothAndName

	def beginPath(self):
		self._data.append('beginPath')

	def endPath(self):
		self._data.append('endPath')

	def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
		if self.ignoreSmoothAndName:
			self._data.append((pt, segmentType))
		else:
			self._data.append((pt, segmentType, smooth, name))

	def addComponent(self, baseGlyphName, transformation):
		t = []
		for v in transformation:
			if int(v) == v:
				t.append(int(v))
			else:
				t.append(v)
		self._data.append((baseGlyphName, tuple(t)))

	def getDigest(self):
		"""Return the digest as a tuple with all coordinates of all points."""
		return tuple(self._data)
	
	def getDigestPointsOnly(self, needSort=True):
		""" Return the digest as a tuple with all coordinates of all points, 
				- but without smooth info or drawing instructions.
				- For instance if you want to compare 2 glyphs in shape,
				  but not interpolatability.
			"""
		points = []
		from types import TupleType
		for item in self._data:
			if type(item) == TupleType:
				points.append(item[0])
		if needSort:
			points.sort()
		return tuple(points)


class DigestPointStructurePen(DigestPointPen):

	"""This calculates a tuple representing the structure and values in a glyph:

		- excluding coordinates
		- excluding components

	>>> from robofab.pens.digestPen import DigestPointStructurePen
	>>> pen = DigestPointStructurePen()
	>>> g = CurrentGlyph()
	>>> g.drawPoints(pen)
	>>> pen.getDigest()
	 ('beginPath', 'line', 'line', 'line', 'line', 'endPath', 'beginPath', 'line', 'line', 'line', 'line', 'endPath')
	
	"""

	def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
		self._data.append(segmentType)

	def addComponent(self, baseGlyphName, transformation):
		self._data.append(baseGlyphName)

