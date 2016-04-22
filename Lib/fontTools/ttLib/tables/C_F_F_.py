from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import cffLib
from . import DefaultTable


class table_C_F_F_(DefaultTable.DefaultTable):

	def __init__(self, tag=None):
		DefaultTable.DefaultTable.__init__(self, tag)
		self.cff = cffLib.CFFFontSet()
		self._gaveGlyphOrder = False

	def decompile(self, data, otFont):
		self.cff.decompile(BytesIO(data), otFont)
		assert len(self.cff) == 1, "can't deal with multi-font CFF tables."

	def compile(self, otFont):
		f = BytesIO()
		self.cff.compile(f, otFont)
		return f.getvalue()

	def haveGlyphNames(self):
		if hasattr(self.cff[self.cff.fontNames[0]], "ROS"):
			return False  # CID-keyed font
		else:
			return True

	def getGlyphOrder(self):
		if self._gaveGlyphOrder:
			from fontTools import ttLib
			raise ttLib.TTLibError("illegal use of getGlyphOrder()")
		self._gaveGlyphOrder = True
		return self.cff[self.cff.fontNames[0]].getGlyphOrder()

	def setGlyphOrder(self, glyphOrder):
		pass
		# XXX
		#self.cff[self.cff.fontNames[0]].setGlyphOrder(glyphOrder)

	def toXML(self, writer, otFont, progress=None):
		self.cff.toXML(writer, progress)

	def fromXML(self, name, attrs, content, otFont):
		if not hasattr(self, "cff"):
			self.cff = cffLib.CFFFontSet()
		self.cff.fromXML(name, attrs, content)
