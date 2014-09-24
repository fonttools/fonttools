from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from . import DefaultTable
import sys
import array
import warnings

class table__l_o_c_a(DefaultTable.DefaultTable):
	
	dependencies = ['glyf']
	
	def decompile(self, data, ttFont):
		longFormat = ttFont['head'].indexToLocFormat
		if longFormat:
			format = "I"
		else:
			format = "H"
		locations = array.array(format)
		locations.fromstring(data)
		if sys.byteorder != "big":
			locations.byteswap()
		if not longFormat:
			l = array.array("I")
			for i in range(len(locations)):
				l.append(locations[i] * 2)
			locations = l
		if len(locations) < (ttFont['maxp'].numGlyphs + 1):
			warnings.warn("corrupt 'loca' table, or wrong numGlyphs in 'maxp': %d %d" % (len(locations) - 1, ttFont['maxp'].numGlyphs))
		self.locations = locations
	
	def compile(self, ttFont):
		try:
			max_location = max(self.locations)
		except AttributeError:
			self.set([])
			max_location = 0
		if max_location < 0x20000:
			locations = array.array("H")
			for i in range(len(self.locations)):
				locations.append(self.locations[i] // 2)
			ttFont['head'].indexToLocFormat = 0
		else:
			locations = array.array("I", self.locations)
			ttFont['head'].indexToLocFormat = 1
		if sys.byteorder != "big":
			locations.byteswap()
		return locations.tostring()
	
	def set(self, locations):
		self.locations = array.array("I", locations)
	
	def toXML(self, writer, ttFont):
		writer.comment("The 'loca' table will be calculated by the compiler")
		writer.newline()
	
	def __getitem__(self, index):
		return self.locations[index]
	
	def __len__(self):
		return len(self.locations)

