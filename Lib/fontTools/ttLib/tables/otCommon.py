"""fontTools.ttLib.tables.otCommon.py -- Various data structures used
by various OpenType tables."""

import struct, sstruct
import string
import DefaultTable
from fontTools import ttLib

# temporary switch:
# - if true use possibly incomplete compile/decompile/toXML/fromXML implementation
# - if false use DefaultTable, ie. dump as hex.
TESTING_OT = 0


class base_GPOS_GSUB(DefaultTable.DefaultTable):
	
	"""Base class for GPOS and GSUB tables; they share the same high-level structure."""
	
	version = 0x00010000
	
	def decompile(self, data, otFont):
		#self.data = data  # handy for debugging
		reader = OTTableReader(data)
		self.version = reader.readLong()
		if self.version <> 0x00010000:
			raise ttLib.TTLibError, "unknown table version: 0x%.8x" % self.version
		
		self.scriptList = reader.readTable(ScriptList, otFont, self.tableTag)
		self.featureList = reader.readTable(FeatureList, otFont, self.tableTag)
		self.lookupList = reader.readTable(LookupList, otFont, self.tableTag)
	
	def compile(self, otFont):
		writer = OTTableWriter()
		writer.writeLong(self.version)
		writer.writeTable(self.scriptList, otFont)
		writer.writeTable(self.featureList, otFont)
		writer.writeTable(self.lookupList, otFont)
		return writer.getData()

	def toXML(self, xmlWriter, otFont):
		names = [("ScriptList", "scriptList"), 
				("FeatureList", "featureList"), 
				("LookupList", "lookupList")]
		for name, attr in names:
			xmlWriter.newline()
			xmlWriter.begintag(name)
			xmlWriter.newline()
			table = getattr(self, attr)
			table.toXML(xmlWriter, otFont)
			xmlWriter.endtag(name)
			xmlWriter.newline()
		xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


if not TESTING_OT:
	# disable the GPOS/GSUB code, dump as hex.
	base_GPOS_GSUB = DefaultTable.DefaultTable

#
# Script List and subtables
#

class ScriptList:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		scriptCount = reader.readUShort()
		self.scripts = reader.readTagList(scriptCount, Script, otFont)
	
	def compile(self, writer, otFont):
		writer.writeUShort(len(self.scripts))
		writer.writeTagList(self.scripts, otFont)
	
	def toXML(self, xmlWriter, otFont):
		for tag, script in self.scripts:
			xmlWriter.begintag("Script", tag=tag)
			xmlWriter.newline()
			script.toXML(xmlWriter, otFont)
			xmlWriter.endtag("Script")
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


class Script:
	
	def decompile(self, reader, otFont):
		self.defaultLangSystem = reader.readTable(LanguageSystem, otFont)
		langSysCount = reader.readUShort()
		self.languageSystems = reader.readTagList(langSysCount, LanguageSystem, otFont)
	
	def compile(self, writer, otFont):
		writer.writeTable(self.defaultLangSystem, otFont)
		writer.writeUShort(len(self.languageSystems))
		writer.writeTagList(self.languageSystems, otFont)
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.begintag("DefaultLanguageSystem")
		xmlWriter.newline()
		self.defaultLangSystem.toXML(xmlWriter, otFont)
		xmlWriter.endtag("DefaultLanguageSystem")
		xmlWriter.newline()
		for tag, langSys in self.languageSystems:
			xmlWriter.begintag("LanguageSystem", tag=tag)
			xmlWriter.newline()
			langSys.toXML(xmlWriter, otFont)
			xmlWriter.endtag("LanguageSystem")
			xmlWriter.newline()


class LanguageSystem:
	
	def decompile(self, reader, otFont):
		self.lookupOrder = reader.readUShort()
		self.reqFeatureIndex = reader.readUShort()
		featureCount = reader.readUShort()
		self.featureIndex = reader.readUShortArray(featureCount)
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.lookupOrder)
		writer.writeUShort(self.reqFeatureIndex)
		writer.writeUShort(len(self.featureIndex))
		writer.writeUShortArray(self.featureIndex)
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.simpletag("LookupOrder", value=self.lookupOrder)
		xmlWriter.newline()
		xmlWriter.simpletag("ReqFeature", index=hex(self.reqFeatureIndex))
		xmlWriter.newline()
		for index in self.featureIndex:
			xmlWriter.simpletag("Feature", index=index)
			xmlWriter.newline()


#
# Feature List and subtables
#

class FeatureList:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		featureCount = reader.readUShort()
		self.features = reader.readTagList(featureCount, Feature, otFont)
	
	def compile(self, writer, otFont):
		writer.writeUShort(len(self.features))
		writer.writeTagList(self.features, otFont)
	
	def toXML(self, xmlWriter, otFont):
		for index in range(len(self.features)):
			tag, feature = self.features[index]
			xmlWriter.begintag("Feature", index=index, tag=tag)
			xmlWriter.newline()
			feature.toXML(xmlWriter, otFont)
			xmlWriter.endtag("Feature")
			xmlWriter.newline()
			
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


class Feature:
	
	def decompile(self, reader, otFont):
		self.featureParams = reader.readUShort()
		lookupCount = reader.readUShort()
		self.lookupListIndex = reader.readUShortArray(lookupCount)
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.featureParams)
		writer.writeUShort(len(self.lookupListIndex))
		writer.writeUShortArray(self.lookupListIndex)
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.simpletag("FeatureParams", value=hex(self.featureParams))
		xmlWriter.newline()
		for lookupIndex in self.lookupListIndex:
			xmlWriter.simpletag("LookupTable", index=lookupIndex)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


#
# Lookup List and subtables
#

class LookupList:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		lookupCount = reader.readUShort()
		self.lookup = reader.readTableArray(lookupCount, LookupTable, otFont, self.parentTag)
	
	def compile(self, writer, otFont):
		writer.writeUShort(len(self.lookup))
		writer.writeTableArray(self.lookup, otFont)
	
	def toXML(self, xmlWriter, otFont):
		for i in range(len(self.lookup)):
			xmlWriter.newline()
			lookupTable = self.lookup[i]
			xmlWriter.begintag("LookupTable",
				[("index", i), ("LookupType", lookupTable.lookupType),
				("LookupFlag", hex(lookupTable.lookupFlag))])
			xmlWriter.newline()
			lookupTable.toXML(xmlWriter, otFont)
			xmlWriter.endtag("LookupTable")
			xmlWriter.newline()
		xmlWriter.newline()
		
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


class LookupTable:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		parentTable = otFont[self.parentTag]
		self.lookupType = reader.readUShort()
		self.lookupFlag = reader.readUShort()
		subTableCount = reader.readUShort()
		lookupTypeClass = parentTable.getLookupTypeClass(self.lookupType)
		self.subTables = reader.readTableArray(subTableCount, lookupTypeClass, otFont)
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.lookupType)
		writer.writeUShort(self.lookupFlag)
		writer.writeUShort(len(self.subTables))
		writer.writeTableArray(self.subTables, otFont)
	
	def __repr__(self):
		if not hasattr(self, "lookupTypeName"):
			m = ttLib.getTableModule(self.parentTag)
			self.lookupTypeName = m.lookupTypeClasses[self.lookupType].__name__
		return "<%s LookupTable at %x>" % (self.lookupTypeName, id(self))
	
	def toXML(self, xmlWriter, otFont):
		for subTable in self.subTables:
			name = subTable.__class__.__name__
			xmlWriter.begintag(name)
			xmlWriter.newline()
			subTable.toXML(xmlWriter, otFont)
			xmlWriter.endtag(name)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


#
# Other common formats
#

class CoverageTable:
	
	def getGlyphIDs(self):
		return self.glyphIDs
	
	def getGlyphNames(self):
		return self.glyphNames
	
	def setGlyphNames(self, glyphNames, otFont):
		glyphIDs = map(otFont.getGlyphID, glyphNames)
		glyphIDs = map(None, glyphIDs, glyphNames)
		glyphIDs.sort()
		self.glyphNames = map(lambda (x, y): y, glyphIDs)
		self.glyphIDs = map(lambda (x, y): x, glyphIDs)
		return self.glyphNames
	
	def makeGlyphNames(self, otFont):
		self.glyphNames = map(lambda i, o=otFont.getGlyphOrder(): o[i], self.glyphIDs)
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format == 1:
			self.decompileFormat1(reader, otFont)
		elif format == 2:
			self.decompileFormat2(reader, otFont)
		else:
			raise ttLib.TTLibError, "unknown Coverage table format: %d" % format
		self.makeGlyphNames(otFont)
	
	def decompileFormat1(self, reader, otFont):
		glyphCount = reader.readUShort()
		self.glyphIDs = glyphIDs = []
		for i in range(glyphCount):
			glyphID = reader.readUShort()
			glyphIDs.append(glyphID)
	
	def decompileFormat2(self, reader, otFont):
		rangeCount = reader.readUShort()
		self.glyphIDs = glyphIDs = []
		for i in range(rangeCount):
			startID = reader.readUShort()
			endID = reader.readUShort()
			startCoverageIndex = reader.readUShort()
			for glyphID in range(startID, endID + 1):
				glyphIDs.append(glyphID)
	
	def compile(self, writer, otFont):
		# figure out which format is more compact, doing so by brute force...
		
		# compile format 1
		writer1 = OTTableWriter()
		writer1.writeUShort(1)
		self.compileFormat1(writer1, otFont)
		data1 = writer1.getData()
		
		# compile format 2
		writer2 = OTTableWriter()
		writer2.writeUShort(2)
		self.compileFormat2(writer2, otFont)
		data2 = writer2.getData()
		
		if len(data1) < len(data2):
			writer.writeRaw(data1)
		else:
			writer.writeRaw(data2)
	
	def compileFormat1(self, writer, otFont):
		writer.writeUShort(len(self.glyphIDs))
		writer.writeUShortArray(self.glyphIDs)
	
	def compileFormat2(self, writer, otFont):
		ranges = []
		lastID = startID = self.glyphIDs[0]
		startCoverageIndex = 0
		glyphCount = len(self.glyphIDs)
		for i in range(1, glyphCount+1):
			if i == glyphCount:
				glyphID = 0x1ffff  # arbitrary, but larger than 0x10000
			else:
				glyphID = self.glyphIDs[i]
			if glyphID <> (lastID + 1):
				ranges.append((startID, lastID, startCoverageIndex))
				startCoverageIndex = i
				startID = glyphID
			lastID = glyphID
		ranges.sort()  # sort by startID
		writer.writeUShort(len(ranges))
		for startID, endID, startCoverageIndex in ranges:
			writer.writeUShort(startID)
			writer.writeUShort(endID)
			writer.writeUShort(startCoverageIndex)


def unpackCoverageArray(coverageArray):
	coverageArray = coverageArray[:]
	for i in range(len(coverageArray)):
		coverageArray[i] = coverageArray[i].getGlyphNames()
	return coverageArray

def buildCoverageArray(coverageArray, otFont):
	coverageArray = coverageArray[:]
	for i in range(len(coverageArray)):
		coverage = CoverageTable()
		coverage.setGlyphNames(coverageArray[i], otFont)
		coverageArray[i] = coverage
	return coverageArray


class ClassDefinitionTable:
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format == 1:
			self.decompileFormat1(reader, otFont)
		elif format == 2:
			self.decompileFormat2(reader, otFont)
		else:
			raise ttLib.TTLibError, "unknown Class table format: %d" % format
		self.reverse()
	
	def reverse(self):
		classDefs = {}
		for glyphName, classCode in self.classDefs:
			try:
				classDefs[classCode].append(glyphName)
			except KeyError:
				classDefs[classCode] = [glyphName]
		self.classDefs = classDefs
	
	def decompileFormat1(self, reader, otFont):
		self.classDefs = classDefs = []
		startGlyphID = reader.readUShort()
		glyphCount = reader.readUShort()
		for i in range(glyphCount):
			glyphName = otFont.getglyphName(startGlyphID + i)
			classValue = reader.readUShort()
			if classValue:
				classDefs.append((glyphName, classValue))
	
	def decompileFormat2(self, reader, otFont):
		self.classDefs = classDefs = []
		classRangeCount = reader.readUShort()
		for i in range(classRangeCount):
			startID = reader.readUShort()
			endID = reader.readUShort()
			classValue = reader.readUShort()
			for glyphID in range(startID, endID + 1):
				if classValue:
					glyphName = otFont.getGlyphName(glyphID)
					classDefs.append((glyphName, classValue))
	
	def compile(self, writer, otFont):
		XXX
		# brute force again
		data1 = self.compileFormat1(otFont)
		data2 = self.compileFormat2(otFont)
		if len(data1) <= len(data2):
			format = 1
			data = data1
		else:
			format = 2
			data = data2
		return struct.pack(">H", format) + data
	
	def compileFormat1(self, otFont):
		XXX
		items = map(lambda (glyphName, classValue), getGlyphID=otFont.getGlyphID:
				(getGlyphID(glyphName), classValue), self.glyphs.items())
		items.sort()
		startGlyphID = items[0][0]
		endGlyphID = items[-1][0]
		data = ""
		lastID = startGlyphID
		for glyphID, classValue in items:
			for i in range(lastID + 1, glyphID - 1):
				data = data + "\0\0"  # 0 == default class
			data = data + struct.pack(">H", classValue)
			lastID = glyphID
		return struct.pack(">H", endGlyphID - startGlyphID + 1) + data
	
	def compileFormat2(self, otFont):
		XXX
		items = map(lambda (glyphName, classValue), getGlyphID=otFont.getGlyphID:
				(getGlyphID(glyphName), classValue), self.glyphs.items())
		items.sort()
		ranges = []
		lastID, lastClassValue = items[0][0]
		startID = lastID
		itemCount = len(items)
		for i in range(1, itemCount+1):
			if i == itemCount:
				glyphID = 0x1ffff  # arbitrary, but larger than 0x10000
				classValue = 0
			else:
				glyphID, classValue = items[i]
			if glyphID <> (lastID + 1) or lastClassValue <> classValue:
				ranges.append((startID, lastID, lastClassValue))
				startID = glyphID
				lastClassValue = classValue
			lastID = glyphID
			lastClassValue = classValue
		rangeData = ""
		for startID, endID, classValue in ranges:
			rangeData = rangeData + struct.pack(">HHH", startID, endID, classValue)
		return pack(">H", len(ranges)) + rangeData
	
	def __getitem__(self, glyphName):
		if self.glyphs.has_key(glyphName):
			return self.glyphs[glyphName]
		else:
			return 0  # default class


class DeviceTable:
	
	def decompile(self, reader, otFont):
		self.startSize = reader.readUShort()
		endSize = reader.readUShort()
		deltaFormat = reader.readUShort()
		if deltaFormat == 1:
			bits = 2
		elif deltaFormat == 2:
			bits = 4
		elif deltaFormat == 3:
			bits = 8
		else:
			raise ttLib.TTLibError, "unknown Device table delta format: %d" % deltaFormat
		numCount = 16 / bits
		deltaCount = endSize - self.startSize + 1
		deltaValues = []
		mask = (1 << bits) - 1
		threshold = (1 << bits) / 2
		shift = 1 << bits
		for i in range(0, deltaCount, numCount):
			offset = 2*i/numCount
			chunk = reader.readUShort()
			deltas = []
			for j in range(numCount):
				delta = chunk & mask
				if delta >= threshold:
					delta = delta - shift
				deltas.append(delta)
				chunk = chunk >> bits
			deltas.reverse()
			deltaValues = deltaValues + deltas
		self.deltaValues = deltaValues[:deltaCount]
	
	def compile(self, writer, otFont):
		raise NotImplementedError
		# XXX
		deltaValues = self.deltaValues
		startSize = self.startSize
		endSize = startSize + len(deltaValues) - 1
		smallestDelta = min(deltas)
		largestDelta = ma(deltas)
		if smallestDelta >= -2 and largestDelta < 2:
			deltaFormat = 1
			bits = 2
		elif smallestDelta >= -8 and largestDelta < 8:
			deltaFormat = 2
			bits = 4
		elif smallestDelta >= -128 and largestDelta < 128:
			deltaFormat = 3
			bits = 8
		else:
			raise ttLib.TTLibError, "delta value too large: min=%d, max=%d" % (smallestDelta, largestDelta)
		data = struct.pack(">HHH", startSize, endSize, deltaFormat)
		numCount = 16 / bits
		# pad the list to a multiple of numCount values
		remainder = len(deltaValues) % numCount
		if remainder:
			deltaValues = deltaValues + [0] * (numCount - remainder)
		deltaData = ""
		for i in range(0, len(deltaValues), numCount):
			chunk = 0
			for j in range(numCount):
				chunk = chunk << bits
				chunk = chunk | deltaValues[i+j]
			deltaData = deltaData + struct.pack(">H", chunk)
		return data + deltaData


#
# Miscelaneous helper routines and classes
#

class OTTableReader:
	
	"""Data wrapper, mostly designed to make reading OT data less cumbersome."""
	
	def __init__(self, data, offset=0):
		self.data = data
		self.offset = offset
		self.pos = offset
	
	def readTable(self, tableClass, otFont, *args):
		offset = self.readOffset()
		if offset == 0:
			return None
		newReader = self.getSubString(offset)
		table = apply(tableClass, args)
		table.decompile(newReader, otFont)
		return table
	
	def readUShort(self):
		pos = self.pos
		newpos = pos + 2
		value = int(struct.unpack(">H", self.data[pos:newpos])[0])
		self.pos = newpos
		return value
	
	readOffset = readUShort
	
	def readShort(self):
		pos = self.pos
		newpos = pos + 2
		value = int(struct.unpack(">h", self.data[pos:newpos])[0])
		self.pos = newpos
		return value
	
	def readLong(self):
		pos = self.pos
		newpos = pos + 4
		value = int(struct.unpack(">l", self.data[pos:newpos])[0])
		self.pos = newpos
		return value
	
	def readTag(self):
		pos = self.pos
		newpos = pos + 4
		value = self.data[pos:newpos]
		assert len(value) == 4
		self.pos = newpos
		return value
	
	def readUShortArray(self, count):
		return self.readArray(count, "H")
	
	def readShortArray(self, count):
		return self.readArray(count, "h")
	
	def readArray(self, count, format):
		from array import array
		assert format in "Hh"
		pos = self.pos
		newpos = pos + 2 * count
		a = array(format)
		a.fromstring(self.data[pos:newpos])
		if ttLib.endian <> 'big':
			a.byteswap()
		self.pos = newpos
		return a.tolist()
	
	def readTableArray(self, count, tableClass, otFont, *args):
		list = []
		for i in range(count):
			list.append(apply(self.readTable, (tableClass, otFont) + args))
		return list
	
	def readTagList(self, count, tableClass, otFont, *args):
		list = []
		for i in range(count):
			tag = self.readTag()
			table = apply(self.readTable, (tableClass, otFont) + args)
			list.append((tag, table))
		return list
	
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
	
	def getSubString(self, offset):
		return self.__class__(self.data, self.offset+offset)
	
	def seek(self, n):
		"""Relative seek."""
		self.pos = self.pos + n


class OTTableWriter:
	
	def __init__(self):
		self.items = []
	
	def getData(self):
		items = self.items[:]
		offset = 0
		for item in items:
			if hasattr(item, "getData"):
				offset = offset + 2  # sizeof(Offset)
			else:
				offset = offset + len(item)
		subTables = []
		cache = {}
		for i in range(len(items)):
			item = items[i]
			if hasattr(item, "getData"):
				subTableData = item.getData()
				if cache.has_key(subTableData):
					items[i] = packOffset(cache[subTableData])
				else:
					items[i] = packOffset(offset)
					subTables.append(subTableData)
					cache[subTableData] = offset
					offset = offset + len(subTableData)
		return string.join(items, "") + string.join(subTables, "")
	
	def writeTable(self, subTable, otFont):
		if subTable is None:
			self.writeUShort(0)
		else:
			subWriter = self.__class__()
			self.items.append(subWriter)
			subTable.compile(subWriter, otFont)
	
	def writeUShort(self, value):
		self.items.append(struct.pack(">H", value))
	
	def writeShort(self, value):
		self.items.append(struct.pack(">h", value))
	
	def writeLong(self, value):
		self.items.append(struct.pack(">l", value))
	
	def writeTag(self, tag):
		assert len(tag) == 4
		self.items.append(tag)
	
	def writeUShortArray(self, array):
		return self.writeArray(array, "H")
	
	def writeShortArray(self, array):
		return self.writeArray(array, "h")
	
	def writeArray(self, list, format):
		from array import array
		assert format in "Hh"
		a = array(format, list)
		if ttLib.endian <> 'big':
			a.byteswap()
		self.items.append(a.tostring())
	
	def writeTableArray(self, list, otFont):
		for subTable in list:
			self.writeTable(subTable, otFont)
	
	def writeTagList(self, list, otFont):
		for tag, subTable in list:
			self.writeTag(tag)
			self.writeTable(subTable, otFont)
	
	def writeStruct(self, format, values):
		data = apply(struct.pack, (format,) + values)
		self.items.append(data)
	
	def writeRaw(self, data):
		self.items.append(data)


def packOffset(offset):
	return struct.pack(">H", offset)

