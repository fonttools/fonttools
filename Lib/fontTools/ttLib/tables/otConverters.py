from types import TupleType
from fontTools.misc.textTools import safeEval


def buildConverters(tableSpec, tableNamespace):
	"""Given a table spec from otData.py, build a converter object for each
	field of the table. This is called for each table in otData.py, and
	the results are assigned to the corresponding class in otTables.py."""
	converters = []
	convertersByName = {}
	for tp, name, repeat, repeatOffset, descr in tableSpec:
		if name.startswith("ValueFormat"):
			assert tp == "uint16"
			converterClass = ValueFormat
		elif name.endswith("Count"):
			assert tp == "uint16"
			converterClass = Count
		elif name == "SubTable":
			converterClass = SubTable
		elif name == "ExtSubTable":
			converterClass = ExtSubTable
		else:
			converterClass = converterMapping[tp]
		tableClass = tableNamespace.get(name)
		conv = converterClass(name, repeat, repeatOffset, tableClass)
		if name in ["SubTable", "ExtSubTable"]:
			conv.lookupTypes = tableNamespace['lookupTypes']
			# also create reverse mapping
			for t in conv.lookupTypes.values():
				for cls in t.values():
					convertersByName[cls.__name__] = Table(name, repeat, repeatOffset, cls)
		converters.append(conv)
		assert not convertersByName.has_key(name)
		convertersByName[name] = conv
	return converters, convertersByName


class BaseConverter:
	
	"""Base class for converter objects. Apart from the constructor, this
	is an abstract class."""
	
	def __init__(self, name, repeat, repeatOffset, tableClass):
		self.name = name
		self.repeat = repeat
		self.repeatOffset = repeatOffset
		self.tableClass = tableClass
		self.isCount = name.endswith("Count")
		self.isPropagatedCount = name in ["ClassCount", "Class2Count"]
	
	def read(self, reader, font, tableDict):
		"""Read a value from the reader."""
		raise NotImplementedError, self
	
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		"""Write a value to the writer."""
		raise NotImplementedError, self
	
	def xmlRead(self, attrs, content, font):
		"""Read a value from XML."""
		raise NotImplementedError, self
	
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		"""Write a value to XML."""
		raise NotImplementedError, self


class SimpleValue(BaseConverter):
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		xmlWriter.simpletag(name, attrs + [("value", value)])
		xmlWriter.newline()
	def xmlRead(self, attrs, content, font):
		return attrs["value"]

class IntValue(SimpleValue):
	def xmlRead(self, attrs, content, font):
		return int(attrs["value"], 0)

class Long(IntValue):
	def read(self, reader, font, tableDict):
		return reader.readLong()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeLong(value)

class Version(BaseConverter):
	def read(self, reader, font, tableDict):
		value = reader.readLong()
		assert (value >> 16) == 1, "Unsupported version 0x%08x" % value
		return float(value) / 0x10000
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		if value < 0x10000:
			value *= 0x10000
		value = int(round(value))
		assert (value >> 16) == 1, "Unsupported version 0x%08x" % value
		writer.writeLong(value)
	def xmlRead(self, attrs, content, font):
		value = attrs["value"]
		value = float(int(value, 0)) if value.startswith("0") else float(value)
		if value >= 0x10000:
			value = float(value) / 0x10000
		return value
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value >= 0x10000:
			value = float(value) / 0x10000
		if value % 1 != 0:
			# Write as hex
			value = "0x%08x" % (int(round(value * 0x10000)))
		xmlWriter.simpletag(name, attrs + [("value", value)])
		xmlWriter.newline()

class Short(IntValue):
	def read(self, reader, font, tableDict):
		return reader.readShort()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeShort(value)

class UShort(IntValue):
	def read(self, reader, font, tableDict):
		return reader.readUShort()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUShort(value)

class Count(Short):
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		xmlWriter.comment("%s=%s" % (name, value))
		xmlWriter.newline()

class Tag(SimpleValue):
	def read(self, reader, font, tableDict):
		return reader.readTag()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeTag(value)

class GlyphID(SimpleValue):
	def read(self, reader, font, tableDict):
		value = reader.readUShort()
		value =  font.getGlyphName(value)
		return value

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		value =  font.getGlyphID(value)
		writer.writeUShort(value)


class Struct(BaseConverter):
	
	def read(self, reader, font, tableDict):
		table = self.tableClass()
		table.decompile(reader, font)
		return table
	
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		value.compile(writer, font)
	
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value is None:
			pass  # NULL table, ignore
		else:
			value.toXML(xmlWriter, font, attrs)
	
	def xmlRead(self, attrs, content, font):
		table = self.tableClass()
		Format = attrs.get("Format")
		if Format is not None:
			table.Format = int(Format)
		for element in content:
			if type(element) == TupleType:
				name, attrs, content = element
				table.fromXML((name, attrs, content), font)
			else:
				pass
		return table


class Table(Struct):
	
	def read(self, reader, font, tableDict, lazy=True):
		offset = reader.readUShort()
		if offset == 0:
			return None
		if offset <= 3:
			# XXX hack to work around buggy pala.ttf
			print "*** Warning: offset is not 0, yet suspiciously low (%s). table: %s" \
					% (offset, self.tableClass.__name__)
			return None
		subReader = reader.getSubReader(offset)
		table = self.tableClass()
		if lazy:
			table.reader = subReader
			table.font = font
			table.compileStatus = 1
		else:
			table.decompile(subReader, font)
		return table
	
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		if value is None:
			writer.writeUShort(0)
		else:
			subWriter = writer.getSubWriter()
			subWriter.name = self.name
			if repeatIndex is not None:
				subWriter.repeatIndex = repeatIndex
			value.preCompile()
			writer.writeSubTable(subWriter)
			value.compile(subWriter, font)

class SubTable(Table):
	def getConverter(self, tableType, lookupType):
		lookupTypes = self.lookupTypes[tableType]
		tableClass = lookupTypes[lookupType]
		return SubTable(self.name, self.repeat, self.repeatOffset, tableClass)


class ExtSubTable(Table):
	def getConverter(self, tableType, lookupType):
		lookupTypes = self.lookupTypes[tableType]
		tableClass = lookupTypes[lookupType]
		return ExtSubTable(self.name, self.repeat, self.repeatOffset, tableClass)
	
	def read(self, reader, font, tableDict, lazy=True):
		offset = reader.readULong()
		if offset == 0:
			return None
		subReader = reader.getSubReader(offset)
		table = self.tableClass()
		table.start = subReader.offset
		if lazy:
			table.reader = subReader
			table.font = font
			table.compileStatus = 1
		else:
			table.decompile(subReader, font)
		return table
	
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.Extension = 1 # actually, mere presence of the field flags it as an Ext Subtable writer.
		if value is None:
			writer.writeULong(0)
		else:
			subWriter = writer.getSubWriter()
			subWriter.name = self.name
			writer.writeSubTable(subWriter)
			# If the subtable has been sorted and we can just write the original
			# data, then do so.
			if value.compileStatus == 3:
				data = value.reader.data[value.start:value.end]
				subWriter.writeData(data)
			else:
				value.compile(subWriter, font)


class ValueFormat(IntValue):
	def __init__(self, name, repeat, repeatOffset, tableClass):
		BaseConverter.__init__(self, name, repeat, repeatOffset, tableClass)
		self.which = name[-1] == "2"
	def read(self, reader, font, tableDict):
		format = reader.readUShort()
		reader.setValueFormat(format, self.which)
		return format
	def write(self, writer, font, tableDict, format, repeatIndex=None):
		writer.writeUShort(format)
		writer.setValueFormat(format, self.which)


class ValueRecord(ValueFormat):
	def read(self, reader, font, tableDict):
		return reader.readValueRecord(font, self.which)
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeValueRecord(value, font, self.which)
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value is None:
			pass  # NULL table, ignore
		else:
			value.toXML(xmlWriter, font, self.name, attrs)
	def xmlRead(self, attrs, content, font):
		from otBase import ValueRecord
		value = ValueRecord()
		value.fromXML((None, attrs, content), font)
		return value


class DeltaValue(BaseConverter):
	
	def read(self, reader, font, tableDict):
		StartSize = tableDict["StartSize"]
		EndSize = tableDict["EndSize"]
		DeltaFormat = tableDict["DeltaFormat"]
		assert DeltaFormat in (1, 2, 3), "illegal DeltaFormat"
		nItems = EndSize - StartSize + 1
		nBits = 1 << DeltaFormat
		minusOffset = 1 << nBits
		mask = (1 << nBits) - 1
		signMask = 1 << (nBits - 1)
		
		DeltaValue = []
		tmp, shift = 0, 0
		for i in range(nItems):
			if shift == 0:
				tmp, shift = reader.readUShort(), 16
			shift = shift - nBits
			value = (tmp >> shift) & mask
			if value & signMask:
				value = value - minusOffset
			DeltaValue.append(value)
		return DeltaValue
	
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		StartSize = tableDict["StartSize"]
		EndSize = tableDict["EndSize"]
		DeltaFormat = tableDict["DeltaFormat"]
		DeltaValue = value
		assert DeltaFormat in (1, 2, 3), "illegal DeltaFormat"
		nItems = EndSize - StartSize + 1
		nBits = 1 << DeltaFormat
		assert len(DeltaValue) == nItems
		mask = (1 << nBits) - 1
		
		tmp, shift = 0, 16
		for value in DeltaValue:
			shift = shift - nBits
			tmp = tmp | ((value & mask) << shift)
			if shift == 0:
				writer.writeUShort(tmp)
				tmp, shift = 0, 16
		if shift <> 16:
			writer.writeUShort(tmp)
	
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		# XXX this could do with a nicer format
		xmlWriter.simpletag(name, attrs + [("value", value)])
		xmlWriter.newline()
	
	def xmlRead(self, attrs, content, font):
		return safeEval(attrs["value"])


converterMapping = {
	# type         class
	"int16":       Short,
	"uint16":      UShort,
	"Version":     Version,
	"Tag":         Tag,
	"GlyphID":     GlyphID,
	"struct":      Struct,
	"Offset":      Table,
	"LOffset":     ExtSubTable,
	"ValueRecord": ValueRecord,
	"DeltaValue":  DeltaValue,
}

