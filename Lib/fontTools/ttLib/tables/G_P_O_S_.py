import otCommon


class table_G_P_O_S_(otCommon.base_GPOS_GSUB):
	
	def getLookupTypeClass(self, lookupType):
		return lookupTypeClasses[lookupType]


class SinglePos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()
			
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class PairPos:
	
	def decompile(self, reader, otFont):
		self.format = reader.readUShort()
		if self.format == 1:
			self.decompileFormat1(reader, otFont)
		elif self.format == 2:
			self.decompileFormat2(reader, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown PairPos format: %d" % self.format
	
	def decompileFormat1(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.glyphNames
		valueFactory1 = ValueRecordFactory(reader.readUShort())
		valueFactory2 = ValueRecordFactory(reader.readUShort())
		self.pairs = pairs = {}
		for i in range(reader.readUShort()):
			firstGlyphName = glyphNames[i]
			offset = reader.readOffset()
			setData = reader.getSubString(offset)
			set = PairSet()
			set.decompile(setData, otFont, valueFactory1, valueFactory2)
			pairs[firstGlyphName] = set.values
	
	def decompileFormat2(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.glyphNames
		valueFactory1 = ValueRecordFactory(reader.readUShort())
		valueFactory2 = ValueRecordFactory(reader.readUShort())
		self.classDef1 = reader.readTable(otCommon.ClassDefinitionTable, otFont)
		self.classDef2 = reader.readTable(otCommon.ClassDefinitionTable, otFont)
		class1Count = reader.readUShort()
		class2Count = reader.readUShort()
		self.pairs = pairs = {}  # sparse matrix
		for i in range(class1Count):
			row = {}
			for j in range(class2Count):
				value1 = valueFactory1.getValueRecord(reader)
				value2 = valueFactory2.getValueRecord(reader)
				if value1 or value2:
					row[j] = (value1, value2)
			if row:
				pairs[i] = row
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		if self.format == 1:
			self.toXMLFormat1(xmlWriter, otFont)
		elif self.format == 2:
			self.toXMLFormat2(xmlWriter, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown PairPos format: %d" % self.format
	
	def toXMLFormat1(self, xmlWriter, otFont):
		pairs = self.pairs.items()
		pairs.sort()
		for firstGlyph, secondGlyphs in pairs:
			for secondGlyph, value1, value2 in secondGlyphs:
				#XXXXXXXXX
				xmlWriter.begintag("Pair", first=firstGlyph, second=secondGlyph)
				xmlWriter.newline()
				if value1:
					value1.toXML(xmlWriter, otFont)
				if value2:
					value2.toXML(xmlWriter, otFont)
				xmlWriter.endtag("Pair")
				xmlWriter.newline()
	
	def toXMLFormat2(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class PairSet:
	
	def decompile(self, reader, otFont, valueFactory1, valueFactory2):
		pairValueCount = reader.readUShort()
		self.values = values = []
		for j in range(pairValueCount):
			secondGlyphID = reader.readUShort()
			secondGlyphName = otFont.getGlyphName(secondGlyphID)
			value1 = valueFactory1.getValueRecord(reader)
			value2 = valueFactory2.getValueRecord(reader)
			values.append((secondGlyphName, value1, value2))
	
	def compile(self, otFont):
		xxx

#
# ------------------
#

class CursivePos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class MarkBasePos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class MarkLigPos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class MarkMarkPos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class ContextPos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class ChainContextPos:
	
	def decompile(self, reader, otFont):
		pass
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


lookupTypeClasses = {
	1: SinglePos,
	2: PairPos,
	3: CursivePos,
	4: MarkBasePos,
	5: MarkLigPos,
	6: MarkMarkPos,
	7: ContextPos,
	8: ChainContextPos,
}


valueRecordFormat = [
#	Mask	 Name		     struct format char
	(0x0001, "XPlacement",   "h"),
	(0x0002, "YPlacement",   "h"),
	(0x0004, "XAdvance",     "h"),
	(0x0008, "YAdvance",     "h"),
	(0x0010, "XPlaDevice",   "H"),
	(0x0020, "YPlaDevice",   "H"),
	(0x0040, "XAdvDevice",   "H"),
	(0x0080, "YAdvDevice",   "H"),
# 	reserved:
	(0x0100, "Reserved1",    "H"),
	(0x0200, "Reserved2",    "H"),
	(0x0400, "Reserved3",    "H"),
	(0x0800, "Reserved4",    "H"),
	(0x1000, "Reserved5",    "H"),
	(0x2000, "Reserved6",    "H"),
	(0x4000, "Reserved7",    "H"),
	(0x8000, "Reserved8",    "H"),
]


class ValueRecordFactory:
	
	def __init__(self, valueFormat):
		format = ">"
		names = []
		for mask, name, formatChar in valueRecordFormat:
			if valueFormat & mask:
				names.append(name)
				format = format + formatChar
		self.names, self.format = names, format
		self.size = 2 * len(names)
	
	def getValueRecord(self, reader):
		names = self.names
		if not names:
			return None
		values = reader.readStruct(self.format, self.size)
		values = map(int, values)
		valueRecord = ValueRecord()
		items = map(None, names, values)
		for name, value in items:
			setattr(valueRecord, name, value)
		return valueRecord


class ValueRecord:
	# see ValueRecordFactory
	
	def __nonzero__(self):
		for value in self.__dict__.values():
			if value:
				return 1
		return 0
			
	def toXML(self, xmlWriter, otFont):
		simpleItems = []
		for mask, name, format in valueRecordFormat[:4]:  # "simple" values
			if hasattr(self, name):
				simpleItems.append((name, getattr(self, name)))
		deviceItems = []
		for mask, name, format in valueRecordFormat[4:8]:  # device records
			if hasattr(self, name):
				deviceItems.append((name, getattr(self, name)))
		if deviceItems:
			xmlWriter.begintag("ValueRecord", simpleItems)
			xmlWriter.newline()
			for name, deviceRecord in deviceItems:
				xxx
			xmlWriter.endtag("ValueRecord")
			xmlWriter.newline()
		else:
			xmlWriter.simpletag("ValueRecord", simpleItems)
			xmlWriter.newline()
	
	def __repr__(self):
		return "<ValueRecord>"

