import DefaultTable
from fontTools import cffLib


class table_C_F_F_(DefaultTable.DefaultTable, cffLib.CFFFontSet):
	
	def __init__(self, tag):
		DefaultTable.DefaultTable.__init__(self, tag)
		cffLib.CFFFontSet.__init__(self)
		self._gaveGlyphOrder = 0
	
	def decompile(self, data, otFont):
		self.data = data  # XXX while work is in progress...
		cffLib.CFFFontSet.decompile(self, data)
		assert len(self.fonts) == 1, "can't deal with multi-font CFF tables."
	
	#def compile(self, otFont):
	#	xxx
	
	def getGlyphOrder(self):
		if self._gaveGlyphOrder:
			from fontTools import ttLib
			raise ttLib.TTLibError, "illegal use of getGlyphOrder()"
		self._gaveGlyphOrder = 1
		return self.fonts[self.fontNames[0]].getGlyphOrder()
	
	def setGlyphOrder(self, glyphOrder):
		self.fonts[self.fontNames[0]].setGlyphOrder(glyphOrder)
	
	def toXML(self, writer, otFont, progress=None):
		cffLib.CFFFontSet.toXML(self, writer, progress)
	
	#def fromXML(self, (name, attrs, content), otFont):
	#	xxx

