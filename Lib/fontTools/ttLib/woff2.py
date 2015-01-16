from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import sys

try:
	import brotli
except ImportError:
	print('ImportError: No module named brotli.\n'
		  'The WOFF2 encoder requires the Brotli Python extension, available at:\n'
		  'https://github.com/google/brotli', file=sys.stderr)
	sys.exit(1)

import array
import struct
from fontTools.misc import sstruct
from fontTools.misc.arrayTools import calcIntBounds
from fontTools.ttLib import (TTFont, TTLibError, getTableModule, getTableClass,
	getSearchRange)
from fontTools.ttLib.sfnt import (SFNTReader, SFNTWriter, DirectoryEntry,
	WOFFFlavorData, sfntDirectoryFormat, sfntDirectorySize, SFNTDirectoryEntry,
	sfntDirectoryEntrySize, calcChecksum)
from fontTools.ttLib.tables import ttProgram


def normaliseFont(ttFont):
	""" The WOFF 2.0 conversion is guaranteed to be lossless in a bitwise sense
	only for 'normalised' font files. Normalisation occurs before any transforms,
	and involves:
		- removing the DSIG table, since the encoding process can invalidate it;
		- recalculating simple glyph bounding boxes so they don't need to be stored
		  in the bboxStream, but are recalculated by the decoder;
		- padding glyph offsets to multiple of 4 bytes;
		- setting bit 11 of head 'flags' field to indicate that the font has
		  undergone a 'lossless modifying transform'.
	"""
	if "DSIG" in ttFont:
		del ttFont["DSIG"]

	if ttFont.sfntVersion == '\x00\x01\x00\x00':
		ttFont.recalcBBoxes = True
		ttFont.padGlyphData = True
		# don't be lazy so that glyph data is 'expanded' on decompile
		ttFont.lazy = False
		# force decompile glyf table to perform normalisation steps above
		if not ttFont.isLoaded('glyf'):
			ttFont['glyf']
		# XXX Not clear if this also applies to CFF-flavoured fonts
		ttFont['head'].flags |= 1 << 11


class WOFF2Reader(SFNTReader):

	flavor = "woff2"

	def __init__(self, file):
		self.file = file

		signature = self.file.read(4)
		if signature != b"wOF2":
			raise TTLibError("Not a WOFF2 font (bad signature)")

		self.file.seek(0)
		self.DirectoryEntry = WOFF2DirectoryEntry
		sstruct.unpack(woff2DirectoryFormat, self.file.read(woff2DirectorySize), self)

		self.tables = {}
		self.tableOrder = []
		offset = 0
		for i in range(self.numTables):
			entry = self.DirectoryEntry()
			entry.fromFile(self.file)
			tag = Tag(entry.tag)
			self.tables[tag] = entry
			self.tableOrder.append(tag)
			entry.offset = offset
			offset += entry.length

		totalUncompressedSize = offset
		compressedData = self.file.read(self.totalCompressedSize)
		decompressedData = brotli.decompress(compressedData)
		if len(decompressedData) != totalUncompressedSize:
			raise TTLibError(
				'unexpected size for decompressed font data: expected %d, found %d'
				% (totalUncompressedSize, len(decompressedData)))
		self.transformBuffer = StringIO(decompressedData)

		self.flavorData = WOFF2FlavorData(self)

	def __getitem__(self, tag):
		entry = self.tables[Tag(tag)]
		rawData = entry.loadData(self.transformBuffer)
		if tag not in woff2TransformedTableTags:
			return rawData

		if hasattr(entry, 'data'):
			# table already reconstructed, return compiled data
			return entry.data

		if tag == 'glyf':
			# reconstruct both glyf and loca
			self.glyfTable = WOFF2GlyfTable()
			data = self.glyfTable.reconstruct(rawData)
		elif tag == 'loca':
			assert len(rawData) == 0, "expected 0, received %d bytes" % len(rawData)
			if not hasattr(self, 'glyfTable'):
				# make sure glyf is loaded first
				self['glyf']
			data = self.glyfTable.getLocaData()

		if len(data) != entry.origLength:
			raise TTLibError(
				"reconstructed '%s' table doesn't match original size: expected %d, found %d"
				% (tag, entry.origLength, len(data)))
		entry.data = data
		return data


class WOFF2Writer(SFNTWriter):

	flavor = "woff2"

	def __init__(self, file, numTables, sfntVersion="\000\001\000\000",
				 flavorData=None):
		self.file = file
		self.numTables = numTables
		self.sfntVersion = Tag(sfntVersion)
		self.flavorData = flavorData

		self.directoryFormat = woff2DirectoryFormat
		self.directorySize = woff2DirectorySize
		self.DirectoryEntry = WOFF2DirectoryEntry

		self.signature = "wOF2"

		self.nextTableOffset = 0
		self.transformBuffer = StringIO()

		self.tables = {}
		self.tableOrder = []

	def __setitem__(self, tag, data):
		"""Associate new entry named 'tag' with raw table data."""
		if tag in self.tables:
			raise TTLibError("cannot rewrite '%s' table" % tag)

		entry = self.DirectoryEntry()
		entry.tag = Tag(tag)
		if tag == 'head':
			entry.checkSum = calcChecksum(data[:8] + b'\0\0\0\0' + data[12:])
		else:
			entry.checkSum = calcChecksum(data)
		entry.flags = getKnownTagIndex(entry.tag)
		entry.origLength = len(data)
		# WOFF2 table data are written to disk only on close(), after all tags
		# have been specified
		entry.data = data

		self.tables[tag] = entry
		self.tableOrder.append(tag)

	def close(self):
		""" All tags must have been specified. Now write the table data and directory.
		"""
		# According to the specs, the WOFF2 table directory must reflect the 'physical
		# order' in which the tables have been encoded. Moreover, the glyf and loca
		# tables must be placed 'as a pair with loca table following the glyf table'.
		"""\
		if 'loca' in self.tableOrder and 'glyf' in self.tableOrder:
			glyfIndex = self.tableOrder.index('glyf')
			locaIndex = self.tableOrder.index('loca')
			self.tableOrder.insert(glyfIndex+1, self.tableOrder.pop(locaIndex))
		tables = [(tag, self.tables[tag]) for tag in self.tableOrder]
		"""
		# However, to pass the legacy OpenType Sanitiser currently included in browsers,
		# we must sort the table directory and data alphabetically by tag.
		# See:
		# https://github.com/google/woff2/pull/3
		# https://lists.w3.org/Archives/Public/public-webfonts-wg/2015Mar/0000.html
		# TODO(user): change to match spec once browsers are on newer OTS
		tables = sorted(self.tables.items())

		if len(tables) != self.numTables:
			raise TTLibError("wrong number of tables; expected %d, found %d" % (self.numTables, len(tables)))

		# compute the original SFNT offsets for checksum adjustment calculation
		offset = sfntDirectorySize + sfntDirectoryEntrySize * len(tables)
		for tag, entry in tables:
			entry.origOffset = offset
			offset += (entry.origLength + 3) & ~3

		# size of uncompressed font
		self.totalSfntSize = offset

		self.signature = b"wOF2"
		self.reserved = 0

		for tag, entry in tables:
			if tag == "loca":
				data = b""
			elif tag == "glyf":
				indexFormat, = struct.unpack(">H", self.tables['head'].data[50:52])
				numGlyphs, = struct.unpack(">H", self.tables['maxp'].data[4:6])
				glyfTable = WOFF2GlyfTable()
				glyfTable.setLocaData(self.tables['loca'].data, indexFormat, numGlyphs)
				data = glyfTable.transform(entry.data)
			else:
				data = entry.data
			entry.offset = self.nextTableOffset
			entry.saveData(self.transformBuffer, data)
			self.nextTableOffset += entry.length

		# update head's checkSumAdjustment
		self.writeMasterChecksum()

		# compress font data
		self.transformBuffer.seek(0)
		uncompressedData = self.transformBuffer.read()
		compressedData = brotli.compress(uncompressedData, brotli.MODE_FONT)
		self.totalCompressedSize = len(compressedData)

		# start calculating total size of WOFF2 font
		offset = woff2DirectorySize
		for tag, entry in tables:
			offset += len(entry.toString())
		offset += self.totalCompressedSize
		offset = (offset + 3) & ~3

		# calculate offsets and lengths for any metadata and/or private data
		compressedMetaData = privData = b""
		flavorData = self.flavorData or WOFF2FlavorData()
		if flavorData.majorVersion is not None and flavorData.minorVersion is not None:
			self.majorVersion = flavorData.majorVersion
			self.minorVersion = flavorData.minorVersion
		else:
			self.majorVersion, self.minorVersion = struct.unpack(
				">HH", self.tables['head'].data[4:8])
		if flavorData.metaData:
			self.metaOrigLength = len(flavorData.metaData)
			self.metaOffset = offset
			compressedMetaData = brotli.compress(flavorData.metaData)
			self.metaLength = len(compressedMetaData)
			offset += self.metaLength
		else:
			self.metaOffset = self.metaLength = self.metaOrigLength = 0
		if flavorData.privData:
			# make sure private data is padded to 4-byte boundary
			offset = (offset + 3) & ~3
			self.privOffset = offset
			self.privLength = len(flavorData.privData)
			offset += self.privLength
		else:
			self.privOffset = self.privLength = 0

		# total size of WOFF2 font, including any metadata or private data
		self.length = offset

		directory = sstruct.pack(self.directoryFormat, self)
		for tag, entry in tables:
			directory = directory + entry.toString()

		# finally write directory and compressed font data to disk
		fontData = padData(directory + compressedData)
		self.file.seek(0)
		self.file.write(fontData)

		# write any WOFF/WOFF2 metadata and/or private data using appropiate padding
		if compressedMetaData and privData:
			compressedMetaData = padData(compressedMetaData)
		if compressedMetaData:
			self.file.seek(self.metaOffset)
			assert self.file.tell() == self.metaOffset
			self.file.write(compressedMetaData)
		if privData:
			self.file.seek(self.privOffset)
			assert self.file.tell() == self.privOffset
			self.file.write(privData)

	def _calcMasterChecksum(self):
		"""Calculate checkSumAdjustment."""
		tags = list(self.tables.keys())
		checksums = []
		for i in range(len(tags)):
			checksums.append(self.tables[tags[i]].checkSum)

		# Create a SFNT directory for checksum calculation purposes
		self.searchRange, self.entrySelector, self.rangeShift = getSearchRange(self.numTables, 16)
		directory = sstruct.pack(sfntDirectoryFormat, self)
		tables = sorted(self.tables.items())
		for tag, entry in tables:
			sfntEntry = SFNTDirectoryEntry()
			sfntEntry.tag = entry.tag
			sfntEntry.checkSum = entry.checkSum
			sfntEntry.offset = entry.origOffset
			sfntEntry.length = entry.origLength
			directory = directory + sfntEntry.toString()

		directory_end = sfntDirectorySize + len(self.tables) * sfntDirectoryEntrySize
		assert directory_end == len(directory)

		checksums.append(calcChecksum(directory))
		checksum = sum(checksums) & 0xffffffff
		# BiboAfba!
		checksumadjustment = (0xB1B0AFBA - checksum) & 0xffffffff
		return checksumadjustment

	def writeMasterChecksum(self):
		checksumadjustment = self._calcMasterChecksum()
		# write the checksum to the transformBuffer
		self.transformBuffer.seek(self.tables['head'].offset + 8)
		self.transformBuffer.write(struct.pack(">L", checksumadjustment))

# -- woff2 directory helpers and cruft

woff2DirectoryFormat = """
		> # big endian
		signature:           4s   # "wOF2"
		sfntVersion:         4s
		length:              L    # total woff2 file size
		numTables:           H    # number of tables
		reserved:            H    # set to 0
		totalSfntSize:       L    # uncompressed size
		totalCompressedSize: L    # compressed size
		majorVersion:        H    # major version of WOFF file
		minorVersion:        H    # minor version of WOFF file
		metaOffset:          L    # offset to metadata block
		metaLength:          L    # length of compressed metadata
		metaOrigLength:      L    # length of uncompressed metadata
		privOffset:          L    # offset to private data block
		privLength:          L    # length of private data block
"""

woff2DirectorySize = sstruct.calcsize(woff2DirectoryFormat)

woff2KnownTags = (
	"cmap", "head", "hhea", "hmtx", "maxp", "name", "OS/2", "post", "cvt ",
	"fpgm", "glyf", "loca", "prep", "CFF ", "VORG", "EBDT", "EBLC", "gasp",
	"hdmx", "kern", "LTSH", "PCLT", "VDMX", "vhea", "vmtx", "BASE", "GDEF",
	"GPOS", "GSUB", "EBSC", "JSTF", "MATH", "CBDT", "CBLC", "COLR", "CPAL",
	"SVG ", "sbix", "acnt", "avar", "bdat", "bloc", "bsln", "cvar", "fdsc",
	"feat", "fmtx", "fvar", "gvar", "hsty", "just", "lcar", "mort", "morx",
	"opbd", "prop", "trak", "Zapf", "Silf", "Glat", "Gloc", "Feat", "Sill")

woff2FlagsFormat = """
		> # big endian
		flags: B  # table type and flags
"""

woff2FlagsSize = sstruct.calcsize(woff2FlagsFormat)

woff2UnknownTagFormat = """
		> # big endian
		tag: 4s  # 4-byte tag (optional)
"""

woff2UnknownTagSize = sstruct.calcsize(woff2UnknownTagFormat)

woff2Base128MaxSize = 5
woff2DirectoryEntryMaxSize = woff2FlagsSize + woff2UnknownTagSize + 2 * woff2Base128MaxSize

woff2TransformedTableTags = ('glyf', 'loca')

woff2GlyfTableFormat = """
		> # big endian
		version:                  L  # = 0x00000000
		numGlyphs:                H  # Number of glyphs
		indexFormat:              H  # Offset format for loca table
		nContourStreamSize:       L  # Size of nContour stream
		nPointsStreamSize:        L  # Size of nPoints stream
		flagStreamSize:           L  # Size of flag stream
		glyphStreamSize:          L  # Size of glyph stream
		compositeStreamSize:      L  # Size of composite stream
		bboxStreamSize:           L  # Comnined size of bboxBitmap and bboxStream
		instructionStreamSize:    L  # Size of instruction stream
"""

woff2GlyfTableFormatSize = sstruct.calcsize(woff2GlyfTableFormat)

bboxFormat = """
		>	# big endian
		xMin:				h
		yMin:				h
		xMax:				h
		yMax:				h
"""


def getKnownTagIndex(tag):
	"""Return index of 'tag' in woff2KnownTags list. Return 63 if not found."""
	for i in range(len(woff2KnownTags)):
		if tag == woff2KnownTags[i]:
			return i
	return 0x3F


class WOFF2DirectoryEntry(DirectoryEntry):

	def fromFile(self, file):
		pos = file.tell()
		data = file.read(woff2DirectoryEntryMaxSize)
		left = self.fromString(data)
		consumed = len(data) - len(left)
		file.seek(pos + consumed)

	def fromString(self, data):
		dummy, data = sstruct.unpack2(woff2FlagsFormat, data, self)
		if self.flags & 0x3F == 0x3F:
			# if bits [0..5] of the flags byte == 63, read a 4-byte arbitrary tag value
			dummy, data = sstruct.unpack2(woff2UnknownTagFormat, data, self)
		else:
			# otherwise, tag is derived from a fixed 'Known Tags' table
			self.tag = woff2KnownTags[self.flags & 0x3F]
		self.tag = Tag(self.tag)
		if self.flags & 0xC0 != 0:
			raise TTLibError('bits 6-7 are reserved and must be 0')
		self.origLength, data = unpackBase128(data)
		self.length = self.origLength
		if self.tag in woff2TransformedTableTags:
			self.length, data = unpackBase128(data)
		# return left over data
		return data

	def toString(self):
		data = bytechr(self.flags)
		if (self.flags & 0x3f) == 0x3f:
			data += struct.pack('>4s', self.tag)
		data += packBase128(self.origLength)
		if self.tag in woff2TransformedTableTags:
			data += packBase128(self.length)
		return data


class WOFF2GlyfTable(getTableClass('glyf')):
	"""Decoder/encoder for WOFF2 'glyf' table transforms."""

	def __init__(self):
		self.tableTag = Tag('glyf')
		self.ttFont = TTFont(flavor="woff2", recalcBBoxes=False, padGlyphData=True)
		self.ttFont['head'] = getTableClass('head')()
		self.ttFont['maxp'] = getTableClass('maxp')()
		self.ttFont['loca'] = getTableClass('loca')()

	def reconstruct(self, transformedGlyfData):
		""" Convert transformed 'glyf' table data to SFNT 'glyf' table data.
		Decompile the resulting 'loca' table data.
		"""
		data = transformedGlyfData
		inputDataSize = len(data)

		dummy, data = sstruct.unpack2(woff2GlyfTableFormat, data, self)
		numGlyphs = self.numGlyphs
		substreamOffset = woff2GlyfTableFormatSize

		self.nContourStream = data[:self.nContourStreamSize]
		data = data[self.nContourStreamSize:]
		substreamOffset += self.nContourStreamSize

		self.nPointsStream = data[:self.nPointsStreamSize]
		data = data[self.nPointsStreamSize:]
		substreamOffset += self.nPointsStreamSize

		self.flagStream = data[:self.flagStreamSize]
		data = data[self.flagStreamSize:]
		substreamOffset += self.flagStreamSize

		self.glyphStream = data[:self.glyphStreamSize]
		data = data[self.glyphStreamSize:]
		substreamOffset += self.glyphStreamSize

		self.compositeStream = data[:self.compositeStreamSize]
		data = data[self.compositeStreamSize:]
		substreamOffset += self.compositeStreamSize

		combinedBboxStream = data[:self.bboxStreamSize]
		data = data[self.bboxStreamSize:]
		substreamOffset += self.bboxStreamSize

		self.instructionStream = data[:self.instructionStreamSize]
		data = data[self.instructionStreamSize:]
		substreamOffset += self.instructionStreamSize

		if substreamOffset != inputDataSize:
			raise TTLibError(
				"incorrect size of transformed 'glyf' table: expected %d, received %d bytes"
				% (substreamOffset, inputDataSize))

		bboxBitmapSize = ((numGlyphs + 31) >> 5) << 2
		bboxBitmap = combinedBboxStream[:bboxBitmapSize]
		self.bboxBitmap = array.array('B', bboxBitmap)
		self.bboxStream = combinedBboxStream[bboxBitmapSize:]

		self.nContourStream = array.array("h", self.nContourStream)
		if sys.byteorder != "big":
			self.nContourStream.byteswap()
		assert len(self.nContourStream) == numGlyphs

		self.glyphOrder = glyphOrder = []
		for glyphID in range(numGlyphs):
			glyphName = "glyph%d" % glyphID
			glyphOrder.append(glyphName)
		self.ttFont.setGlyphOrder(glyphOrder)

		self.glyphs = {}
		for glyphID, glyphName in enumerate(glyphOrder):
			glyph = self._decodeGlyph(glyphID)
			self.glyphs[glyphName] = glyph

		glyfData = self.compile(self.ttFont)
		return glyfData

	def _decodeGlyph(self, glyphID):
		glyph = getTableModule('glyf').Glyph()
		glyph.numberOfContours = self.nContourStream[glyphID]
		if glyph.numberOfContours == 0:
			return glyph
		elif glyph.isComposite():
			self._decodeComponents(glyph)
		else:
			self._decodeCoordinates(glyph)
		self._decodeBBox(glyphID, glyph)
		return glyph

	def _decodeComponents(self, glyph):
		data = self.compositeStream
		glyph.components = []
		more = 1
		haveInstructions = 0
		while more:
			component = getTableModule('glyf').GlyphComponent()
			more, haveInstr, data = component.decompile(data, self)
			haveInstructions = haveInstructions | haveInstr
			glyph.components.append(component)
		self.compositeStream = data
		if haveInstructions:
			self._decodeInstructions(glyph)

	def _decodeCoordinates(self, glyph):
		data = self.nPointsStream
		endPtsOfContours = []
		endPoint = -1
		for i in range(glyph.numberOfContours):
			ptsOfContour, data = unpack255UShort(data)
			endPoint += ptsOfContour
			endPtsOfContours.append(endPoint)
		glyph.endPtsOfContours = endPtsOfContours
		self.nPointsStream = data
		self._decodeTriplets(glyph)
		self._decodeInstructions(glyph)

	def _decodeInstructions(self, glyph):
		glyphStream = self.glyphStream
		instructionStream = self.instructionStream
		instructionLength, glyphStream = unpack255UShort(glyphStream)
		glyph.program = ttProgram.Program()
		glyph.program.fromBytecode(instructionStream[:instructionLength])
		self.glyphStream = glyphStream
		self.instructionStream = instructionStream[instructionLength:]

	def _decodeBBox(self, glyphID, glyph):
		haveBBox = bool(self.bboxBitmap[glyphID >> 3] & (0x80 >> (glyphID & 7)))
		if glyph.isComposite() and not haveBBox:
			raise TTLibError('no bbox values for composite glyph %d' % glyphID)
		if haveBBox:
			dummy, self.bboxStream = sstruct.unpack2(bboxFormat, self.bboxStream, glyph)
		else:
			glyph.recalcBounds(self)

	def _decodeTriplets(self, glyph):

		def withSign(flag, baseval):
			assert 0 <= baseval and baseval < 65536, 'integer overflow'
			return baseval if flag & 1 else -baseval

		nPoints = glyph.endPtsOfContours[-1] + 1
		flagSize = nPoints
		if flagSize > len(self.flagStream):
			raise TTLibError("not enough 'flagStream' data")
		flagsData = self.flagStream[:flagSize]
		self.flagStream = self.flagStream[flagSize:]
		flags = array.array('B', flagsData)

		triplets = array.array('B', self.glyphStream)
		nTriplets = len(triplets)
		assert nPoints <= nTriplets

		x = 0
		y = 0
		glyph.coordinates = getTableModule('glyf').GlyphCoordinates.zeros(nPoints)
		glyph.flags = array.array("B")
		tripletIndex = 0
		for i in range(nPoints):
			flag = flags[i]
			onCurve = not bool(flag >> 7)
			flag &= 0x7f
			if flag < 84:
				nBytes = 1
			elif flag < 120:
				nBytes = 2
			elif flag < 124:
				nBytes = 3
			else:
				nBytes = 4
			assert ((tripletIndex + nBytes) <= nTriplets)
			if flag < 10:
				dx = 0
				dy = withSign(flag, ((flag & 14) << 7) + triplets[tripletIndex])
			elif flag < 20:
				dx = withSign(flag, (((flag - 10) & 14) << 7) + triplets[tripletIndex])
				dy = 0
			elif flag < 84:
				b0 = flag - 20
				b1 = triplets[tripletIndex]
				dx = withSign(flag, 1 + (b0 & 0x30) + (b1 >> 4))
				dy = withSign(flag >> 1, 1 + ((b0 & 0x0c) << 2) + (b1 & 0x0f))
			elif flag < 120:
				b0 = flag - 84
				dx = withSign(flag, 1 + ((b0 // 12) << 8) + triplets[tripletIndex])
				dy = withSign(flag >> 1,
					1 + (((b0 % 12) >> 2) << 8) + triplets[tripletIndex + 1])
			elif flag < 124:
				b2 = triplets[tripletIndex + 1]
				dx = withSign(flag, (triplets[tripletIndex] << 4) + (b2 >> 4))
				dy = withSign(flag >> 1,
					((b2 & 0x0f) << 8) + triplets[tripletIndex + 2])
			else:
				dx = withSign(flag,
					(triplets[tripletIndex] << 8) + triplets[tripletIndex + 1])
				dy = withSign(flag >> 1,
					(triplets[tripletIndex + 2] << 8) + triplets[tripletIndex + 3])
			tripletIndex += nBytes
			x += dx
			y += dy
			glyph.coordinates[i] = (x, y)
			glyph.flags.append(int(onCurve))
		bytesConsumed = tripletIndex
		self.glyphStream = self.glyphStream[bytesConsumed:]

	def getLocaData(self):
		""" Return compiled 'loca' table data (must be run after 'reconstruct'
		method).
		"""
		locaTable = self.ttFont['loca']
		locaData = locaTable.compile(self.ttFont)
		origIndexFormat = self.indexFormat
		currIndexFormat = self.ttFont['head'].indexToLocFormat
		if currIndexFormat != origIndexFormat:
			raise TTLibError(
				"reconstructed 'loca' table has wrong index format: expected %d, found %d"
				% (origIndexFormat, currIndexFormat))
		return locaData

	def setLocaData(self, locaData, indexFormat, numGlyphs):
		""" Decompile 'loca' table data using the specified 'indexFormat' and
		'numGlyphs' (must be run before 'transform' method).
		"""
		self.indexFormat = self.ttFont['head'].indexToLocFormat = indexFormat
		self.numGlyphs = self.ttFont['maxp'].numGlyphs = numGlyphs
		self.ttFont['loca'].decompile(locaData, self.ttFont)

	def transform(self, glyfData):
		""" Convert the SFNT 'glyf' table data to WOFF2 transformed 'glyf' data. """
		glyphOrder = ["glyph%d" % i for i in range(self.numGlyphs)]
		self.ttFont.setGlyphOrder(glyphOrder)
		self.ttFont.lazy = False

		self.decompile(glyfData, self.ttFont)

		self.nContourStream = b""
		self.nPointsStream = b""
		self.flagStream = b""
		self.glyphStream = b""
		self.compositeStream = b""
		self.bboxStream = b""
		self.instructionStream = b""
		bboxBitmapSize = ((self.numGlyphs + 31) >> 5) << 2
		self.bboxBitmap = array.array('B', [0]*bboxBitmapSize)

		for glyphID in range(self.numGlyphs):
			self._encodeGlyph(glyphID)

		self.bboxStream = self.bboxBitmap.tostring() + self.bboxStream

		self.version = 0

		self.nContourStreamSize = len(self.nContourStream)
		self.nPointsStreamSize = len(self.nPointsStream)
		self.flagStreamSize = len(self.flagStream)
		self.glyphStreamSize = len(self.glyphStream)
		self.compositeStreamSize = len(self.compositeStream)
		self.bboxStreamSize = len(self.bboxStream)
		self.instructionStreamSize = len(self.instructionStream)

		transfomedGlyfData = sstruct.pack(woff2GlyfTableFormat, self) + \
			self.nContourStream + self.nPointsStream + self.flagStream + \
			self.glyphStream + self.compositeStream + self.bboxStream + \
			self.instructionStream
		return transfomedGlyfData

	def _encodeGlyph(self, glyphID):
		glyphName = self.getGlyphName(glyphID)
		glyph = self.glyphs[glyphName]
		self.nContourStream += struct.pack(">h", glyph.numberOfContours)
		if glyph.numberOfContours == 0:
			return
		elif glyph.isComposite():
			self._encodeComponents(glyph)
		else:
			self._encodeCoordinates(glyph)
		self._encodeBBox(glyphID, glyph)

	def _encodeComponents(self, glyph):
		lastcomponent = len(glyph.components) - 1
		more = 1
		haveInstructions = 0
		for i in range(len(glyph.components)):
			if i == lastcomponent:
				haveInstructions = hasattr(glyph, "program")
				more = 0
			component = glyph.components[i]
			self.compositeStream += component.compile(more, haveInstructions, self)
		if haveInstructions:
			self._encodeInstructions(glyph)

	def _encodeCoordinates(self, glyph):
		lastEndPoint = -1
		for endPoint in glyph.endPtsOfContours:
			ptsOfContour = endPoint - lastEndPoint
			self.nPointsStream += pack255UShort(ptsOfContour)
			lastEndPoint = endPoint
		self._encodeTriplets(glyph)
		self._encodeInstructions(glyph)

	def _encodeInstructions(self, glyph):
		instructions = glyph.program.getBytecode()
		self.glyphStream += pack255UShort(len(instructions))
		self.instructionStream += instructions

	def _encodeBBox(self, glyphID, glyph):
		if glyph.isComposite():
			self.bboxBitmap[glyphID >> 3] |= 0x80 >> (glyphID & 7)
			self.bboxStream += sstruct.pack(bboxFormat, glyph)
		else:
			assert glyph.numberOfContours > 0
			glyphBBox = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
			if glyphBBox != calcIntBounds(glyph.coordinates):
				raise TTLibError(
					"glyph %d bounding box doesn't match calculated value" % glyphID)

	def _encodeTriplets(self, glyph):
		assert len(glyph.coordinates) == len(glyph.flags)
		coordinates = glyph.coordinates.copy()
		coordinates.absoluteToRelative()

		flags = array.array('B')
		triplets = array.array('B')
		for i in range(len(coordinates)):
			onCurve = glyph.flags[i]
			x, y = coordinates[i]
			absX = abs(x)
			absY = abs(y)
			onCurveBit = 0 if onCurve else 128
			xSignBit = 0 if (x < 0) else 1
			ySignBit = 0 if (y < 0) else 1
			xySignBits = xSignBit + 2 * ySignBit

			if x == 0 and absY < 1280:
				flags.append(onCurveBit + ((absY & 0xf00) >> 7) + ySignBit)
				triplets.append(absY & 0xff)
			elif y == 0 and absX < 1280:
				flags.append(onCurveBit + 10 + ((absX & 0xf00) >> 7) + xSignBit)
				triplets.append(absX & 0xff)
			elif absX < 65 and absY < 65:
				flags.append(onCurveBit + 20 + ((absX - 1) & 0x30) + (((absY - 1) & 0x30) >> 2) + xySignBits)
				triplets.append((((absX - 1) & 0xf) << 4) | ((absY - 1) & 0xf))
			elif absX < 769 and absY < 769:
				flags.append(onCurveBit + 84 + 12 * (((absX - 1) & 0x300) >> 8) + (((absY - 1) & 0x300) >> 6) + xySignBits)
				triplets.append((absX - 1) & 0xff)
				triplets.append((absY - 1) & 0xff)
			elif absX < 4096 and absY < 4096:
				flags.append(onCurveBit + 120 + xySignBits)
				triplets.append(absX >> 4)
				triplets.append(((absX & 0xf) << 4) | (absY >> 8))
				triplets.append(absY & 0xff)
			else:
				flags.append(onCurveBit + 124 + xySignBits)
				triplets.append(absX >> 8)
				triplets.append(absX & 0xff)
				triplets.append(absY >> 8)
				triplets.append(absY & 0xff)

		self.flagStream += flags.tostring()
		self.glyphStream += triplets.tostring()


class WOFF2FlavorData(WOFFFlavorData):

	Flavor = 'woff2'

	def __init__(self, reader=None):
		self.majorVersion = None
		self.minorVersion = None
		self.metaData = None
		self.privData = None
		if reader:
			self.majorVersion = reader.majorVersion
			self.minorVersion = reader.minorVersion
			if reader.metaLength:
				reader.file.seek(reader.metaOffset)
				rawData = reader.file.read(reader.metaLength)
				assert len(rawData) == reader.metaLength
				import brotli
				data = brotli.decompress(rawData)
				assert len(data) == reader.metaOrigLength
				self.metaData = data
			if reader.privLength:
				reader.file.seek(reader.privOffset)
				data = reader.file.read(reader.privLength)
				assert len(data) == reader.privLength
				self.privData = data


def unpackBase128(data):
	""" A UIntBase128 encoded number is a sequence of bytes for which the most
	significant bit is set for all but the last byte, and clear for the last byte.
	The number itself is base 128 encoded in the lower 7 bits of each byte.
	"""
	result = 0
	for i in range(5):
		if len(data) == 0:
			raise TTLibError('not enough data to unpack UIntBase128')
		code = byteord(data[0])
		data = data[1:]
		# if any of the top seven bits are set then we're about to overflow
		if result & 0xFE000000:
			raise TTLibError('UIntBase128 value exceeds 2**32-1')
		# set current value = old value times 128 bitwise-or (byte bitwise-and 127)
		result = (result << 7) | (code & 0x7f)
		# repeat until the most significant bit of byte is false
		if (code & 0x80) == 0:
			# return result plus left over data
			return result, data
	# make sure not to exceed the size bound
	raise TTLibError('UIntBase128-encoded sequence is longer than 5 bytes')

def base128Size(n):
	size = 1
	while n >= 128:
		size += 1
		n >>= 7
	return size

def packBase128(n):
	data = b''
	size = base128Size(n)
	for i in range(size):
		b = (n >> (7 * (size - i - 1))) & 0x7f
		if i < size - 1:
			b |= 0x80
		data += struct.pack('B', b)
	return data

def unpack255UShort(data):
	"""Based on MicroType Express specification, section 6.1.1."""
	code = byteord(data[:1])
	data = data[1:]
	if code == 253:
		# read two more bytes as an unsigned short
		result, = struct.unpack(">H", data[:2])
		data = data[2:]
	elif code == 254:
		# read another byte, plus 253 * 2
		result = byteord(data[:1])
		result += 506
		data = data[1:]
	elif code == 255:
		# read another byte, plus 253
		result = byteord(data[:1])
		result += 253
		data = data[1:]
	else:
		# leave as is if lower than 253
		result = code
	# return result plus left over data
	return result, data

def pack255UShort(value):
	if value < 253:
		return struct.pack(">B", value)
	elif value < 506:
		return struct.pack(">BB", 255, value - 253)
	elif value < 762:
		return struct.pack(">BB", 254, value - 506)
	else:
		return struct.pack(">BH", 253, value)

def padData(data):
	length = len(data)
	paddedLength = (length + 3) & ~3
	paddedData = data + b"\0" * (paddedLength - length)
	return paddedData
