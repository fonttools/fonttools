import DefaultTable
import struct
import array
from fontTools import ttLib
from fontTools.misc.textTools import safeEval, readHex
from types import TupleType


class table__c_m_a_p(DefaultTable.DefaultTable):
	
	def getcmap(self, platformID, platEncID):
		for subtable in self.tables:
			if (subtable.platformID == platformID and 
					subtable.platEncID == platEncID):
				return subtable
		return None # not found
	
	def decompile(self, data, ttFont):
		tableVersion, numSubTables = struct.unpack(">HH", data[:4])
		self.tableVersion = int(tableVersion)
		self.tables = tables = []
		for i in range(numSubTables):
			platformID, platEncID, offset = struct.unpack(
					">HHl", data[4+i*8:4+(i+1)*8])
			platformID, platEncID = int(platformID), int(platEncID)
			format, length = struct.unpack(">HH", data[offset:offset+4])
			if not length:
				continue  # bogus cmap subtable?
			if not cmap_classes.has_key(format):
				table = cmap_format_unknown(format)
			else:
				table = cmap_classes[format](format)
			table.platformID = platformID
			table.platEncID = platEncID
			table.decompile(data[offset:offset+int(length)], ttFont)
			tables.append(table)
	
	def compile(self, ttFont):
		self.tables.sort()    # sort according to the spec; see CmapSubtable.__cmp__()
		numSubTables = len(self.tables)
		totalOffset = 4 + 8 * numSubTables
		data = struct.pack(">HH", self.tableVersion, numSubTables)
		tableData = ""
		done = {}  # remember the data so we can reuse the "pointers"
		for table in self.tables:
			chunk = table.compile(ttFont)
			if done.has_key(chunk):
				offset = done[chunk]
			else:
				offset = done[chunk] = totalOffset + len(tableData)
				tableData = tableData + chunk
			data = data + struct.pack(">HHl", table.platformID, table.platEncID, offset)
		return data + tableData
	
	def toXML(self, writer, ttFont):
		writer.simpletag("tableVersion", version=self.tableVersion)
		writer.newline()
		for table in self.tables:
			table.toXML(writer, ttFont)
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name == "tableVersion":
			self.tableVersion = safeEval(attrs["version"])
			return
		if name[:12] <> "cmap_format_":
			return
		if not hasattr(self, "tables"):
			self.tables = []
		format = safeEval(name[12])
		if not cmap_classes.has_key(format):
			table = cmap_format_unknown(format)
		else:
			table = cmap_classes[format](format)
		table.platformID = safeEval(attrs["platformID"])
		table.platEncID = safeEval(attrs["platEncID"])
		table.fromXML((name, attrs, content), ttFont)
		self.tables.append(table)


class CmapSubtable:
	
	def __init__(self, format):
		self.format = format
	
	def toXML(self, writer, ttFont):
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				])
		writer.newline()
		writer.dumphex(self.compile(ttFont))
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.decompile(readHex(content), ttFont)
	
	def __cmp__(self, other):
		# implemented so that list.sort() sorts according to the cmap spec.
		selfTuple = (
					self.platformID,
					self.platEncID,
					self.version,
					self.__dict__)
		otherTuple = (
					other.platformID,
					other.platEncID,
					other.version,
					other.__dict__)
		return cmp(selfTuple, otherTuple)


class cmap_format_0(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, length, version = struct.unpack(">HHH", data[:6])
		self.version = int(version)
		assert len(data) == 262 == length
		glyphIdArray = array.array("B")
		glyphIdArray.fromstring(data[6:])
		self.cmap = cmap = {}
		for charCode in range(len(glyphIdArray)):
			cmap[charCode] = ttFont.getGlyphName(glyphIdArray[charCode])
	
	def compile(self, ttFont):
		charCodes = self.cmap.keys()
		charCodes.sort()
		assert charCodes == range(256)  # charCodes[charCode] == charCode
		for charCode in charCodes:
			# reusing the charCodes list!
			charCodes[charCode] = ttFont.getGlyphID(self.cmap[charCode])
		glyphIdArray = array.array("B", charCodes)
		data = struct.pack(">HHH", 0, 262, self.version) + glyphIdArray.tostring()
		assert len(data) == 262
		return data
	
	def toXML(self, writer, ttFont):
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("version", self.version),
				])
		writer.newline()
		items = self.cmap.items()
		items.sort()
		for code, name in items:
			writer.simpletag("map", code=hex(code), name=name)
			writer.newline()
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.version = safeEval(attrs["version"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


class cmap_format_2(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, length, version = struct.unpack(">HHH", data[:6])
		self.version = int(version)
		self.data = data
	
	def compile(self, ttFont):
		return self.data


cmap_format_4_format = ">7H"

#uint16  endCode[segCount]          # Ending character code for each segment, last = 0xFFFF.
#uint16  reservedPad                # This value should be zero
#uint16  startCode[segCount]        # Starting character code for each segment
#uint16  idDelta[segCount]          # Delta for all character codes in segment
#uint16  idRangeOffset[segCount]    # Offset in bytes to glyph indexArray, or 0
#uint16  glyphIndexArray[variable]  # Glyph index array

def splitRange(startCode, endCode, cmap):
	# Try to split a range of character codes into subranges with consecutive
	# glyph IDs in such a way that the cmap4 subtable can be stored "most"
	# efficiently. I can't prove I've got the optimal solution, but it seems
	# to do well with the fonts I tested: none became bigger, many became smaller.
	if startCode == endCode:
		return [], [endCode]
	
	lastID = cmap[startCode]
	lastCode = startCode
	inOrder = None
	orderedBegin = None
	subRanges = []
	
	# Gather subranges in which the glyph IDs are consecutive.
	for code in range(startCode + 1, endCode + 1):
		glyphID = cmap[code]
		
		if glyphID - 1 == lastID:
			if inOrder is None or not inOrder:
				inOrder = 1
				orderedBegin = lastCode
		else:
			if inOrder:
				inOrder = 0
				subRanges.append((orderedBegin, lastCode))
				orderedBegin = None
				
		lastID = glyphID
		lastCode = code
	
	if inOrder:
		subRanges.append((orderedBegin, lastCode))
	assert lastCode == endCode
	
	# Now filter out those new subranges that would only make the data bigger.
	# A new segment cost 8 bytes, not using a new segment costs 2 bytes per
	# character.
	newRanges = []
	for b, e in subRanges:
		if b == startCode and e == endCode:
			break  # the whole range, we're fine
		if b == startCode or e == endCode:
			threshold = 4  # split costs one more segment
		else:
			threshold = 8  # split costs two more segments
		if (e - b + 1) > threshold:
			newRanges.append((b, e))
	subRanges = newRanges
	
	if not subRanges:
		return [], [endCode]
	
	if subRanges[0][0] != startCode:
		subRanges.insert(0, (startCode, subRanges[0][0] - 1))
	if subRanges[-1][1] != endCode:
		subRanges.append((subRanges[-1][1] + 1, endCode))
	
	# Fill the "holes" in the segments list -- those are the segments in which
	# the glyph IDs are _not_ consecutive.
	i = 1
	while i < len(subRanges):
		if subRanges[i-1][1] + 1 != subRanges[i][0]:
			subRanges.insert(i, (subRanges[i-1][1] + 1, subRanges[i][0] - 1))
			i = i + 1
		i = i + 1
	
	# Transform the ranges into startCode/endCode lists.
	start = []
	end = []
	for b, e in subRanges:
		start.append(b)
		end.append(e)
	start.pop(0)
	
	assert len(start) + 1 == len(end)
	return start, end


class cmap_format_4(CmapSubtable):
	
	def decompile(self, data, ttFont):
		(format, length, self.version, segCountX2, 
				searchRange, entrySelector, rangeShift) = \
					struct.unpack(cmap_format_4_format, data[:14])
		assert len(data) == length, "corrupt cmap table (%d, %d)" % (len(data), length)
		segCount = segCountX2 / 2
		
		allCodes = array.array("H")
		allCodes.fromstring(data[14:])
		if ttLib.endian <> "big":
			allCodes.byteswap()
		
		# divide the data
		endCode = allCodes[:segCount]
		allCodes = allCodes[segCount+1:]  # the +1 is skipping the reservedPad field
		startCode = allCodes[:segCount]
		allCodes = allCodes[segCount:]
		idDelta = allCodes[:segCount]
		allCodes = allCodes[segCount:]
		idRangeOffset = allCodes[:segCount]
		glyphIndexArray = allCodes[segCount:]
		
		# build 2-byte character mapping
		cmap = {}
		for i in range(len(startCode) - 1):	# don't do 0xffff!
			for charCode in range(startCode[i], endCode[i] + 1):
				rangeOffset = idRangeOffset[i]
				if rangeOffset == 0:
					glyphID = charCode + idDelta[i]
				else:
					# *someone* needs to get killed.
					index = idRangeOffset[i] / 2 + (charCode - startCode[i]) + i - len(idRangeOffset)
					if glyphIndexArray[index] <> 0:  # if not missing glyph
						glyphID = glyphIndexArray[index] + idDelta[i]
					else:
						glyphID = 0  # missing glyph
				cmap[charCode] = ttFont.getGlyphName(glyphID % 0x10000)
		self.cmap = cmap
	
	def compile(self, ttFont):
		from fontTools.ttLib.sfnt import maxPowerOfTwo
		
		cmap = {}  # code:glyphID mapping
		for code, glyphName in self.cmap.items():
			cmap[code] = ttFont.getGlyphID(glyphName)
		codes = cmap.keys()
		codes.sort()
		
		# Build startCode and endCode lists.
		# Split the char codes in ranges of consecutive char codes, then split
		# each range in more ranges of consecutive/not consecutive glyph IDs.
		# See splitRange().
		lastCode = codes[0]
		endCode = []
		startCode = [lastCode]
		for charCode in codes[1:]:  # skip the first code, it's the first start code
			if charCode == lastCode + 1:
				lastCode = charCode
				continue
			start, end = splitRange(startCode[-1], lastCode, cmap)
			startCode.extend(start)
			endCode.extend(end)
			startCode.append(charCode)
			lastCode = charCode
		endCode.append(lastCode)
		startCode.append(0xffff)
		endCode.append(0xffff)
		
		# build up rest of cruft
		idDelta = []
		idRangeOffset = []
		glyphIndexArray = []
		
		for i in range(len(endCode)-1):  # skip the closing codes (0xffff)
			indices = []
			for charCode in range(startCode[i], endCode[i] + 1):
				indices.append(cmap[charCode])
			if indices == range(indices[0], indices[0] + len(indices)):
				idDelta.append((indices[0] - startCode[i]) % 0x10000)
				idRangeOffset.append(0)
			else:
				# someone *definitely* needs to get killed.
				idDelta.append(0)
				idRangeOffset.append(2 * (len(endCode) + len(glyphIndexArray) - i))
				glyphIndexArray.extend(indices)
		idDelta.append(1)  # 0xffff + 1 == (tadaa!) 0. So this end code maps to .notdef
		idRangeOffset.append(0)
		
		# Insane. 
		segCount = len(endCode)
		segCountX2 = segCount * 2
		maxExponent = maxPowerOfTwo(segCount)
		searchRange = 2 * (2 ** maxExponent)
		entrySelector = maxExponent
		rangeShift = 2 * segCount - searchRange
		
		allCodes = array.array("H", 
				endCode + [0] + startCode + idDelta + idRangeOffset + glyphIndexArray)
		if ttLib.endian <> "big":
			allCodes.byteswap()
		data = allCodes.tostring()
		length = struct.calcsize(cmap_format_4_format) + len(data)
		header = struct.pack(cmap_format_4_format, self.format, length, self.version, 
				segCountX2, searchRange, entrySelector, rangeShift)
		data = header + data
		return data
	
	def toXML(self, writer, ttFont):
		from fontTools.unicode import Unicode
		codes = self.cmap.items()
		codes.sort()
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("version", self.version),
				])
		writer.newline()
		
		for code, name in codes:
			writer.simpletag("map", code=hex(code), name=name)
			writer.comment(Unicode[code])
			writer.newline()
		
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.version = safeEval(attrs["version"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


class cmap_format_6(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, length, version, firstCode, entryCount = struct.unpack(
				">HHHHH", data[:10])
		self.version = int(version)
		firstCode = int(firstCode)
		self.version = int(version)
		data = data[10:]
		#assert len(data) == 2 * entryCount  # XXX not true in Apple's Helvetica!!!
		glyphIndexArray = array.array("H")
		glyphIndexArray.fromstring(data[:2 * int(entryCount)])
		if ttLib.endian <> "big":
			glyphIndexArray.byteswap()
		self.cmap = cmap = {}
		for i in range(len(glyphIndexArray)):
			glyphID = glyphIndexArray[i]
			glyphName = ttFont.getGlyphName(glyphID)
			cmap[i+firstCode] = glyphName
	
	def compile(self, ttFont):
		codes = self.cmap.keys()
		codes.sort()
		assert codes == range(codes[0], codes[0] + len(codes))
		glyphIndexArray = array.array("H", [0] * len(codes))
		firstCode = codes[0]
		for i in range(len(codes)):
			code = codes[i]
			glyphIndexArray[code-firstCode] = ttFont.getGlyphID(self.cmap[code])
		if ttLib.endian <> "big":
			glyphIndexArray.byteswap()
		data = glyphIndexArray.tostring()
		header = struct.pack(">HHHHH", 
				6, len(data) + 10, self.version, firstCode, len(self.cmap))
		return header + data
	
	def toXML(self, writer, ttFont):
		codes = self.cmap.items()
		codes.sort()
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("version", self.version),
				])
		writer.newline()
		
		for code, name in codes:
			writer.simpletag("map", code=hex(code), name=name)
			writer.newline()
		
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.version = safeEval(attrs["version"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


class cmap_format_unknown(CmapSubtable):
	
	def decompile(self, data, ttFont):
		self.data = data
	
	def compile(self, ttFont):
		return self.data


cmap_classes = {
		0: cmap_format_0,
		2: cmap_format_2,
		4: cmap_format_4,
		6: cmap_format_6,
		}


