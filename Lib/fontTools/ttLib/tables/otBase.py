from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from .DefaultTable import DefaultTable
import sys
import array
import struct
import logging

log = logging.getLogger(__name__)

class OverflowErrorRecord(object):
	def __init__(self, overflowTuple):
		self.tableType = overflowTuple[0]
		self.LookupListIndex = overflowTuple[1]
		self.SubTableIndex = overflowTuple[2]
		self.itemName = overflowTuple[3]
		self.itemIndex = overflowTuple[4]

	def __repr__(self):
		return str((self.tableType, "LookupIndex:", self.LookupListIndex, "SubTableIndex:", self.SubTableIndex, "ItemName:", self.itemName, "ItemIndex:", self.itemIndex))

class OTLOffsetOverflowError(Exception):
	def __init__(self, overflowErrorRecord):
		self.value = overflowErrorRecord

	def __str__(self):
		return repr(self.value)


class BaseTTXConverter(DefaultTable):

	"""Generic base class for TTX table converters. It functions as an
	adapter between the TTX (ttLib actually) table model and the model
	we use for OpenType tables, which is necessarily subtly different.
	"""

	def decompile(self, data, font):
		from . import otTables
		reader = OTTableReader(data, tableTag=self.tableTag)
		tableClass = getattr(otTables, self.tableTag)
		self.table = tableClass()
		self.table.decompile(reader, font)

	def compile(self, font):
		""" Create a top-level OTTableWriter for the GPOS/GSUB table.
			Call the compile method for the the table
				for each 'converter' record in the table converter list
					call converter's write method for each item in the value.
						- For simple items, the write method adds a string to the
						writer's self.items list.
						- For Struct/Table/Subtable items, it add first adds new writer to the
						to the writer's self.items, then calls the item's compile method.
						This creates a tree of writers, rooted at the GUSB/GPOS writer, with
						each writer representing a table, and the writer.items list containing
						the child data strings and writers.
			call the getAllData method
				call _doneWriting, which removes duplicates
				call _gatherTables. This traverses the tables, adding unique occurences to a flat list of tables
				Traverse the flat list of tables, calling getDataLength on each to update their position
				Traverse the flat list of tables again, calling getData each get the data in the table, now that
				pos's and offset are known.

				If a lookup subtable overflows an offset, we have to start all over.
		"""
		overflowRecord = None

		while True:
			try:
				writer = OTTableWriter(tableTag=self.tableTag)
				self.table.compile(writer, font)
				return writer.getAllData()

			except OTLOffsetOverflowError as e:

				if overflowRecord == e.value:
					raise # Oh well...

				overflowRecord = e.value
				log.info("Attempting to fix OTLOffsetOverflowError %s", e)
				lastItem = overflowRecord

				ok = 0
				if overflowRecord.itemName is None:
					from .otTables import fixLookupOverFlows
					ok = fixLookupOverFlows(font, overflowRecord)
				else:
					from .otTables import fixSubTableOverFlows
					ok = fixSubTableOverFlows(font, overflowRecord)
				if not ok:
					# Try upgrading lookup to Extension and hope
					# that cross-lookup sharing not happening would
					# fix overflow...
					from .otTables import fixLookupOverFlows
					ok = fixLookupOverFlows(font, overflowRecord)
					if not ok:
						raise

	def toXML(self, writer, font):
		self.table.toXML2(writer, font)

	def fromXML(self, name, attrs, content, font):
		from . import otTables
		if not hasattr(self, "table"):
			tableClass = getattr(otTables, self.tableTag)
			self.table = tableClass()
		self.table.fromXML(name, attrs, content, font)
		self.table.populateDefaults()


class OTTableReader(object):

	"""Helper class to retrieve data from an OpenType table."""

	__slots__ = ('data', 'offset', 'pos', 'localState', 'tableTag')

	def __init__(self, data, localState=None, offset=0, tableTag=None):
		self.data = data
		self.offset = offset
		self.pos = offset
		self.localState = localState
		self.tableTag = tableTag

	def advance(self, count):
		self.pos += count

	def seek(self, pos):
		self.pos = pos

	def copy(self):
		other = self.__class__(self.data, self.localState, self.offset, self.tableTag)
		other.pos = self.pos
		return other

	def getSubReader(self, offset):
		offset = self.offset + offset
		return self.__class__(self.data, self.localState, offset, self.tableTag)

	def readUShort(self):
		pos = self.pos
		newpos = pos + 2
		value, = struct.unpack(">H", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readUShortArray(self, count):
		pos = self.pos
		newpos = pos + count * 2
		value = array.array("H", self.data[pos:newpos])
		if sys.byteorder != "big": value.byteswap()
		self.pos = newpos
		return value

	def readInt8(self):
		pos = self.pos
		newpos = pos + 1
		value, = struct.unpack(">b", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readShort(self):
		pos = self.pos
		newpos = pos + 2
		value, = struct.unpack(">h", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readLong(self):
		pos = self.pos
		newpos = pos + 4
		value, = struct.unpack(">l", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readUInt8(self):
		pos = self.pos
		newpos = pos + 1
		value, = struct.unpack(">B", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readUInt24(self):
		pos = self.pos
		newpos = pos + 3
		value, = struct.unpack(">l", b'\0'+self.data[pos:newpos])
		self.pos = newpos
		return value

	def readULong(self):
		pos = self.pos
		newpos = pos + 4
		value, = struct.unpack(">L", self.data[pos:newpos])
		self.pos = newpos
		return value

	def readTag(self):
		pos = self.pos
		newpos = pos + 4
		value = Tag(self.data[pos:newpos])
		assert len(value) == 4, value
		self.pos = newpos
		return value

	def readData(self, count):
		pos = self.pos
		newpos = pos + count
		value = self.data[pos:newpos]
		self.pos = newpos
		return value

	def __setitem__(self, name, value):
		state = self.localState.copy() if self.localState else dict()
		state[name] = value
		self.localState = state

	def __getitem__(self, name):
		return self.localState and self.localState[name]

	def __contains__(self, name):
		return self.localState and name in self.localState


class OTTableWriter(object):

	"""Helper class to gather and assemble data for OpenType tables."""

	def __init__(self, localState=None, tableTag=None):
		self.items = []
		self.pos = None
		self.localState = localState
		self.tableTag = tableTag
		self.longOffset = False
		self.parent = None

	def __setitem__(self, name, value):
		state = self.localState.copy() if self.localState else dict()
		state[name] = value
		self.localState = state

	def __getitem__(self, name):
		return self.localState[name]

	def __delitem__(self, name):
		del self.localState[name]

	# assembler interface

	def getDataLength(self):
		"""Return the length of this table in bytes, without subtables."""
		l = 0
		for item in self.items:
			if hasattr(item, "getCountData"):
				l += item.size
			elif hasattr(item, "getData"):
				l += 4 if item.longOffset else 2
			else:
				l = l + len(item)
		return l

	def getData(self):
		"""Assemble the data for this writer/table, without subtables."""
		items = list(self.items)  # make a shallow copy
		pos = self.pos
		numItems = len(items)
		for i in range(numItems):
			item = items[i]

			if hasattr(item, "getData"):
				if item.longOffset:
					items[i] = packULong(item.pos - pos)
				else:
					try:
						items[i] = packUShort(item.pos - pos)
					except struct.error:
						# provide data to fix overflow problem.
						overflowErrorRecord = self.getOverflowErrorRecord(item)

						raise OTLOffsetOverflowError(overflowErrorRecord)

		return bytesjoin(items)

	def __hash__(self):
		# only works after self._doneWriting() has been called
		return hash(self.items)

	def __ne__(self, other):
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.longOffset == other.longOffset and self.items == other.items

	def _doneWriting(self, internedTables):
		# Convert CountData references to data string items
		# collapse duplicate table references to a unique entry
		# "tables" are OTTableWriter objects.

		# For Extension Lookup types, we can
		# eliminate duplicates only within the tree under the Extension Lookup,
		# as offsets may exceed 64K even between Extension LookupTable subtables.
		isExtension = hasattr(self, "Extension")

		# Certain versions of Uniscribe reject the font if the GSUB/GPOS top-level
		# arrays (ScriptList, FeatureList, LookupList) point to the same, possibly
		# empty, array.  So, we don't share those.
		# See: https://github.com/fonttools/fonttools/issues/518
		dontShare = hasattr(self, 'DontShare')

		if isExtension:
			internedTables = {}

		items = self.items
		for i in range(len(items)):
			item = items[i]
			if hasattr(item, "getCountData"):
				items[i] = item.getCountData()
			elif hasattr(item, "getData"):
				item._doneWriting(internedTables)
				if not dontShare:
					items[i] = item = internedTables.setdefault(item, item)
		self.items = tuple(items)

	def _gatherTables(self, tables, extTables, done):
		# Convert table references in self.items tree to a flat
		# list of tables in depth-first traversal order.
		# "tables" are OTTableWriter objects.
		# We do the traversal in reverse order at each level, in order to
		# resolve duplicate references to be the last reference in the list of tables.
		# For extension lookups, duplicate references can be merged only within the
		# writer tree under the  extension lookup.

		done[id(self)] = True

		numItems = len(self.items)
		iRange = list(range(numItems))
		iRange.reverse()

		isExtension = hasattr(self, "Extension")

		selfTables = tables

		if isExtension:
			assert extTables is not None, "Program or XML editing error. Extension subtables cannot contain extensions subtables"
			tables, extTables, done = extTables, None, {}

		# add Coverage table if it is sorted last.
		sortCoverageLast = 0
		if hasattr(self, "sortCoverageLast"):
			# Find coverage table
			for i in range(numItems):
				item = self.items[i]
				if hasattr(item, "name") and (item.name == "Coverage"):
					sortCoverageLast = 1
					break
			if id(item) not in done:
				item._gatherTables(tables, extTables, done)
			else:
				# We're a new parent of item
				pass

		for i in iRange:
			item = self.items[i]
			if not hasattr(item, "getData"):
				continue

			if sortCoverageLast and (i==1) and item.name == 'Coverage':
				# we've already 'gathered' it above
				continue

			if id(item) not in done:
				item._gatherTables(tables, extTables, done)
			else:
				# Item is already written out by other parent
				pass

		selfTables.append(self)

	def getAllData(self):
		"""Assemble all data, including all subtables."""
		internedTables = {}
		self._doneWriting(internedTables)
		tables = []
		extTables = []
		done = {}
		self._gatherTables(tables, extTables, done)
		tables.reverse()
		extTables.reverse()
		# Gather all data in two passes: the absolute positions of all
		# subtable are needed before the actual data can be assembled.
		pos = 0
		for table in tables:
			table.pos = pos
			pos = pos + table.getDataLength()

		for table in extTables:
			table.pos = pos
			pos = pos + table.getDataLength()

		data = []
		for table in tables:
			tableData = table.getData()
			data.append(tableData)

		for table in extTables:
			tableData = table.getData()
			data.append(tableData)

		return bytesjoin(data)

	# interface for gathering data, as used by table.compile()

	def getSubWriter(self):
		subwriter = self.__class__(self.localState, self.tableTag)
		subwriter.parent = self # because some subtables have idential values, we discard
					# the duplicates under the getAllData method. Hence some
					# subtable writers can have more than one parent writer.
					# But we just care about first one right now.
		return subwriter

	def writeUShort(self, value):
		assert 0 <= value < 0x10000, value
		self.items.append(struct.pack(">H", value))

	def writeShort(self, value):
		assert -32768 <= value < 32768, value
		self.items.append(struct.pack(">h", value))

	def writeUInt8(self, value):
		assert 0 <= value < 256, value
		self.items.append(struct.pack(">B", value))

	def writeInt8(self, value):
		assert -128 <= value < 128, value
		self.items.append(struct.pack(">b", value))

	def writeUInt24(self, value):
		assert 0 <= value < 0x1000000, value
		b = struct.pack(">L", value)
		self.items.append(b[1:])

	def writeLong(self, value):
		self.items.append(struct.pack(">l", value))

	def writeULong(self, value):
		self.items.append(struct.pack(">L", value))

	def writeTag(self, tag):
		tag = Tag(tag).tobytes()
		assert len(tag) == 4, tag
		self.items.append(tag)

	def writeSubTable(self, subWriter):
		self.items.append(subWriter)

	def writeCountReference(self, table, name, size=2, value=None):
		ref = CountReference(table, name, size=size, value=value)
		self.items.append(ref)
		return ref

	def writeStruct(self, format, values):
		data = struct.pack(*(format,) + values)
		self.items.append(data)

	def writeData(self, data):
		self.items.append(data)

	def getOverflowErrorRecord(self, item):
		LookupListIndex = SubTableIndex = itemName = itemIndex = None
		if self.name == 'LookupList':
			LookupListIndex = item.repeatIndex
		elif self.name == 'Lookup':
			LookupListIndex = self.repeatIndex
			SubTableIndex = item.repeatIndex
		else:
			itemName = getattr(item, 'name', '<none>')
			if hasattr(item, 'repeatIndex'):
				itemIndex = item.repeatIndex
			if self.name == 'SubTable':
				LookupListIndex = self.parent.repeatIndex
				SubTableIndex = self.repeatIndex
			elif self.name == 'ExtSubTable':
				LookupListIndex = self.parent.parent.repeatIndex
				SubTableIndex = self.parent.repeatIndex
			else: # who knows how far below the SubTable level we are! Climb back up to the nearest subtable.
				itemName = ".".join([self.name, itemName])
				p1 = self.parent
				while p1 and p1.name not in ['ExtSubTable', 'SubTable']:
					itemName = ".".join([p1.name, itemName])
					p1 = p1.parent
				if p1:
					if p1.name == 'ExtSubTable':
						LookupListIndex = p1.parent.parent.repeatIndex
						SubTableIndex = p1.parent.repeatIndex
					else:
						LookupListIndex = p1.parent.repeatIndex
						SubTableIndex = p1.repeatIndex

		return OverflowErrorRecord( (self.tableTag, LookupListIndex, SubTableIndex, itemName, itemIndex) )


class CountReference(object):
	"""A reference to a Count value, not a count of references."""
	def __init__(self, table, name, size=None, value=None):
		self.table = table
		self.name = name
		self.size = size
		if value is not None:
			self.setValue(value)
	def setValue(self, value):
		table = self.table
		name = self.name
		if table[name] is None:
			table[name] = value
		else:
			assert table[name] == value, (name, table[name], value)
	def getCountData(self):
		v = self.table[self.name]
		if v is None: v = 0
		return {1:packUInt8, 2:packUShort, 4:packULong}[self.size](v)


def packUInt8 (value):
	return struct.pack(">B", value)

def packUShort(value):
	return struct.pack(">H", value)

def packULong(value):
	assert 0 <= value < 0x100000000, value
	return struct.pack(">L", value)


class BaseTable(object):

	"""Generic base class for all OpenType (sub)tables."""

	def __getattr__(self, attr):
		reader = self.__dict__.get("reader")
		if reader:
			del self.reader
			font = self.font
			del self.font
			self.decompile(reader, font)
			return getattr(self, attr)

		raise AttributeError(attr)

	def ensureDecompiled(self):
		reader = self.__dict__.get("reader")
		if reader:
			del self.reader
			font = self.font
			del self.font
			self.decompile(reader, font)

	@classmethod
	def getRecordSize(cls, reader):
		totalSize = 0
		for conv in cls.converters:
			size = conv.getRecordSize(reader)
			if size is NotImplemented: return NotImplemented
			countValue = 1
			if conv.repeat:
				if conv.repeat in reader:
					countValue = reader[conv.repeat]
				else:
					return NotImplemented
			totalSize += size * countValue
		return totalSize

	def getConverters(self):
		return self.converters

	def getConverterByName(self, name):
		return self.convertersByName[name]

	def populateDefaults(self, propagator=None):
		for conv in self.getConverters():
			if conv.repeat:
				if not hasattr(self, conv.name):
					setattr(self, conv.name, [])
				countValue = len(getattr(self, conv.name)) - conv.aux
				try:
					count_conv = self.getConverterByName(conv.repeat)
					setattr(self, conv.repeat, countValue)
				except KeyError:
					# conv.repeat is a propagated count
					if propagator and conv.repeat in propagator:
						propagator[conv.repeat].setValue(countValue)
			else:
				if conv.aux and not eval(conv.aux, None, self.__dict__):
					continue
				if hasattr(self, conv.name):
					continue # Warn if it should NOT be present?!
				if hasattr(conv, 'writeNullOffset'):
					setattr(self, conv.name, None) # Warn?
				#elif not conv.isCount:
				#	# Warn?
				#	pass

	def decompile(self, reader, font):
		self.readFormat(reader)
		table = {}
		self.__rawTable = table  # for debugging
		for conv in self.getConverters():
			if conv.name == "SubTable":
				conv = conv.getConverter(reader.tableTag,
						table["LookupType"])
			if conv.name == "ExtSubTable":
				conv = conv.getConverter(reader.tableTag,
						table["ExtensionLookupType"])
			if conv.name == "FeatureParams":
				conv = conv.getConverter(reader["FeatureTag"])
			if conv.name == "SubStruct":
				conv = conv.getConverter(reader.tableTag,
				                         table["MorphType"])
			try:
				if conv.repeat:
					if isinstance(conv.repeat, int):
						countValue = conv.repeat
					elif conv.repeat in table:
						countValue = table[conv.repeat]
					else:
						# conv.repeat is a propagated count
						countValue = reader[conv.repeat]
					countValue += conv.aux
					table[conv.name] = conv.readArray(reader, font, table, countValue)
				else:
					if conv.aux and not eval(conv.aux, None, table):
						continue
					table[conv.name] = conv.read(reader, font, table)
					if conv.isPropagated:
						reader[conv.name] = table[conv.name]
			except Exception as e:
				name = conv.name
				e.args = e.args + (name,)
				raise

		if hasattr(self, 'postRead'):
			self.postRead(table, font)
		else:
			self.__dict__.update(table)

		del self.__rawTable  # succeeded, get rid of debugging info

	def compile(self, writer, font):
		self.ensureDecompiled()
		if hasattr(self, 'preWrite'):
			table = self.preWrite(font)
		else:
			table = self.__dict__.copy()


		if hasattr(self, 'sortCoverageLast'):
			writer.sortCoverageLast = 1

		if hasattr(self, 'DontShare'):
			writer.DontShare = True

		if hasattr(self.__class__, 'LookupType'):
			writer['LookupType'].setValue(self.__class__.LookupType)

		self.writeFormat(writer)
		for conv in self.getConverters():
			value = table.get(conv.name) # TODO Handle defaults instead of defaulting to None!
			if conv.repeat:
				if value is None:
					value = []
				countValue = len(value) - conv.aux
				if isinstance(conv.repeat, int):
					assert len(value) == conv.repeat, 'expected %d values, got %d' % (conv.repeat, len(value))
				elif conv.repeat in table:
					CountReference(table, conv.repeat, value=countValue)
				else:
					# conv.repeat is a propagated count
					writer[conv.repeat].setValue(countValue)
				values = value
				for i, value in enumerate(values):
					try:
						conv.write(writer, font, table, value, i)
					except Exception as e:
						name = value.__class__.__name__ if value is not None else conv.name
						e.args = e.args + (name+'['+str(i)+']',)
						raise
			elif conv.isCount:
				# Special-case Count values.
				# Assumption: a Count field will *always* precede
				# the actual array(s).
				# We need a default value, as it may be set later by a nested
				# table. We will later store it here.
				# We add a reference: by the time the data is assembled
				# the Count value will be filled in.
				ref = writer.writeCountReference(table, conv.name, conv.staticSize)
				table[conv.name] = None
				if conv.isPropagated:
					writer[conv.name] = ref
			elif conv.isLookupType:
				# We make sure that subtables have the same lookup type,
				# and that the type is the same as the one set on the
				# Lookup object, if any is set.
				if conv.name not in table:
					table[conv.name] = None
				ref = writer.writeCountReference(table, conv.name, conv.staticSize, table[conv.name])
				writer['LookupType'] = ref
			else:
				if conv.aux and not eval(conv.aux, None, table):
					continue
				try:
					conv.write(writer, font, table, value)
				except Exception as e:
					name = value.__class__.__name__ if value is not None else conv.name
					e.args = e.args + (name,)
					raise
				if conv.isPropagated:
					writer[conv.name] = value

	def readFormat(self, reader):
		pass

	def writeFormat(self, writer):
		pass

	def toXML(self, xmlWriter, font, attrs=None, name=None):
		tableName = name if name else self.__class__.__name__
		if attrs is None:
			attrs = []
		if hasattr(self, "Format"):
			attrs = attrs + [("Format", self.Format)]
		xmlWriter.begintag(tableName, attrs)
		xmlWriter.newline()
		self.toXML2(xmlWriter, font)
		xmlWriter.endtag(tableName)
		xmlWriter.newline()

	def toXML2(self, xmlWriter, font):
		# Simpler variant of toXML, *only* for the top level tables (like GPOS, GSUB).
		# This is because in TTX our parent writes our main tag, and in otBase.py we
		# do it ourselves. I think I'm getting schizophrenic...
		for conv in self.getConverters():
			if conv.repeat:
				value = getattr(self, conv.name, [])
				for i in range(len(value)):
					item = value[i]
					conv.xmlWrite(xmlWriter, font, item, conv.name,
							[("index", i)])
			else:
				if conv.aux and not eval(conv.aux, None, vars(self)):
					continue
				value = getattr(self, conv.name, None) # TODO Handle defaults instead of defaulting to None!
				conv.xmlWrite(xmlWriter, font, value, conv.name, [])

	def fromXML(self, name, attrs, content, font):
		try:
			conv = self.getConverterByName(name)
		except KeyError:
			raise    # XXX on KeyError, raise nice error
		value = conv.xmlRead(attrs, content, font)
		if conv.repeat:
			seq = getattr(self, conv.name, None)
			if seq is None:
				seq = []
				setattr(self, conv.name, seq)
			seq.append(value)
		else:
			setattr(self, conv.name, value)

	def __ne__(self, other):
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented

		self.ensureDecompiled()
		other.ensureDecompiled()

		return self.__dict__ == other.__dict__


class FormatSwitchingBaseTable(BaseTable):

	"""Minor specialization of BaseTable, for tables that have multiple
	formats, eg. CoverageFormat1 vs. CoverageFormat2."""

	@classmethod
	def getRecordSize(cls, reader):
		return NotImplemented

	def getConverters(self):
		return self.converters.get(self.Format, [])

	def getConverterByName(self, name):
		return self.convertersByName[self.Format][name]

	def readFormat(self, reader):
		self.Format = reader.readUShort()

	def writeFormat(self, writer):
		writer.writeUShort(self.Format)

	def toXML(self, xmlWriter, font, attrs=None, name=None):
		BaseTable.toXML(self, xmlWriter, font, attrs, name)


#
# Support for ValueRecords
#
# This data type is so different from all other OpenType data types that
# it requires quite a bit of code for itself. It even has special support
# in OTTableReader and OTTableWriter...
#

valueRecordFormat = [
#	Mask	 Name		isDevice signed
	(0x0001, "XPlacement",	0,	1),
	(0x0002, "YPlacement",	0,	1),
	(0x0004, "XAdvance",	0,	1),
	(0x0008, "YAdvance",	0,	1),
	(0x0010, "XPlaDevice",	1,	0),
	(0x0020, "YPlaDevice",	1,	0),
	(0x0040, "XAdvDevice",	1,	0),
	(0x0080, "YAdvDevice",	1,	0),
#	reserved:
	(0x0100, "Reserved1",	0,	0),
	(0x0200, "Reserved2",	0,	0),
	(0x0400, "Reserved3",	0,	0),
	(0x0800, "Reserved4",	0,	0),
	(0x1000, "Reserved5",	0,	0),
	(0x2000, "Reserved6",	0,	0),
	(0x4000, "Reserved7",	0,	0),
	(0x8000, "Reserved8",	0,	0),
]

def _buildDict():
	d = {}
	for mask, name, isDevice, signed in valueRecordFormat:
		d[name] = mask, isDevice, signed
	return d

valueRecordFormatDict = _buildDict()


class ValueRecordFactory(object):

	"""Given a format code, this object convert ValueRecords."""

	def __init__(self, valueFormat):
		format = []
		for mask, name, isDevice, signed in valueRecordFormat:
			if valueFormat & mask:
				format.append((name, isDevice, signed))
		self.format = format

	def __len__(self):
		return len(self.format)

	def readValueRecord(self, reader, font):
		format = self.format
		if not format:
			return None
		valueRecord = ValueRecord()
		for name, isDevice, signed in format:
			if signed:
				value = reader.readShort()
			else:
				value = reader.readUShort()
			if isDevice:
				if value:
					from . import otTables
					subReader = reader.getSubReader(value)
					value = getattr(otTables, name)()
					value.decompile(subReader, font)
				else:
					value = None
			setattr(valueRecord, name, value)
		return valueRecord

	def writeValueRecord(self, writer, font, valueRecord):
		for name, isDevice, signed in self.format:
			value = getattr(valueRecord, name, 0)
			if isDevice:
				if value:
					subWriter = writer.getSubWriter()
					writer.writeSubTable(subWriter)
					value.compile(subWriter, font)
				else:
					writer.writeUShort(0)
			elif signed:
				writer.writeShort(value)
			else:
				writer.writeUShort(value)


class ValueRecord(object):

	# see ValueRecordFactory

	def __init__(self, valueFormat=None, src=None):
		if valueFormat is not None:
			for mask, name, isDevice, signed in valueRecordFormat:
				if valueFormat & mask:
					setattr(self, name, None if isDevice else 0)
			if src is not None:
				for key,val in src.__dict__.items():
					if not hasattr(self, key):
						continue
					setattr(self, key, val)
		elif src is not None:
			self.__dict__ = src.__dict__.copy()

	def getFormat(self):
		format = 0
		for name in self.__dict__.keys():
			format = format | valueRecordFormatDict[name][0]
		return format

	def toXML(self, xmlWriter, font, valueName, attrs=None):
		if attrs is None:
			simpleItems = []
		else:
			simpleItems = list(attrs)
		for mask, name, isDevice, format in valueRecordFormat[:4]:  # "simple" values
			if hasattr(self, name):
				simpleItems.append((name, getattr(self, name)))
		deviceItems = []
		for mask, name, isDevice, format in valueRecordFormat[4:8]:  # device records
			if hasattr(self, name):
				device = getattr(self, name)
				if device is not None:
					deviceItems.append((name, device))
		if deviceItems:
			xmlWriter.begintag(valueName, simpleItems)
			xmlWriter.newline()
			for name, deviceRecord in deviceItems:
				if deviceRecord is not None:
					deviceRecord.toXML(xmlWriter, font, name=name)
			xmlWriter.endtag(valueName)
			xmlWriter.newline()
		else:
			xmlWriter.simpletag(valueName, simpleItems)
			xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		from . import otTables
		for k, v in attrs.items():
			setattr(self, k, int(v))
		for element in content:
			if not isinstance(element, tuple):
				continue
			name, attrs, content = element
			value = getattr(otTables, name)()
			for elem2 in content:
				if not isinstance(elem2, tuple):
					continue
				name2, attrs2, content2 = elem2
				value.fromXML(name2, attrs2, content2, font)
			setattr(self, name, value)

	def __ne__(self, other):
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.__dict__ == other.__dict__
