import DefaultTable
import array
import Numeric
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
		if ttLib.endian <> "big":
			locations.byteswap()
		locations = Numeric.array(locations, Numeric.Int32)
		if not longFormat:
			locations = locations * 2
		if len(locations) <> (ttFont['maxp'].numGlyphs + 1):
			raise  ttLib.TTLibError, "corrupt 'loca' table"
		self.locations = locations
	
	def compile(self, ttFont):
		locations = self.locations
		if max(locations) < 0x20000:
			locations = locations / 2
			locations = locations.astype(Numeric.Int16)
			ttFont['head'].indexToLocFormat = 0
		else:
			ttFont['head'].indexToLocFormat = 1
		if ttLib.endian <> "big":
			locations = locations.byteswapped()
		return locations.tostring()
	
	def set(self, locations):
		self.locations = Numeric.array(locations, Numeric.Int32)
	
	def toXML(self, writer, ttFont):
		writer.comment("The 'loca' table will be calculated by the compiler")
		writer.newline()
	
	def __getitem__(self, index):
		return self.locations[index]
	
	def __len__(self):
		return len(self.locations)
	
	def __cmp__(self, other):
		return cmp(len(self), len(other)) or not Numeric.alltrue(Numeric.equal(self.locations, other.locations))

