from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from fontTools.misc.fixedTools import fixedToFloat as fi2fl, floatToFixed as fl2fi
from .otBase import ValueRecordFactory
import logging


log = logging.getLogger(__name__)


def buildConverters(tableSpec, tableNamespace):
	"""Given a table spec from otData.py, build a converter object for each
	field of the table. This is called for each table in otData.py, and
	the results are assigned to the corresponding class in otTables.py."""
	converters = []
	convertersByName = {}
	for tp, name, repeat, aux, descr in tableSpec:
		tableName = name
		if name.startswith("ValueFormat"):
			assert tp == "uint16"
			converterClass = ValueFormat
		elif name.endswith("Count") or name.endswith("LookupType"):
			assert tp == "uint16"
			converterClass = ComputedUShort
		elif name == "SubTable":
			converterClass = SubTable
		elif name == "ExtSubTable":
			converterClass = ExtSubTable
		elif name == "FeatureParams":
			converterClass = FeatureParams
		else:
			if not tp in converterMapping:
				tableName = tp
				converterClass = Struct
			else:
				converterClass = converterMapping[tp]
		tableClass = tableNamespace.get(tableName)
		conv = converterClass(name, repeat, aux, tableClass)
		if name in ["SubTable", "ExtSubTable"]:
			conv.lookupTypes = tableNamespace['lookupTypes']
			# also create reverse mapping
			for t in conv.lookupTypes.values():
				for cls in t.values():
					convertersByName[cls.__name__] = Table(name, repeat, aux, cls)
		if name == "FeatureParams":
			conv.featureParamTypes = tableNamespace['featureParamTypes']
			conv.defaultFeatureParams = tableNamespace['FeatureParams']
			for cls in conv.featureParamTypes.values():
				convertersByName[cls.__name__] = Table(name, repeat, aux, cls)
		converters.append(conv)
		assert name not in convertersByName, name
		convertersByName[name] = conv
	return converters, convertersByName


class _MissingItem(tuple):
	__slots__ = ()

try:
	from collections import UserList
except:
	from UserList import UserList

class _LazyList(UserList):

	def __getslice__(self, i, j):
		return self.__getitem__(slice(i, j))
	def __getitem__(self, k):
		if isinstance(k, slice):
			indices = range(*k.indices(len(self)))
			return [self[i] for i in indices]
		item = self.data[k]
		if isinstance(item, _MissingItem):
			self.reader.seek(self.pos + item[0] * self.recordSize)
			item = self.conv.read(self.reader, self.font, {})
			self.data[k] = item
		return item

class BaseConverter(object):

	"""Base class for converter objects. Apart from the constructor, this
	is an abstract class."""

	def __init__(self, name, repeat, aux, tableClass):
		self.name = name
		self.repeat = repeat
		self.aux = aux
		self.tableClass = tableClass
		self.isCount = name.endswith("Count")
		self.isLookupType = name.endswith("LookupType")
		self.isPropagated = name in ["ClassCount", "Class2Count", "FeatureTag", "SettingsCount", "AxisCount"]

	def readArray(self, reader, font, tableDict, count):
		"""Read an array of values from the reader."""
		lazy = font.lazy and count > 8
		if lazy:
			recordSize = self.getRecordSize(reader)
			if recordSize is NotImplemented:
				lazy = False
		if not lazy:
			l = []
			for i in range(count):
				l.append(self.read(reader, font, tableDict))
			return l
		else:
			l = _LazyList()
			l.reader = reader.copy()
			l.pos = l.reader.pos
			l.font = font
			l.conv = self
			l.recordSize = recordSize
			l.extend(_MissingItem([i]) for i in range(count))
			reader.advance(count * recordSize)
			return l

	def getRecordSize(self, reader):
		if hasattr(self, 'staticSize'): return self.staticSize
		return NotImplemented

	def read(self, reader, font, tableDict):
		"""Read a value from the reader."""
		raise NotImplementedError(self)

	def writeArray(self, writer, font, tableDict, values):
		for i, value in enumerate(values):
			self.write(writer, font, tableDict, value, i)

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		"""Write a value to the writer."""
		raise NotImplementedError(self)

	def xmlRead(self, attrs, content, font):
		"""Read a value from XML."""
		raise NotImplementedError(self)

	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		"""Write a value to XML."""
		raise NotImplementedError(self)


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
	staticSize = 4
	def read(self, reader, font, tableDict):
		return reader.readLong()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeLong(value)

class ULong(IntValue):
	staticSize = 4
	def read(self, reader, font, tableDict):
		return reader.readULong()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeULong(value)

class Short(IntValue):
	staticSize = 2
	def read(self, reader, font, tableDict):
		return reader.readShort()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeShort(value)

class UShort(IntValue):
	staticSize = 2
	def read(self, reader, font, tableDict):
		return reader.readUShort()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUShort(value)

class UInt8(IntValue):
	staticSize = 1
	def read(self, reader, font, tableDict):
		return reader.readUInt8()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUInt8(value)

class UInt24(IntValue):
	staticSize = 3
	def read(self, reader, font, tableDict):
		return reader.readUInt24()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUInt24(value)

class ComputedUShort(UShort):
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		xmlWriter.comment("%s=%s" % (name, value))
		xmlWriter.newline()

class Tag(SimpleValue):
	staticSize = 4
	def read(self, reader, font, tableDict):
		return reader.readTag()
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeTag(value)

class GlyphID(SimpleValue):
	staticSize = 2
	def readArray(self, reader, font, tableDict, count):
		glyphOrder = font.getGlyphOrder()
		gids = reader.readUShortArray(count)
		try:
			l = [glyphOrder[gid] for gid in gids]
		except IndexError:
			# Slower, but will not throw an IndexError on an invalid glyph id.
			l = [font.getGlyphName(gid) for gid in gids]
		return l
	def read(self, reader, font, tableDict):
		return font.getGlyphName(reader.readUShort())
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUShort(font.getGlyphID(value))

class FloatValue(SimpleValue):
	def xmlRead(self, attrs, content, font):
		return float(attrs["value"])

class DeciPoints(FloatValue):
	staticSize = 2
	def read(self, reader, font, tableDict):
		return reader.readUShort() / 10

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeUShort(int(round(value * 10)))

class Fixed(FloatValue):
	staticSize = 4
	def read(self, reader, font, tableDict):
		return  fi2fl(reader.readLong(), 16)
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.writeLong(fl2fi(value, 16))

class Version(BaseConverter):
	staticSize = 4
	def read(self, reader, font, tableDict):
		value = reader.readLong()
		assert (value >> 16) == 1, "Unsupported version 0x%08x" % value
		return  fi2fl(value, 16)
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		if value < 0x10000:
			value = fl2fi(value, 16)
		value = int(round(value))
		assert (value >> 16) == 1, "Unsupported version 0x%08x" % value
		writer.writeLong(value)
	def xmlRead(self, attrs, content, font):
		value = attrs["value"]
		value = float(int(value, 0)) if value.startswith("0") else float(value)
		if value >= 0x10000:
			value = fi2fl(value, 16)
		return value
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value >= 0x10000:
			value = fi2fl(value, 16)
		if value % 1 != 0:
			# Write as hex
			value = "0x%08x" % fl2fi(value, 16)
		xmlWriter.simpletag(name, attrs + [("value", value)])
		xmlWriter.newline()


class Struct(BaseConverter):

	def getRecordSize(self, reader):
		return self.tableClass and self.tableClass.getRecordSize(reader)

	def read(self, reader, font, tableDict):
		table = self.tableClass()
		table.decompile(reader, font)
		return table

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		value.compile(writer, font)

	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value is None:
			if attrs:
				# If there are attributes (probably index), then
				# don't drop this even if it's NULL.  It will mess
				# up the array indices of the containing element.
				xmlWriter.simpletag(name, attrs + [("empty", 1)])
				xmlWriter.newline()
			else:
				pass # NULL table, ignore
		else:
			value.toXML(xmlWriter, font, attrs, name=name)

	def xmlRead(self, attrs, content, font):
		if "empty" in attrs and safeEval(attrs["empty"]):
			return None
		table = self.tableClass()
		Format = attrs.get("Format")
		if Format is not None:
			table.Format = int(Format)
		for element in content:
			if isinstance(element, tuple):
				name, attrs, content = element
				table.fromXML(name, attrs, content, font)
			else:
				pass
		# TODO Fill in items that are not set by XML.
		return table

	def __repr__(self):
		return "Struct of " + repr(self.tableClass)


class Table(Struct):

	longOffset = False
	staticSize = 2

	def readOffset(self, reader):
		return reader.readUShort()

	def writeNullOffset(self, writer):
		if self.longOffset:
			writer.writeULong(0)
		else:
			writer.writeUShort(0)

	def read(self, reader, font, tableDict):
		offset = self.readOffset(reader)
		if offset == 0:
			return None
		if offset <= 3:
			# XXX hack to work around buggy pala.ttf
			log.warning("offset is not 0, yet suspiciously low (%d). table: %s",
					offset, self.tableClass.__name__)
			return None
		table = self.tableClass()
		reader = reader.getSubReader(offset)
		if font.lazy:
			table.reader = reader
			table.font = font
		else:
			table.decompile(reader, font)
		return table

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		if value is None:
			self.writeNullOffset(writer)
		else:
			subWriter = writer.getSubWriter()
			subWriter.longOffset = self.longOffset
			subWriter.name = self.name
			if repeatIndex is not None:
				subWriter.repeatIndex = repeatIndex
			writer.writeSubTable(subWriter)
			value.compile(subWriter, font)

class LTable(Table):

	longOffset = True
	staticSize = 4

	def readOffset(self, reader):
		return reader.readULong()


class SubTable(Table):
	def getConverter(self, tableType, lookupType):
		tableClass = self.lookupTypes[tableType][lookupType]
		return self.__class__(self.name, self.repeat, self.aux, tableClass)

	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		Table.xmlWrite(self, xmlWriter, font, value, None, attrs)


class ExtSubTable(LTable, SubTable):

	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer.Extension = True # actually, mere presence of the field flags it as an Ext Subtable writer.
		Table.write(self, writer, font, tableDict, value, repeatIndex)

class FeatureParams(Table):
	def getConverter(self, featureTag):
		tableClass = self.featureParamTypes.get(featureTag, self.defaultFeatureParams)
		return self.__class__(self.name, self.repeat, self.aux, tableClass)


class ValueFormat(IntValue):
	staticSize = 2
	def __init__(self, name, repeat, aux, tableClass):
		BaseConverter.__init__(self, name, repeat, aux, tableClass)
		self.which = "ValueFormat" + ("2" if name[-1] == "2" else "1")
	def read(self, reader, font, tableDict):
		format = reader.readUShort()
		reader[self.which] = ValueRecordFactory(format)
		return format
	def write(self, writer, font, tableDict, format, repeatIndex=None):
		writer.writeUShort(format)
		writer[self.which] = ValueRecordFactory(format)


class ValueRecord(ValueFormat):
	def getRecordSize(self, reader):
		return 2 * len(reader[self.which])
	def read(self, reader, font, tableDict):
		return reader[self.which].readValueRecord(reader, font)
	def write(self, writer, font, tableDict, value, repeatIndex=None):
		writer[self.which].writeValueRecord(writer, font, value)
	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		if value is None:
			pass  # NULL table, ignore
		else:
			value.toXML(xmlWriter, font, self.name, attrs)
	def xmlRead(self, attrs, content, font):
		from .otBase import ValueRecord
		value = ValueRecord()
		value.fromXML(None, attrs, content, font)
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
		if shift != 16:
			writer.writeUShort(tmp)

	def xmlWrite(self, xmlWriter, font, value, name, attrs):
		xmlWriter.simpletag(name, attrs + [("value", value)])
		xmlWriter.newline()

	def xmlRead(self, attrs, content, font):
		return safeEval(attrs["value"])


converterMapping = {
	# type		class
	"int16":	Short,
	"uint8":	UInt8,
	"uint16":	UShort,
	"uint24":	UInt24,
	"uint32":	ULong,
	"Version":	Version,
	"Tag":		Tag,
	"GlyphID":	GlyphID,
	"DeciPoints":	DeciPoints,
	"Fixed":	Fixed,
	"struct":	Struct,
	"Offset":	Table,
	"LOffset":	LTable,
	"ValueRecord":	ValueRecord,
	"DeltaValue":	DeltaValue,
}
