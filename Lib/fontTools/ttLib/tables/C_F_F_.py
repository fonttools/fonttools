import DefaultTable
from fontTools import cffLib


class table_C_F_F_(DefaultTable.DefaultTable):
	
	def __init__(self, tag):
		DefaultTable.DefaultTable.__init__(self, tag)
		self.cff = cffLib.CFFFontSet()
		self._gaveGlyphOrder = 0
	
	def decompile(self, data, otFont):
		from cStringIO import StringIO
		self.cff.decompile(StringIO(data), otFont)
		assert len(self.cff) == 1, "can't deal with multi-font CFF tables."
	
	def compile(self, otFont):
		from cStringIO import StringIO
		f = StringIO()
		self.cff.compile(f, otFont)
		return f.getvalue()
	
	def haveGlyphNames(self):
		if hasattr(self.cff[self.cff.fontNames[0]], "ROS"):
			return 0  # CID-keyed font
		else:
			return 1
	
	def getGlyphOrder(self):
		if self._gaveGlyphOrder:
			from fontTools import ttLib
			raise ttLib.TTLibError, "illegal use of getGlyphOrder()"
		self._gaveGlyphOrder = 1
		return self.cff[self.cff.fontNames[0]].getGlyphOrder()
	
	def setGlyphOrder(self, glyphOrder):
		pass
		# XXX
		#self.cff[self.cff.fontNames[0]].setGlyphOrder(glyphOrder)
	
	def toXML(self, writer, otFont, progress=None):
		self.cff.toXML(writer, progress)
	
	def fromXML(self, (name, attrs, content), otFont):
		if not hasattr(self, "cff"):
			self.cff = cffLib.CFFFontSet()
		self.cff.fromXML((name, attrs, content))

