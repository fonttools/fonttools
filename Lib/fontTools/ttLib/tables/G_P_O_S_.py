import otCommon


class table_G_P_O_S_(otCommon.base_GPOS_GSUB):
	
	def getLookupTypeClass(self, lookupType):
		return lookupTypeClasses[lookupType]


class SinglePos:
	
	def decompile(self, reader, otFont):
		self.format = reader.readUShort()
		if self.format == 1:
			self.decompileFormat1(reader, otFont)
		elif self.format == 2:
			self.decompileFormat2(reader, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown SinglePos format: %d" % self.format
	
	def decompileFormat1(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		valueFactory = ValueRecordFactory(reader.readUShort())
		self.coverage = coverage.getGlyphNames()
		self.value = valueFactory.readValueRecord(reader, otFont)
	
	def decompileFormat2(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		valueFactory = ValueRecordFactory(reader.readUShort())
		valueCount = reader.readUShort()
		glyphNames = coverage.getGlyphNames()
		self.pos = pos = {}
		for i in range(valueCount):
			pos[glyphNames[i]] = valueFactory.readValueRecord(reader, otFont)
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()
			
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


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
			set = reader.readTable(PairSet, otFont, valueFactory1, valueFactory2)
			pairs[firstGlyphName] = set.getValues()
	
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
				value1 = valueFactory1.readValueRecord(reader, otFont)
				value2 = valueFactory2.readValueRecord(reader, otFont)
				if value1 or value2:
					row[j] = (value1, value2)
			if row:
				pairs[i] = row
	
	def compile(self, writer, otFont):
		if self.format == 1:
			self.compileFormat1(writer, otFont)
		elif self.format == 2:
			self.compileFormat2(writer, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown PairPos format: %d" % self.format
	
	def compileFormat1(self, writer, otFont):
		pairs = self.pairs
		glyphNames = pairs.keys()
		coverage = otCommon.CoverageTable()
		glyphNames = coverage.setGlyphNames(glyphNames, otFont)
		writer.writeTable(coverage, otFont)
		# dumb approach: just take the first pair and grab the value.
		dummy, sample1, sample2 = pairs[pairs.keys()[0]][0]
		valueFormat1 = valueFormat2 = 0
		if sample1:
			valueFormat1 = sample1.getFormat()
		if sample2:
			valueFormat2 = sample2.getFormat()
		writer.writeUShort(valueFormat1)
		writer.writeUShort(valueFormat2)
		
		valueFactory1 = ValueRecordFactory(valueFormat1)
		valueFactory2 = ValueRecordFactory(valueFormat2)
		
		writer.writeUShort(len(pairs))
		for glyphName in glyphNames:
			set = PairSet(valueFactory1, valueFactory2)
			set.setValues(pairs[glyphName])
			writer.writeTable(set, otFont)
	
	def compileFormat2(self, writer, otFont):
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
				xmlWriter.begintag("Pair", pair=firstGlyph+","+secondGlyph)
				if value1:
					value1.toXML(xmlWriter, otFont)
				else:
					xmlWriter.simpletag("Value")
				if value2:
					value2.toXML(xmlWriter, otFont)
				#else:  # the second value can be omitted
				#	xmlWriter.simpletag("Value")
				xmlWriter.endtag("Pair")
				xmlWriter.newline()
	
	def toXMLFormat2(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


class PairSet:
	
	def __init__(self, valueFactory1=None, valueFactory2=None):
		self.valueFactory1 = valueFactory1
		self.valueFactory2 = valueFactory2
	
	def getValues(self):
		return self.values
	
	def setValues(self, values):
		self.values = values
	
	def decompile(self, reader, otFont):
		pairValueCount = reader.readUShort()
		self.values = values = []
		for j in range(pairValueCount):
			secondGlyphID = reader.readUShort()
			secondGlyphName = otFont.getGlyphName(secondGlyphID)
			value1 = self.valueFactory1.readValueRecord(reader, otFont)
			value2 = self.valueFactory2.readValueRecord(reader, otFont)
			values.append((secondGlyphName, value1, value2))
	
	def compile(self, writer, otFont):
		values = self.values
		writer.writeUShort(len(values))
		for secondGlyphName, value1, value2 in values:
			writer.writeUShort(otFont.getGlyphID(secondGlyphName))
			self.valueFactory1.writeValuerecord(value1, writer, otFont)
			self.valueFactory2.writeValuerecord(value2, writer, otFont)
			

#
# ------------------
#

class CursivePos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


class MarkBasePos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


class MarkLigPos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


class MarkMarkPos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


class ContextPos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


class ChainContextPos:
	
	def decompile(self, reader, otFont):
		xxx
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
		xmlWriter.newline()


valueRecordFormat = [
#	Mask	 Name		     isDevice  struct format char
	(0x0001, "XPlacement",   0,        "h"),
	(0x0002, "YPlacement",   0,        "h"),
	(0x0004, "XAdvance",     0,        "h"),
	(0x0008, "YAdvance",     0,        "h"),
	(0x0010, "XPlaDevice",   1,        "H"),
	(0x0020, "YPlaDevice",   1,        "H"),
	(0x0040, "XAdvDevice",   1,        "H"),
	(0x0080, "YAdvDevice",   1,        "H"),
# 	reserved:
	(0x0100, "Reserved1",    0,        "H"),
	(0x0200, "Reserved2",    0,        "H"),
	(0x0400, "Reserved3",    0,        "H"),
	(0x0800, "Reserved4",    0,        "H"),
	(0x1000, "Reserved5",    0,        "H"),
	(0x2000, "Reserved6",    0,        "H"),
	(0x4000, "Reserved7",    0,        "H"),
	(0x8000, "Reserved8",    0,        "H"),
]

valueRecordFormatDict = {}
for mask, name, isDevice, format in valueRecordFormat:
	valueRecordFormatDict[name] = mask, isDevice, format


class ValueRecordFactory:
	
	def __init__(self, valueFormat):
		format = ">"
		names = []
		for mask, name, isDevice, formatChar in valueRecordFormat:
			if valueFormat & mask:
				names.append((name, isDevice))
				format = format + formatChar
		self.names, self.format = names, format
		self.size = 2 * len(names)
	
	def readValueRecord(self, reader, otFont):
		names = self.names
		if not names:
			return None
		values = reader.readStruct(self.format, self.size)
		values = map(int, values)
		valueRecord = ValueRecord()
		items = map(None, names, values)
		for (name, isDevice), value in items:
			if isDevice:
				if value:
					device = otCommon.DeviceTable()
					device.decompile(reader.getSubString(value), otFont)
				else:
					device = None
				setattr(valueRecord, name, device)
			else:
				setattr(valueRecord, name, value)
		return valueRecord
	
	def writeValuerecord(self, valueRecord, writer, otFont):
		values = []
		for (name, isDevice) in self.names:
			if isDevice:
				raise NotImplementedError
			else:
				values.append(valueRecord.__dict__.get(name, 0))
		writer.writeStruct(self.format, tuple(values))


class ValueRecord:
	# see ValueRecordFactory
	
	def getFormat(self):
		format = 0
		for name in self.__dict__.keys():
			format = format | valueRecordFormatDict[name][0]
		return format
	
	def toXML(self, xmlWriter, otFont):
		simpleItems = []
		for mask, name, isDevice, format in valueRecordFormat[:4]:  # "simple" values
			if hasattr(self, name):
				simpleItems.append((name, getattr(self, name)))
		deviceItems = []
		for mask, name, isDevice, format in valueRecordFormat[4:8]:  # device records
			if hasattr(self, name):
				deviceItems.append((name, getattr(self, name)))
		if deviceItems:
			xmlWriter.begintag("Value", simpleItems)
			xmlWriter.newline()
			for name, deviceRecord in deviceItems:
				xxx
			xmlWriter.endtag("Value")
		else:
			xmlWriter.simpletag("Value", simpleItems)
	
	def __repr__(self):
		return "<ValueRecord>"


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

