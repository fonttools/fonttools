
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
		# drawPoints is only implemented for _TTGlyphGlyf at this time.
		raise NotImplementedError()

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


