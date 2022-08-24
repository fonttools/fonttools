"""GlyphSets returned by a TTFont."""

from fontTools.misc.fixedTools import otRound
from copy import copy

class _TTGlyphSet(object):

	"""Generic dict-like GlyphSet class that pulls metrics from hmtx and
	glyph shape from TrueType or CFF.
	"""

	def __init__(self, ttFont, glyphs, glyphType):
		"""Construct a new glyphset.

		Args:
			font (TTFont): The font object (used to get metrics).
			glyphs (dict): A dictionary mapping glyph names to ``_TTGlyph`` objects.
			glyphType (class): Either ``_TTGlyphCFF`` or ``_TTGlyphGlyf``.
		"""
		self._glyphs = glyphs
		self._hmtx = ttFont['hmtx']
		self._vmtx = ttFont['vmtx'] if 'vmtx' in ttFont else None
		self._glyphType = glyphType

	def keys(self):
		return list(self._glyphs.keys())

	def has_key(self, glyphName):
		return glyphName in self._glyphs

	__contains__ = has_key

	def __getitem__(self, glyphName):
		horizontalMetrics = self._hmtx[glyphName]
		verticalMetrics = self._vmtx[glyphName] if self._vmtx else None
		return self._glyphType(
			self, self._glyphs[glyphName], horizontalMetrics, verticalMetrics)

	def __len__(self):
		return len(self._glyphs)

	def get(self, glyphName, default=None):
		try:
			return self[glyphName]
		except KeyError:
			return default

class _TTGlyph(object):

	"""Wrapper for a TrueType glyph that supports the Pen protocol, meaning
	that it has .draw() and .drawPoints() methods that take a pen object as
	their only argument. Additionally there are 'width' and 'lsb' attributes,
	read from the 'hmtx' table.

	If the font contains a 'vmtx' table, there will also be 'height' and 'tsb'
	attributes.
	"""

	def __init__(self, glyphset, glyph, horizontalMetrics, verticalMetrics=None):
		"""Construct a new _TTGlyph.

		Args:
			glyphset (_TTGlyphSet): A glyphset object used to resolve components.
			glyph (ttLib.tables._g_l_y_f.Glyph): The glyph object.
			horizontalMetrics (int, int): The glyph's width and left sidebearing.
		"""
		self._glyphset = glyphset
		self._glyph = glyph
		self.width, self.lsb = horizontalMetrics
		if verticalMetrics:
			self.height, self.tsb = verticalMetrics
		else:
			self.height, self.tsb = None, None

	def draw(self, pen):
		"""Draw the glyph onto ``pen``. See fontTools.pens.basePen for details
		how that works.
		"""
		self._glyph.draw(pen)

	def drawPoints(self, pen):
		from fontTools.pens.pointPen import SegmentToPointPen
		self.draw(SegmentToPointPen(pen))

class _TTGlyphCFF(_TTGlyph):
	pass

class _TTGlyphGlyf(_TTGlyph):

	def draw(self, pen):
		"""Draw the glyph onto Pen. See fontTools.pens.basePen for details
		how that works.
		"""
		glyfTable = self._glyphset._glyphs
		glyph = self._glyph
		offset = self.lsb - glyph.xMin if hasattr(glyph, "xMin") else 0
		glyph.draw(pen, glyfTable, offset)

	def drawPoints(self, pen):
		"""Draw the glyph onto PointPen. See fontTools.pens.pointPen
		for details how that works.
		"""
		glyfTable = self._glyphset._glyphs
		glyph = self._glyph
		offset = self.lsb - glyph.xMin if hasattr(glyph, "xMin") else 0
		glyph.drawPoints(pen, glyfTable, offset)



class _TTVarGlyphSet(_TTGlyphSet):

	def __init__(self, font, location, normalized=False):
		self._ttFont = font
		self._glyphs = font['glyf']

		if not normalized:
			from fontTools.varLib.models import normalizeLocation, piecewiseLinearMap

			axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font['fvar'].axes}
			location = normalizeLocation(location, axes)
			if 'avar' in font:
				avar = font['avar']
				avarSegments = avar.segments
				new_location = {}
				for axis_tag, value in location.items():
					avarMapping = avarSegments.get(axis_tag, None)
					if avarMapping is not None:
						value = piecewiseLinearMap(value, avarMapping)
					new_location[axis_tag] = value
				location = new_location
				del new_location

		self.location = location

	def __getitem__(self, glyphName):
		if glyphName not in self._glyphs:
			raise KeyError(glyphName)
		return _TTVarGlyphGlyf(self._ttFont, glyphName, self.location)


def _setCoordinates(glyph, coord, glyfTable):
	# Handle phantom points for (left, right, top, bottom) positions.
	assert len(coord) >= 4
	if not hasattr(glyph, 'xMin'):
		glyph.recalcBounds(glyfTable)
	leftSideX = coord[-4][0]
	rightSideX = coord[-3][0]
	topSideY = coord[-2][1]
	bottomSideY = coord[-1][1]

	for _ in range(4):
		del coord[-1]

	if glyph.isComposite():
		assert len(coord) == len(glyph.components)
		for p,comp in zip(coord, glyph.components):
			if hasattr(comp, 'x'):
				comp.x,comp.y = p
	elif glyph.numberOfContours == 0:
		assert len(coord) == 0
	else:
		assert len(coord) == len(glyph.coordinates)
		glyph.coordinates = coord

	glyph.recalcBounds(glyfTable)

	horizontalAdvanceWidth = otRound(rightSideX - leftSideX)
	verticalAdvanceWidth = otRound(topSideY - bottomSideY)
	leftSideBearing = otRound(glyph.xMin - leftSideX)
	topSideBearing = otRound(topSideY - glyph.yMax)
	return (
		horizontalAdvanceWidth,
		leftSideBearing,
		verticalAdvanceWidth,
		topSideBearing,
	)


class _TTVarGlyph(_TTGlyph):
	def __init__(self, ttFont, glyphName, location):
		self._ttFont = ttFont
		self._glyphName = glyphName
		self._location = location
		# draw() fills these in
		self.width = self.height = self.lsb = self.tsb = None


class _TTVarGlyphGlyf(_TTVarGlyph):

	def draw(self, pen):
		from fontTools.varLib.iup import iup_delta
		from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
		from fontTools.varLib.models import supportScalar

		glyf = self._ttFont['glyf']
		hMetrics = self._ttFont['hmtx'].metrics
		vMetrics = getattr(self._ttFont.get('vmtx'), 'metrics', None)

		variations = self._ttFont['gvar'].variations[self._glyphName]
		coordinates, _ = glyf._getCoordinatesAndControls(self._glyphName, hMetrics, vMetrics)
		origCoords, endPts = None, None
		for var in variations:
			scalar = supportScalar(self._location, var.axes)
			if not scalar:
				continue
			delta = var.coordinates
			if None in delta:
				if origCoords is None:
					origCoords,control = glyf._getCoordinatesAndControls(self._glyphName, hMetrics, vMetrics)
					endPts = control[1] if control[0] >= 1 else list(range(len(control[1])))
				delta = iup_delta(delta, origCoords, endPts)
			coordinates += GlyphCoordinates(delta) * scalar

		glyph = copy(glyf[self._glyphName]) # Shallow copy
		width, lsb, height, tsb = _setCoordinates(glyph, coordinates, glyf)
		self.width = width
		self.lsb = lsb
		self.height = height
		self.tsb = tsb
		offset = lsb - glyph.xMin if hasattr(glyph, "xMin") else 0
		glyph.draw(pen, glyf, offset)
