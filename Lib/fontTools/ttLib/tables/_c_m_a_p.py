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
			if (format < 8) and not length:
				continue  # bogus cmap subtable?
			if format in [8,10,12]:
				format, reserved, length = struct.unpack(">HHL", data[offset:offset+8])
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
		format = safeEval(name[12:])
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
					self.language,
					self.__dict__)
		otherTuple = (
					other.platformID,
					other.platEncID,
					other.language,
					other.__dict__)
		return cmp(selfTuple, otherTuple)


class cmap_format_0(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, length, language = struct.unpack(">HHH", data[:6])
		self.language = int(language)
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
		data = struct.pack(">HHH", 0, 262, self.language) + glyphIdArray.tostring()
		assert len(data) == 262
		return data
	
	def toXML(self, writer, ttFont):
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("language", self.language),
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
		self.language = safeEval(attrs["language"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


subHeaderFormat = ">HHhH"
class SubHeader:
	def __init__(self):
		self.firstCode = None
		self.entryCount = None
		self.idDelta = None
		self.idRangeOffset = None
		self.glyphIndexArray = []
		
class cmap_format_2(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, length, language = struct.unpack(">HHH", data[:6])
		self.language = int(language)
		data = data[6:]
		subHeaderKeys = []
		maxSubHeaderindex = 0
		
		# get the key array, and determine the number of subHeaders.
		for i in range(256):
			key = struct.unpack(">H", data[:2])[0]
			value = int(key)/8
			if value > maxSubHeaderindex:
				maxSubHeaderindex  = value
			data = data[2:]
			subHeaderKeys.append(value)
	
		#Load subHeaders
		subHeaderList = []
		for i in range(maxSubHeaderindex + 1):
			subHeader = SubHeader()
			(subHeader.firstCode, subHeader.entryCount, subHeader.idDelta, \
				subHeader.idRangeOffset) = struct.unpack(subHeaderFormat, data[:8])
			data = data[8:]
			giData = data[subHeader.idRangeOffset-2:]
			for j in range(subHeader.entryCount):
				gi = struct.unpack(">H", giData[:2])[0]
				giData = giData[2:]
				subHeader.glyphIndexArray.append(int(gi))
			 		
			subHeaderList.append(subHeader)
		
		# How this gets processed. 
		# Charcodes may be one or two bytes.
		# The first byte of a charcode is mapped through the  subHeaderKeys, to select
		# a subHeader. For any subheader but 0, the next byte is then mapped through the
		# selected subheader. If subheader Index 0 is selected, then the byte itself is 
		# mapped through the subheader, and there is no second byte.
		# Then assume that the subsequent byte is the first byte of the next charcode,and repeat.
		# 
		# Each subheader references a range in the glyphIndexArray whose length is entryCount.
		# The range in glyphIndexArray referenced by a sunheader may overlap with the range in glyphIndexArray
		# referenced by another subheader.
		# The only subheader that will be referenced by more than one first-byte value is the subheader
		# that maps the entire range of glyphID values to glyphIndex 0, e.g notdef:
		#	 {firstChar 0, EntryCount 0,idDelta 0,idRangeOffset xx}
		# A byte being mapped though a subheader is treated as in index into a mapping of array index to font glyphIndex.
		# A subheader specifies a subrange within (0...256) by the
		# firstChar and EntryCount values. If the byte value is outside the subrange, then the glyphIndex is zero
		# (e.g. glyph not in font).
		# If the byte index is in the subrange, then an offset index is calculated as (byteIndex - firstChar).
		# The index to glyphIndex mapping is a subrange of the glyphIndexArray. You find the start of the subrange by 
		# counting idRangeOffset bytes from the idRangeOffset word. The first value in this subrange is the
		# glyphIndex for the index firstChar. The offset index should then be used in this array to get the glyphIndex.
		# Example for Logocut-Medium
		# first byte of charcode = 129; selects subheader 1.
		# subheader 1 = {firstChar 64, EntryCount 108,idDelta 42,idRangeOffset 0252}
		# second byte of charCode = 66
		# the index offset = 66-64 = 2.
		# The subrange of the glyphIndexArray starting at 0x0252 bytes from the idRangeOffset word is:
		# [glyphIndexArray index], [subrange array index] = glyphIndex
		# [256], [0]=1 	from charcode [129, 64]
		# [257], [1]=2  	from charcode [129, 65]
		# [258], [2]=3  	from charcode [129, 66]
		# [259], [3]=4  	from charcode [129, 67]
		# So, the glyphIndex = 3 from the array. Then if idDelta is not zero, add it to the glyphInex to get the final glyphIndex
		# value. In this case the final glyph index = 3+ 42 -> 45 for the final glyphIndex. Whew!
		# Has anyone ever really tried to overlap the subHeader subranges in the glyphIndexArray? I doubt it!
		
		self.data = ""
		self.cmap = {}
		for firstByte in range(256):
			subHeadindex = subHeaderKeys[firstByte]
			subHeader = subHeaderList[subHeadindex]
			if subHeadindex == 0:
				if (firstByte < subHeader.firstCode) or (firstByte >= subHeader.firstCode + subHeader.entryCount):
					gi = 0
				else:
					charCode = firstByte
					offsetIndex = firstByte - subHeader.firstCode
					gi = subHeader.glyphIndexArray[offsetIndex]
					if gi != 0:
						gi = gi + subHeader.idDelta
				gName = ttFont.getGlyphName(gi)
				self.cmap[charCode] = gName
			else:
				if subHeader.entryCount:
					for offsetIndex in range(subHeader.entryCount):
						charCode = firstByte * 256 + offsetIndex + subHeader.firstCode
						gi = subHeader.glyphIndexArray[offsetIndex]
						if gi != 0:
							gi = gi + subHeader.idDelta
						gName = ttFont.getGlyphName(gi)
						self.cmap[charCode] = gName
				else:
					# Is a subHead that maps to .notdef. We do need to record it, so we can later
					# know that this firstByte value is the initial byte of a two byte charcode,
					# as opposed to a sing byte charcode.
					charCode = firstByte * 256
					gName = ttFont.getGlyphName(0)
					self.cmap[charCode] = gName
		
	def compile(self, ttFont):
		kEmptyTwoCharCodeRange = -1
		items = self.cmap.items()
		items.sort()

		# All one-byte code values map through the subHeaderKeys table to subheader 0.
		# Assume that all entries in the subHeaderKeys table are one-byte codes unless proven otherwise.
		subHeaderKeys = [0 for x in  range(256)] 
		subHeaderList = []
		
		lastFirstByte = -1
		for item in items:
			charCode = item[0]
			firstbyte = charCode >> 8
			secondByte = charCode & 0x00FF
			gi = ttFont.getGlyphID(item[1])
			if firstbyte != lastFirstByte:
				if lastFirstByte > -1:
					# fix GI's and iDelta of last subheader.
					subHeader.idDelta = 0
					if subHeader.entryCount > 0:
						minGI = min(subHeader.glyphIndexArray) -1
						if minGI > 0:
							subHeader.idDelta = minGI
							for i in range(subHeader.entryCount):
								subHeader.glyphIndexArray[i] = subHeader.glyphIndexArray[i] - minGI
					assert (subHeader.entryCount == len(subHeader.glyphIndexArray)), "Error - subhead entry count does not match len of glyphID subrange."
				# init new subheader
				subHeader = SubHeader()
				subHeader.firstCode = secondByte
				if (secondByte == 0) and ( gi==0 ) and (lastFirstByte > -1): # happens only when the font has no glyphs in the this charcpde range.
					subHeader.entryCount = 0
					subHeaderKeys[firstbyte] = kEmptyTwoCharCodeRange
				else:
					subHeader.entryCount = 1
					subHeader.glyphIndexArray.append(gi)
					subHeaderList.append(subHeader)
					subHeaderKeys[firstbyte] = len(subHeaderList) -1
				lastFirstByte = firstbyte
			else:
				assert (subHeader.entryCount != 0), "Error: we should never see another entry for an empty 2 byte charcode range."
				codeDiff = secondByte - (subHeader.firstCode + subHeader.entryCount)
				for i in range(codeDiff):
					subHeader.glyphIndexArray.append(0)
				subHeader.glyphIndexArray.append(gi)
				subHeader.entryCount = subHeader.entryCount + codeDiff + 1
		# fix GI's and iDelta of last subheader.
		subHeader.idDelta = 0
		if subHeader.entryCount > 0:
			minGI = min(subHeader.glyphIndexArray) -1
			if minGI > 0:
				subHeader.idDelta = minGI
				for i in range(subHeader.entryCount):
					subHeaderList[i] = subHeaderList[i] - minGI

		# Now we add a last subheader for the subHeaderKeys which mapped to empty two byte charcode ranges.
		subHeader = SubHeader()
		subHeader.firstCode = 0
		subHeader.entryCount = 0
		subHeader.idDelta = 0
		subHeader.idRangeOffset = 2
		subHeaderList.append(subHeader)
		emptySubheadIndex = len(subHeaderList) - 1
		for index in range(256):
			if subHeaderKeys[index] < 0:
				subHeaderKeys[index] = emptySubheadIndex
		# Since this is the last subheader, the GlyphIndex Array starts two bytes after the start of the
		# idRangeOffset word of this subHeader. we can safely point to the first entry in the GlyphIndexArray,
		# since the first subrange of the GlyphIndexArray is for subHeader 0, which always starts with 
		# charcode 0 and GID 0.
		
		# I am not going to try and optimise by trying to overlap the glyphIDArray subranges of the subheaders -
		# I will just write them out sequentially.
		idRangeOffset = (len(subHeaderList)-1)*8  + 2 # offset to beginning of glyphIDArray from first subheader idRangeOffset.
		for subHeader in subHeaderList[:-1]: # skip last special empty-set subheader
			subHeader.idRangeOffset = idRangeOffset
			idRangeOffset = (idRangeOffset -8) + subHeader.entryCount*2 # one less subheader, one more subRange.
		
		# Now we can write out the data!
		length = 6 + 512 + 8*len(subHeaderList) # header, 256 subHeaderKeys, and subheader array.
		for subhead in 	subHeaderList[:-1]:
			length = length + subhead.entryCount*2
		data = struct.pack(">HHH", 2, length, self.language)
		for index in subHeaderKeys:
			data = data + struct.pack(">H", index*8)
		for subhead in 	subHeaderList:
			data = data + struct.pack(subHeaderFormat, subhead.firstCode, subhead.entryCount, subhead.idDelta, subhead.idRangeOffset)
		for subhead in 	subHeaderList[:-1]:
			for gi in subhead.glyphIndexArray:
				data = data + struct.pack(">H", gi)
			
		assert (len(data) == length), "Error: cmap format 2 is not same length as calculated! actual: " + str(len(data))+ " calc : " + str(length)
		return data

	def toXML(self, writer, ttFont):
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("language", self.language),
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
		self.language = safeEval(attrs["language"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


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
		(format, length, self.language, segCountX2, 
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
		header = struct.pack(cmap_format_4_format, self.format, length, self.language, 
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
				("language", self.language),
				])
		writer.newline()
		
		for code, name in codes:
			writer.simpletag("map", code=hex(code), name=name)
			writer.comment(Unicode[code])
			writer.newline()
		
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.language = safeEval(attrs["language"])
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
		format, length, language, firstCode, entryCount = struct.unpack(
				">HHHHH", data[:10])
		self.language = int(language)
		firstCode = int(firstCode)
		self.language = int(language)
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
				6, len(data) + 10, self.language, firstCode, len(self.cmap))
		return header + data
	
	def toXML(self, writer, ttFont):
		codes = self.cmap.items()
		codes.sort()
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("language", self.language),
				])
		writer.newline()
		
		for code, name in codes:
			writer.simpletag("map", code=hex(code), name=name)
			writer.newline()
		
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.language = safeEval(attrs["language"])
		self.cmap = {}
		for element in content:
			if type(element) <> TupleType:
				continue
			name, attrs, content = element
			if name <> "map":
				continue
			self.cmap[safeEval(attrs["code"])] = attrs["name"]


class cmap_format_12(CmapSubtable):
	
	def decompile(self, data, ttFont):
		format, reserved, length, language, nGroups = struct.unpack(">HHLLL", data[:16])
		data = data[16:]
		assert len(data) == nGroups*12 == (length - 16) 
		self.cmap = cmap = {}
		for i in range(nGroups):
			startCharCode, endCharCode, glyphID = struct.unpack(">LLL",data[:12] )
			data = data[12:]
			while startCharCode <= endCharCode:
				glyphName = ttFont.getGlyphName(glyphID)
				cmap[startCharCode] = glyphName
				glyphID = glyphID + 1
				startCharCode = startCharCode + 1
		self.format = format
		self.reserved = reserved
		self.length = length
		self.language = language
		self.nGroups = nGroups
	
	def compile(self, ttFont):
		cmap = {}  # code:glyphID mapping
		for code, glyphName in self.cmap.items():
			cmap[code] = ttFont.getGlyphID(glyphName)

		charCodes = self.cmap.keys()
		charCodes.sort()
		startCharCode = charCodes[0]
		startGlyphID = cmap[startCharCode]
		prevCharCode = startCharCode
		prevGlyphID = startGlyphID
		nGroups = 0
		data = ""

		for charCode in charCodes[1:]:
			glyphID = cmap[charCode]
			if charCode != prevCharCode+1 or glyphID != prevGlyphID+1:
				endCharCode = prevCharCode
				data = data + struct.pack(">LLL", startCharCode, endCharCode, startGlyphID)
				startGlyphID = glyphID
				startCharCode = charCode
				nGroups = nGroups + 1
			prevCharCode = charCode
			prevGlyphID = glyphID
		# Need to write out the last group
		endCharCode = prevCharCode
		data = data + struct.pack(">LLL", startCharCode, endCharCode, startGlyphID)
		nGroups = nGroups + 1

		# Prepend header information
		data = struct.pack(">HHLLL", self.format, 0, len(data)+16, self.language, nGroups) + data
		return data
	
	def toXML(self, writer, ttFont):
		from fontTools.unicode import Unicode
		codes = self.cmap.items()
		codes.sort()
		writer.begintag(self.__class__.__name__, [
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("format", self.format),
				("reserved", self.reserved),
				("length", self.length),
				("language", self.language),
				("nGroups", self.nGroups),
				])
		writer.newline()

		for code, name in codes:
			writer.simpletag("map", code=hex(code), name=name)
			writer.comment(Unicode[code])
			writer.newline()
		writer.endtag(self.__class__.__name__)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.language = safeEval(attrs["language"])
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
		12: cmap_format_12,
		}


