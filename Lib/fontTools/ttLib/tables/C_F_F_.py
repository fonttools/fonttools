import DefaultTable
from fontTools import cffLib


# temporary switch:
# - if true use possibly incomplete compile/decompile/toXML/fromXML implementation
# - if false use DefaultTable, ie. dump as hex.
TESTING_CFF = 0


class table_C_F_F_(DefaultTable.DefaultTable):
	
	def __init__(self, tag):
		DefaultTable.DefaultTable.__init__(self, tag)
		self.cff = cffLib.CFFFontSet()
		self._gaveGlyphOrder = 0
	
	def decompile(self, data, otFont):
		from cStringIO import StringIO
		self.data = data  # XXX while work is in progress...
		self.cff.decompile(StringIO(data))
		assert len(self.cff) == 1, "can't deal with multi-font CFF tables."
	
	#def compile(self, otFont):
	#	xxx
	
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
		if TESTING_CFF:
			self.cff.toXML(writer, progress)
		else:
			# dump as hex as long as we can't compile
			DefaultTable.DefaultTable.toXML(self, writer, otFont)
	
	#def fromXML(self, (name, attrs, content), otFont):
	#	xxx

