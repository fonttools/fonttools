"""ttLib.tables.otCommon.py -- Various data structures used by various OpenType tables.
"""

import struct, sstruct
import DefaultTable
from fontTools import ttLib


class base_GPOS_GSUB(DefaultTable.DefaultTable):
	
	"""Base class for GPOS and GSUB tables; they share the same high-level structure."""
	
	version = 0x00010000
	
	def decompile(self, data, otFont):
		self.data = data   # while work is in progress, dump as hex
		return
		reader = OTTableReader(data)
		self.version = reader.readLong()
		if self.version <> 0x00010000:
			raise ttLib.TTLibError, "unknown table version: 0x%.8x" % self.version
		
		self.scriptList = reader.readTable(ScriptList, otFont, self.tableTag)
		self.featureList = reader.readTable(FeatureList, otFont, self.tableTag)
		self.lookupList = reader.readTable(LookupList, otFont, self.tableTag)
	
	def compile(self, otFont):
		return self.data


class Dummy:
	
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
		xxx


#
# Script List and subtables
#

class ScriptList:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		scriptCount = reader.readUShort()
		self.scripts = reader.readTagList(scriptCount, Script, otFont)
	
	def compile(self, otFont):
		XXXXXX
	
	def toXML(self, xmlWriter, otFont):
		for tag, script in self.scripts:
			xmlWriter.begintag("Script", tag=tag)
			xmlWriter.newline()
			script.toXML(xmlWriter, otFont)
			xmlWriter.endtag("Script")
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class Script:
	
	def decompile(self, reader, otFont):
		self.defaultLangSystem = None
		self.defaultLangSystem = reader.readTable(LanguageSystem, otFont)
		langSysCount = reader.readUShort()
		self.languageSystems = reader.readTagList(langSysCount, LanguageSystem, otFont)
	
	def compile(self, otFont):
		XXXXX
	
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
	
	def compile(self, otFont):
		xxx
	
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
	
	def compile(self, otFont):
		XXXXX
	
	def toXML(self, xmlWriter, otFont):
		for index in range(len(self.features)):
			tag, feature = self.features[index]
			xmlWriter.begintag("Feature", index=index, tag=tag)
			xmlWriter.newline()
			feature.toXML(xmlWriter, otFont)
			xmlWriter.endtag("Feature")
			xmlWriter.newline()
			
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class Feature:
	
	def decompile(self, reader, otFont):
		self.featureParams = reader.readUShort()
		lookupCount = reader.readUShort()
		self.lookupListIndex = reader.readUShortArray(lookupCount)
	
	def compile(self, otFont):
		XXXXX
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.simpletag("FeatureParams", value=hex(self.featureParams))
		xmlWriter.newline()
		for lookupIndex in self.lookupListIndex:
			xmlWriter.simpletag("LookupTable", index=lookupIndex)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		xxx


#
# Lookup List and subtables
#

class LookupList:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		lookupCount = reader.readUShort()
		self.lookup = lookup = []
		for i in range(lookupCount):
			lookup.append(reader.readTable(LookupTable, otFont, self.parentTag))
	
	def compile(self, otFont):
		XXXXX
	
	def toXML(self, xmlWriter, otFont):
		for i in range(len(self.lookup)):
			xmlWriter.newline()
			lookupTable = self.lookup[i]
			xmlWriter.begintag("LookupTable", index=i)
			xmlWriter.newline()
			lookupTable.toXML(xmlWriter, otFont)
			xmlWriter.endtag("LookupTable")
			xmlWriter.newline()
		xmlWriter.newline()
		
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class LookupTable:
	
	def __init__(self, parentTag):
		self.parentTag = parentTag
	
	def decompile(self, reader, otFont):
		parentTable = otFont[self.parentTag]
		self.lookupType = reader.readUShort()
		self.lookupFlag = reader.readUShort()
		subTableCount = reader.readUShort()
		self.subTables = subTables = []
		lookupTypeClass = parentTable.getLookupTypeClass(self.lookupType)
		for i in range(subTableCount):
			subTables.append(reader.readTable(lookupTypeClass, otFont))
	
	def compile(self, otFont):
		XXXXXX
	
	def __repr__(self):
		if not hasattr(self, "lookupTypeName"):
			m = ttLib.getTableModule(self.parentTag)
			self.lookupTypeName = m.lookupTypeClasses[self.lookupType].__name__
		return "<%s LookupTable at %x>" % (self.lookupTypeName, id(self))
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.simpletag("LookupFlag", value=hex(self.lookupFlag))
		xmlWriter.newline()
		for subTable in self.subTables:
			name = subTable.__class__.__name__
			xmlWriter.begintag(name)
			xmlWriter.newline()
			subTable.toXML(xmlWriter, otFont)
			xmlWriter.endtag(name)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		xxx


#
# Other common formats
#

class CoverageTable:
	
	def getGlyphIDs(self):
		return self.glyphIDs
	
	def getGlyphNames(self):
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
	
	def compile(self, otFont):
		# brute force ;-)
		data1 = self.compileFormat1(otFont)
		data2 = self.compileFormat2(otFont)
		if len(data1) <= len(data2):
			format = 1
			reader = data1
		else:
			format = 2
			reader = data2
		return struct.pack(">H", format) + reader
	
	def compileFormat1(self, otFont):
		xxxxx
		glyphIDs = map(otFont.getGlyphID, self.glyphNames)
		data = pack(">H", len(glyphIDs))
		pack = struct.pack
		for glyphID in glyphIDs:
			data = data + pack(">H", glyphID)
		return data
	
	def compileFormat2(self, otFont):
		xxxxx
		glyphIDs = map(otFont.getGlyphID, self.glyphNames)
		ranges = []
		lastID = startID = glyphIDs[0]
		startCoverageIndex = 0
		glyphCount = len(glyphIDs)
		for i in range(1, glyphCount+1):
			if i == glyphCount:
				glyphID = 0x1ffff  # arbitrary, but larger than 0x10000
			else:
				glyphID = glyphIDs[i]
			if glyphID <> (lastID + 1):
				ranges.append((startID, lastID, startCoverageIndex))
				startCoverageIndex = i
				startID = glyphID
			lastID = glyphID
		ranges.sort()  # sort by startID
		rangeData = ""
		for startID, endID, startCoverageIndex in ranges:
			rangeData = rangeData + struct.pack(">HHH", startID, endID, startCoverageIndex)
		return pack(">H", len(ranges)) + rangeData


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
	
	def compile(self, otFont):
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
		xxxxxx
		self.startSize = unpack_uint16(reader[:2])
		endSize = unpack_uint16(reader[2:4])
		deltaFormat = unpack_uint16(reader[4:6])
		reader = reader[6:]
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
			chunk = unpack_uint16(reader[offset:offset+2])
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
	
	def compile(self, otFont):
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
	
	readOffsetArray = readUShortArray
	
	def readShortArray(self, count):
		return self.readArray(count, "h")
	
	def readArray(self, count, format):
		assert format in "Hh"
		from array import array
		pos = self.pos
		newpos = pos + 2 * count
		a = array(format)
		a.fromstring(self.data[pos:newpos])
		if ttLib.endian <> 'big':
			a.byteswap()
		self.pos = newpos
		return a.tolist()
	
	def readTable(self, tableClass, otFont, *args):
		offset = self.readOffset()
		if offset == 0:
			return None
		newReader = self.getSubString(offset)
		table = apply(tableClass, args)
		table.decompile(newReader, otFont)
		return table
	
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


