import sys
import DefaultTable
import array
from fontTools import ttLib
from fontTools.misc.textTools import safeEval


class table_T_S_I__5(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		numGlyphs = ttFont['maxp'].numGlyphs
		assert len(data) == 2 * numGlyphs
		a = array.array("H")
		a.fromstring(data)
		if sys.byteorder <> "big":
			a.byteswap()
		self.glyphGrouping = {}
		for i in range(numGlyphs):
			self.glyphGrouping[ttFont.getGlyphName(i)] = a[i]
	
	def compile(self, ttFont):
		glyphNames = ttFont.getGlyphOrder()
		a = array.array("H")
		for i in range(len(glyphNames)):
			a.append(self.glyphGrouping[glyphNames[i]])
		if sys.byteorder <> "big":
			a.byteswap()
		return a.tostring()
	
	def toXML(self, writer, ttFont):
		names = self.glyphGrouping.keys()
		names.sort()
		for glyphName in names:
			writer.simpletag("glyphgroup", name=glyphName, value=self.glyphGrouping[glyphName])
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if not hasattr(self, "glyphGrouping"):
			self.glyphGrouping = {}
		if name <> "glyphgroup":
			return
		self.glyphGrouping[attrs["name"]] = safeEval(attrs["value"])

