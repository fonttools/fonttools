import DefaultTable
import struct
from fontTools.ttLib import sfnt
from fontTools.misc.textTools import safeEval, readHex


class table__k_e_r_n(DefaultTable.DefaultTable):
	
	def getkern(self, format):
		for subtable in self.kernTables:
			if subtable.version == format:
				return subtable
		return None  # not found
	
	def decompile(self, data, ttFont):
		version, nTables = struct.unpack(">HH", data[:4])
		if version == 1:
			# Apple's new format. Hm.
			version, nTables = struct.unpack(">ll", data[:8])
			self.version = version / float(0x10000)
			data = data[8:]
		else:
			self.version = version
			data = data[4:]
		tablesIndex = []
		self.kernTables = []
		for i in range(nTables):
			version, length = struct.unpack(">HH", data[:4])
			length = int(length)
			if not kern_classes.has_key(version):
				subtable = KernTable_format_unkown()
			else:
				subtable = kern_classes[version]()
			subtable.decompile(data[:length], ttFont)
			self.kernTables.append(subtable)
			data = data[length:]
	
	def compile(self, ttFont):
		nTables = len(self.kernTables)
		if self.version == 1.0:
			# Apple's new format.
			data = struct.pack(">ll", self.version * 0x1000, nTables)
		else:
			data = struct.pack(">HH", self.version, nTables)
		for subtable in self.kernTables:
			data = data + subtable.compile(ttFont)
		return data
	
	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		for subtable in self.kernTables:
			subtable.toXML(writer, ttFont)
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name == "version":
			self.version = safeEval(attrs["value"])
			return
		if name <> "kernsubtable":
			return
		if not hasattr(self, "kernTables"):
			self.kernTables = []
		format = safeEval(attrs["format"])
		if not kern_classes.has_key(format):
			subtable = KernTable_format_unkown()
		else:
			subtable = kern_classes[format]()
		self.kernTables.append(subtable)
		subtable.fromXML((name, attrs, content), ttFont)


class KernTable_format_0:
	
	def decompile(self, data, ttFont):
		version, length, coverage = struct.unpack(">HHH", data[:6])
		self.version, self.coverage = int(version), int(coverage)
		data = data[6:]
		
		self.kernTable = kernTable = {}
		
		nPairs, searchRange, entrySelector, rangeShift = struct.unpack(">HHHH", data[:8])
		data = data[8:]
		
		for k in range(nPairs):
			left, right, value = struct.unpack(">HHh", data[:6])
			data = data[6:]
			left, right = int(left), int(right)
			kernTable[(ttFont.getGlyphName(left), ttFont.getGlyphName(right))] = value
		assert len(data) == 0
	
	def compile(self, ttFont):
		nPairs = len(self.kernTable)
		entrySelector = sfnt.maxpoweroftwo(nPairs)
		searchRange = (2 ** entrySelector) * 6
		rangeShift = (nPairs - (2 ** entrySelector)) * 6
		data = struct.pack(">HHHH", nPairs, searchRange, entrySelector, rangeShift)
		
		# yeehee! (I mean, turn names into indices)
		kernTable = map(lambda ((left, right), value), getGlyphID=ttFont.getGlyphID:
					(getGlyphID(left), getGlyphID(right), value), 
				self.kernTable.items())
		kernTable.sort()
		for left, right, value in kernTable:
			data = data + struct.pack(">HHh", left, right, value)
		return struct.pack(">HHH", self.version, len(data) + 6, self.coverage) + data
	
	def toXML(self, writer, ttFont):
		writer.begintag("kernsubtable", coverage=self.coverage, format=0)
		writer.newline()
		items = self.kernTable.items()
		items.sort()
		for (left, right), value in items:
			writer.simpletag("pair", [
					("l", left),
					("r", right),
					("v", value)
					])
			writer.newline()
		writer.endtag("kernsubtable")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.coverage = safeEval(attrs["coverage"])
		self.version = safeEval(attrs["format"])
		if not hasattr(self, "kernTable"):
			self.kernTable = {}
		for element in content:
			if type(element) <> type(()):
				continue
			name, attrs, content = element
			self.kernTable[(attrs["l"], attrs["r"])] = safeEval(attrs["v"])
	
	def __getitem__(self, pair):
		return self.kernTable[pair]
	
	def __setitem__(self, pair, value):
		self.kernTable[pair] = value
	
	def __delitem__(self, pair):
		del self.kernTable[pair]
	
	def __cmp__(self, other):
		return cmp(self.__dict__, other.__dict__)


class KernTable_format_2:
	
	def decompile(self, data, ttFont):
		self.data = data
	
	def compile(self, ttFont, ttFont):
		return data
	
	def toXML(self, writer):
		writer.begintag("kernsubtable", format=2)
		writer.newline()
		writer.dumphex(self.data)
		writer.endtag("kernsubtable")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.decompile(readHex(content))


class KernTable_format_unkown:
	
	def decompile(self, data, ttFont):
		self.data = data
	
	def compile(self, ttFont):
		return data
	
	def toXML(self, writer, ttFont):
		writer.begintag("kernsubtable", format="-1")
		writer.newline()
		writer.comment("unknown 'kern' subtable format")
		writer.dumphex(self.data)
		writer.endtag("kernsubtable")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.decompile(readHex(content))



kern_classes = {0: KernTable_format_0, 1: KernTable_format_2}
