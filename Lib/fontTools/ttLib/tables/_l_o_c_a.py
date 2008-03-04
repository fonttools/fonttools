import sys
import DefaultTable
import array
import numpy
from fontTools import ttLib
import struct

class table__l_o_c_a(DefaultTable.DefaultTable):
	
	dependencies = ['glyf']
	
	def decompile(self, data, ttFont):
		longFormat = ttFont['head'].indexToLocFormat
		if longFormat:
			format = "i"
		else:
			format = "H"
		locations = array.array(format)
		locations.fromstring(data)
		if sys.byteorder <> "big":
			locations.byteswap()
		locations = numpy.array(locations, numpy.int32)
		if not longFormat:
			locations = locations * 2
		if len(locations) < (ttFont['maxp'].numGlyphs + 1):
			raise  ttLib.TTLibError, "corrupt 'loca' table, or wrong numGlyphs in 'maxp': %d %d" % (len(locations) - 1, ttFont['maxp'].numGlyphs)
		self.locations = locations[:ttFont['maxp'].numGlyphs + 1]
	
	def compile(self, ttFont):
		locations = self.locations
		if max(locations) < 0x20000:
			locations = locations / 2
			locations = locations.astype(numpy.int16)
			ttFont['head'].indexToLocFormat = 0
		else:
			ttFont['head'].indexToLocFormat = 1
		if sys.byteorder <> "big":
			locations = locations.byteswap()
		return locations.tostring()
	
	def set(self, locations):
		self.locations = numpy.array(locations, numpy.int32)
	
	def toXML(self, writer, ttFont):
		writer.comment("The 'loca' table will be calculated by the compiler")
		writer.newline()
	
	def __getitem__(self, index):
		return self.locations[index]
	
	def __len__(self):
		return len(self.locations)
	
	def __cmp__(self, other):
		return cmp(len(self), len(other)) or not numpy.alltrue(numpy.equal(self.locations, other.locations))

