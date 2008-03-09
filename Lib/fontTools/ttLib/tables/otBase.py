from DefaultTable import DefaultTable
import otData
import struct
from types import TupleType

class OverflowErrorRecord:
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
		import otTables
		cachingStats = None
		reader = OTTableReader(data, self.tableTag, cachingStats=cachingStats)
		tableClass = getattr(otTables, self.tableTag)
		self.table = tableClass()
		self.table.decompile(reader, font)
		if 0:
			stats = [(v, k) for k, v in cachingStats.items()]
			stats.sort()
			stats.reverse()
			print "cachingsstats for ", self.tableTag
			for v, k in stats:
				if v < 2:
					break
				print v, k
			print "---", len(stats)
	
	def compile(self, font):
		""" Create a top-level OTFWriter for the GPOS/GSUB table.
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
		writer = OTTableWriter(self.tableTag)
		writer.parent = None
		self.table.compile(writer, font)
		return writer.getAllData()

	def toXML(self, writer, font):
		self.table.toXML2(writer, font)
	
	def fromXML(self, (name, attrs, content), font):
		import otTables
		if not hasattr(self, "table"):
			tableClass = getattr(otTables, self.tableTag)
			self.table = tableClass()
		self.table.fromXML((name, attrs, content), font)


class OTTableReader:
	
	"""Helper class to retrieve data from an OpenType table."""
	
	def __init__(self, data, tableType, offset=0, valueFormat=None, cachingStats=None):
		self.data = data
		self.offset = offset
		self.pos = offset
		self.tableType = tableType
		if valueFormat is None:
			valueFormat = (ValueRecordFactory(), ValueRecordFactory())
		self.valueFormat = valueFormat
		self.cachingStats = cachingStats
	
	def getSubReader(self, offset):
		offset = self.offset + offset
		if self.cachingStats is not None:
			try:
				self.cachingStats[offset] = self.cachingStats[offset] + 1
			except KeyError:
				self.cachingStats[offset] = 1
		
		subReader = self.__class__(self.data, self.tableType, offset,
			self.valueFormat, self.cachingStats)
		return subReader
	
	def readUShort(self):
		pos = self.pos
		newpos = pos + 2
		value, = struct.unpack(">H", self.data[pos:newpos])
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
	
	def readULong(self):
		pos = self.pos
		newpos = pos + 4
		value, = struct.unpack(">L", self.data[pos:newpos])
		self.pos = newpos
		return value
	
	def readTag(self):
		pos = self.pos
		newpos = pos + 4
		value = self.data[pos:newpos]
		assert len(value) == 4
		self.pos = newpos
		return value
	
	def readStruct(self, format, size=None):
		if size is None:
			size = struct.calcsize(format)
		else:
			assert size == struct.calcsize(format)
		pos = self.pos
		newpos = pos + size
		values = struct.unpack(format, self.data[pos:newpos])
		self.pos = newpos
		return values
	
	def setValueFormat(self, format, which):
		self.valueFormat[which].setFormat(format)
	
	def readValueRecord(self, font, which):
		return self.valueFormat[which].readValueRecord(self, font)


class OTTableWriter:
	
	"""Helper class to gather and assemble data for OpenType tables."""
	
	def __init__(self, tableType, valueFormat=None):
		self.items = []
		self.tableType = tableType
		if valueFormat is None:
			valueFormat = ValueRecordFactory(), ValueRecordFactory()
		self.valueFormat = valueFormat
		self.pos = None
	
	# assembler interface
	
	def getAllData(self):
		"""Assemble all data, including all subtables."""
		self._doneWriting()
		tables, extTables = self._gatherTables()
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

		return "".join(data)
	
	def getDataLength(self):
		"""Return the length of this table in bytes, without subtables."""
		l = 0
		if hasattr(self, "Extension"):
			longOffset = 1
		else:
			longOffset = 0
		for item in self.items:
			if hasattr(item, "getData") or hasattr(item, "getCountData"):
				if longOffset:
					l = l + 4  # sizeof(ULong)
				else:
					l = l + 2  # sizeof(UShort)
			else:
				l = l + len(item)
		return l
	
	def getData(self):
		"""Assemble the data for this writer/table, without subtables."""
		items = list(self.items)  # make a shallow copy
		if hasattr(self,"Extension"):
			longOffset = 1
		else:
			longOffset = 0
		pos = self.pos
		numItems = len(items)
		for i in range(numItems):
			item = items[i]
			
			if hasattr(item, "getData"):
				if longOffset:
					items[i] = packULong(item.pos - pos)
				else:
					try:
						items[i] = packUShort(item.pos - pos)
					except AssertionError:
						# provide data to fix overflow problem.
						# If the overflow is to a lookup, or from a lookup to a subtable, 
						# just report the current item.
						if self.name in [ 'LookupList', 'Lookup']:
							overflowErrorRecord = self.getOverflowErrorRecord(item)
						else:
							# overflow is within a subTable. Life is more complicated.
							# If we split the sub-table just before the current item, we may still suffer overflow.
							# This is because duplicate table merging is done only within an Extension subTable tree;
							# when we split the subtable in two, some items may no longer be duplicates. 
							# Get worst case by adding up all the item lengths, depth first traversal.
							# and then report the first item that overflows a short.
							def getDeepItemLength(table):
								if hasattr(table, "getDataLength"):
									length = 0
									for item in table.items:
										length = length + getDeepItemLength(item)
								else:
									length = len(table)
								return length
	
							length = self.getDataLength()
							if hasattr(self, "sortCoverageLast") and item.name == "Coverage":
								# Coverage is first in the item list, but last in the table list,
								# The original overflow is really in the item list. Skip the Coverage 
								# table in the following test.
								items = items[i+1:]
	
							for j in range(len(items)):
								item = items[j]
								length = length + getDeepItemLength(item)
								if length > 65535:
									break
						overflowErrorRecord = self.getOverflowErrorRecord(item)
						
						
						raise OTLOffsetOverflowError, overflowErrorRecord

		return "".join(items)
	
	def __hash__(self):
		# only works after self._doneWriting() has been called
		return hash(self.items)
	
	def __cmp__(self, other):
		if hasattr(other, "items"):
			return cmp(self.items, other.items)
		else:
			return cmp(id(self), id(other))
	
	def _doneWriting(self, internedTables=None):
		# Convert CountData references to data string items
		# collapse duplicate table references to a unique entry
		# "tables" are OTTableWriter objects.

		# For Extension Lookup types, we can
		# eliminate duplicates only within the tree under the Extension Lookup,
		# as offsets may exceed 64K even between Extension LookupTable subtables.
		if internedTables is None:
			internedTables = {}
		items = self.items
		iRange = range(len(items))
		
		if hasattr(self, "Extension"):
			newTree = 1
		else:
			newTree = 0
		for i in iRange:
			item = items[i]
			if hasattr(item, "getCountData"):
				items[i] = item.getCountData()
			elif hasattr(item, "getData"):
				if newTree:
					item._doneWriting()
				else:
					item._doneWriting(internedTables)
					if internedTables.has_key(item):
						items[i] = item = internedTables[item]
					else:
						internedTables[item] = item
		self.items = tuple(items)
	
	def _gatherTables(self, tables=None, extTables=None, done=None):
		# Convert table references in self.items tree to a flat
		# list of tables in depth-first traversal order.
		# "tables" are OTTableWriter objects.
		# We do the traversal in reverse order at each level, in order to 
		# resolve duplicate references to be the last reference in the list of tables.
		# For extension lookups, duplicate references can be merged only within the
		# writer tree under the  extension lookup.
		if tables is None: # init call for first time.
			tables = []
			extTables = []
			done = {}

		done[self] = 1

		numItems = len(self.items)
		iRange = range(numItems)
		iRange.reverse()

		if hasattr(self, "Extension"):
			appendExtensions = 1
		else:
			appendExtensions = 0

		# add Coverage table if it is sorted last.
		sortCoverageLast = 0
		if hasattr(self, "sortCoverageLast"):
			# Find coverage table
			for i in range(numItems):
				item = self.items[i]
				if hasattr(item, "name") and (item.name == "Coverage"):
					sortCoverageLast = 1
					break
			if not done.has_key(item):
				item._gatherTables(tables, extTables, done)
			else:
				index = max(item.parent.keys())
				item.parent[index + 1] = self

		saveItem = None
		for i in iRange:
			item = self.items[i]
			if not hasattr(item, "getData"):
				continue

			if sortCoverageLast and (i==1) and item.name == 'Coverage':
				# we've already 'gathered' it above
				continue

			if appendExtensions:
				assert extTables != None, "Program or XML editing error. Extension subtables cannot contain extensions subtables"
				newDone = {}
				item._gatherTables(extTables, None, newDone)

			elif not done.has_key(item):
				item._gatherTables(tables, extTables, done)
			else:
				index = max(item.parent.keys())
				item.parent[index + 1] = self


		tables.append(self)
		return tables, extTables
	
	# interface for gathering data, as used by table.compile()
	
	def getSubWriter(self):
		subwriter = self.__class__(self.tableType, self.valueFormat)
		subwriter.parent = {0:self} # because some subtables have idential values, we discard
									# the duplicates under the getAllData method. Hence some
									# subtable writers can have more than one parent writer.
		return subwriter
	
	def writeUShort(self, value):
		assert 0 <= value < 0x10000
		self.items.append(struct.pack(">H", value))
	
	def writeShort(self, value):
		self.items.append(struct.pack(">h", value))
	
	def writeLong(self, value):
		self.items.append(struct.pack(">l", value))
	
	def writeULong(self, value):
		self.items.append(struct.pack(">L", value))
	
	def writeTag(self, tag):
		assert len(tag) == 4
		self.items.append(tag)
	
	def writeSubTable(self, subWriter):
		self.items.append(subWriter)
	
	def writeCountReference(self, table, name):
		self.items.append(CountReference(table, name))
	
	def writeStruct(self, format, values):
		data = apply(struct.pack, (format,) + values)
		self.items.append(data)
	
	def writeData(self, data):
		self.items.append(data)
	
	def setValueFormat(self, format, which):
		self.valueFormat[which].setFormat(format)
	
	def writeValueRecord(self, value, font, which):
		return self.valueFormat[which].writeValueRecord(self, font, value)

	def	getOverflowErrorRecord(self, item):
		LookupListIndex = SubTableIndex = itemName = itemIndex = None
		if self.name == 'LookupList':
			LookupListIndex = item.repeatIndex
		elif self.name == 'Lookup':
			LookupListIndex = self.repeatIndex
			SubTableIndex = item.repeatIndex
		else:
			itemName = item.name
			if hasattr(item, 'repeatIndex'):
				itemIndex = item.repeatIndex
			if self.name == 'SubTable':
				LookupListIndex = self.parent[0].repeatIndex
				SubTableIndex = self.repeatIndex
			elif self.name == 'ExtSubTable':
				LookupListIndex = self.parent[0].parent[0].repeatIndex
				SubTableIndex = self.parent[0].repeatIndex
			else: # who knows how far below the SubTable level we are! Climb back up to the nearest subtable.
				itemName = ".".join(self.name, item.name)
				p1 = self.parent[0]
				while p1 and p1.name not in ['ExtSubTable', 'SubTable']:
					itemName = ".".join(p1.name, item.name)
					p1 = p1.parent[0]
				if p1:
					if p1.name == 'ExtSubTable':
						LookupListIndex = self.parent[0].parent[0].repeatIndex
						SubTableIndex = self.parent[0].repeatIndex
					else:
						LookupListIndex = self.parent[0].repeatIndex
						SubTableIndex = self.repeatIndex

		return OverflowErrorRecord( (self.tableType, LookupListIndex, SubTableIndex, itemName, itemIndex) )


class CountReference:
	"""A reference to a Count value, not a count of references."""
	def __init__(self, table, name):
		self.table = table
		self.name = name
	def getCountData(self):
		return packUShort(self.table[self.name])


def packUShort(value):
	assert 0 <= value < 0x10000, value
	return struct.pack(">H", value)


def packULong(value):
	assert 0 <= value < 0x100000000, value
	return struct.pack(">L", value)



class TableStack:
	"""A stack of table dicts, working as a stack of namespaces so we can
	retrieve values from (and store values to) tables higher up the stack."""
	def __init__(self):
		self.stack = []
	def push(self, table):
		self.stack.insert(0, table)
	def pop(self):
		self.stack.pop(0)
	def getTop(self):
		return self.stack[0]
	def getValue(self, name):
		return self.__findTable(name)[name]
	def storeValue(self, name, value):
		table = self.__findTable(name)
		if table[name] is None:
			table[name] = value
		else:
			assert table[name] == value, (table[name], value)
	def __findTable(self, name):
		for table in self.stack:
			if table.has_key(name):
				return table
		raise KeyError, name


class BaseTable:
	def __init__(self):
		self.compileStatus = 0 # 0 means table was created
									# 1 means the table.read() function was called by a table which is subject
									# to delayed compilation
									# 2 means that it was subject to delayed compilation, and 
									# has been decompiled
									# 3 means that the start and end fields have been filled out, and that we
									# can use the data string rather than compiling from the table data.

		self.recurse = 0
	
	def __getattr__(self, attr):
		# we get here only when the table does not have the attribute.
		# This method ovveride exists so that we can try to de-compile
		# a table which is subject to delayed decompilation, and then try
		# to get the value again after decompilation.
		self.recurse +=1
		if self.recurse > 2:
			# shouldn't ever get here - we should only get to two levels of recursion.
			# this guards against self.decompile NOT setting compileStatus to other than 1.
			raise AttributeError, attr 
		if self.compileStatus == 1:
			# table.read() has been called, but table has not yet been decompiled
			# This happens only for extension tables.
			self.decompile(self.reader, self.font)
			val = getattr(self, attr)
			self.recurse -=1
			return val
			
		raise AttributeError, attr 


	"""Generic base class for all OpenType (sub)tables."""
	
	def getConverters(self):
		return self.converters
	
	def getConverterByName(self, name):
		return self.convertersByName[name]
	
	def decompile(self, reader, font, tableStack=None):
		self.compileStatus = 2 # table has been decompiled.
		if tableStack is None:
			tableStack = TableStack()
		self.readFormat(reader)
		table = {}
		self.__rawTable = table  # for debugging
		tableStack.push(table)
		for conv in self.getConverters():
			if conv.name == "SubTable":
				conv = conv.getConverter(reader.tableType,
						table["LookupType"])
			if conv.name == "ExtSubTable":
				conv = conv.getConverter(reader.tableType,
						table["ExtensionLookupType"])
			if conv.repeat:
				l = []
				for i in range(tableStack.getValue(conv.repeat) + conv.repeatOffset):
					l.append(conv.read(reader, font, tableStack))
				table[conv.name] = l
			else:
				table[conv.name] = conv.read(reader, font, tableStack)
		tableStack.pop()
		self.postRead(table, font)
		del self.__rawTable  # succeeded, get rid of debugging info

	def preCompile(self):
		pass # used only by the LookupList class

	def compile(self, writer, font, tableStack=None):
		if tableStack is None:
			tableStack = TableStack()
		table = self.preWrite(font)

		if hasattr(self, 'sortCoverageLast'):
			writer.sortCoverageLast = 1

		self.writeFormat(writer)
		tableStack.push(table)
		for conv in self.getConverters():
			value = table.get(conv.name)
			if conv.repeat:
				if value is None:
					value = []
				tableStack.storeValue(conv.repeat, len(value) - conv.repeatOffset)
				for i in range(len(value)):
					conv.write(writer, font, tableStack, value[i], i)
			elif conv.isCount:
				# Special-case Count values.
				# Assumption: a Count field will *always* precede
				# the actual array.
				# We need a default value, as it may be set later by a nested
				# table. TableStack.storeValue() will then find it here.
				table[conv.name] = None
				# We add a reference: by the time the data is assembled
				# the Count value will be filled in.
				writer.writeCountReference(table, conv.name)
			else:
				conv.write(writer, font, tableStack, value)
		tableStack.pop()
	
	def readFormat(self, reader):
		pass
	
	def writeFormat(self, writer):
		pass
	
	def postRead(self, table, font):
		self.__dict__.update(table)
	
	def preWrite(self, font):
		return self.__dict__.copy()
	
	def toXML(self, xmlWriter, font, attrs=None):
		tableName = self.__class__.__name__
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
			value = getattr(self, conv.name)
			if conv.repeat:
				for i in range(len(value)):
					item = value[i]
					conv.xmlWrite(xmlWriter, font, item, conv.name,
							[("index", i)])
			else:
				conv.xmlWrite(xmlWriter, font, value, conv.name, [])
	
	def fromXML(self, (name, attrs, content), font):
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
	
	def __cmp__(self, other):
		# this is only for debugging, so it's ok to barf
		# when 'other' has no __dict__ or __class__
		rv = cmp(self.__class__, other.__class__)
		if not rv:
			rv = cmp(self.__dict__, other.__dict__)
			return rv
		else:
			return rv


class FormatSwitchingBaseTable(BaseTable):
	
	"""Minor specialization of BaseTable, for tables that have multiple
	formats, eg. CoverageFormat1 vs. CoverageFormat2."""
	
	def getConverters(self):
		return self.converters[self.Format]
	
	def getConverterByName(self, name):
		return self.convertersByName[self.Format][name]
	
	def readFormat(self, reader):
		self.Format = reader.readUShort()
		assert self.Format <> 0, (self, reader.pos, len(reader.data))
	
	def writeFormat(self, writer):
		writer.writeUShort(self.Format)


#
# Support for ValueRecords
#
# This data type is so different from all other OpenType data types that
# it requires quite a bit of code for itself. It even has special support
# in OTTableReader and OTTableWriter...
#

valueRecordFormat = [
#	Mask	 Name            isDevice  signed
	(0x0001, "XPlacement",   0,        1),
	(0x0002, "YPlacement",   0,        1),
	(0x0004, "XAdvance",     0,        1),
	(0x0008, "YAdvance",     0,        1),
	(0x0010, "XPlaDevice",   1,        0),
	(0x0020, "YPlaDevice",   1,        0),
	(0x0040, "XAdvDevice",   1,        0),
	(0x0080, "YAdvDevice",   1,        0),
# 	reserved:
	(0x0100, "Reserved1",    0,        0),
	(0x0200, "Reserved2",    0,        0),
	(0x0400, "Reserved3",    0,        0),
	(0x0800, "Reserved4",    0,        0),
	(0x1000, "Reserved5",    0,        0),
	(0x2000, "Reserved6",    0,        0),
	(0x4000, "Reserved7",    0,        0),
	(0x8000, "Reserved8",    0,        0),
]

def _buildDict():
	d = {}
	for mask, name, isDevice, signed in valueRecordFormat:
		d[name] = mask, isDevice, signed
	return d

valueRecordFormatDict = _buildDict()


class ValueRecordFactory:
	
	"""Given a format code, this object convert ValueRecords."""
	
	def setFormat(self, valueFormat):
		format = []
		for mask, name, isDevice, signed in valueRecordFormat:
			if valueFormat & mask:
				format.append((name, isDevice, signed))
		self.format = format
	
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
					import otTables
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


class ValueRecord:
	
	# see ValueRecordFactory
	
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
					deviceRecord.toXML(xmlWriter, font)
			xmlWriter.endtag(valueName)
			xmlWriter.newline()
		else:
			xmlWriter.simpletag(valueName, simpleItems)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		import otTables
		for k, v in attrs.items():
			setattr(self, k, int(v))
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			value = getattr(otTables, name)()
			for elem2 in content:
				if type(elem2) <> TupleType:
					continue
				value.fromXML(elem2, font)
			setattr(self, name, value)
	
	def __cmp__(self, other):
		# this is only for debugging, so it's ok to barf
		# when 'other' has no __dict__ or __class__
		rv = cmp(self.__class__, other.__class__)
		if not rv:
			rv = cmp(self.__dict__, other.__dict__)
			return rv
		else:
			return rv

