"""ttLib/sfnt.py -- low-level module to deal with the sfnt file format.

Defines two public classes:
	SFNTReader
	SFNTWriter

(Normally you don't have to use these classes explicitly; they are 
used automatically by ttLib.TTFont.)

The reading and writing of sfnt files is separated in two distinct 
classes, since whenever to number of tables changes or whenever
a table's length chages you need to rewrite the whole file anyway.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
import struct


class SFNTReader(object):
	
	def __init__(self, file, checkChecksums=1, fontNumber=-1):
		self.file = file
		self.checkChecksums = checkChecksums

		self.flavor = None
		self.flavorData = None
		self.DirectoryEntry = SFNTDirectoryEntry
		self.sfntVersion = self.file.read(4)
		self.file.seek(0)
		if self.sfntVersion == b"ttcf":
			sstruct.unpack(ttcHeaderFormat, self.file.read(ttcHeaderSize), self)
			assert self.Version == 0x00010000 or self.Version == 0x00020000, "unrecognized TTC version 0x%08x" % self.Version
			if not 0 <= fontNumber < self.numFonts:
				from fontTools import ttLib
				raise ttLib.TTLibError("specify a font number between 0 and %d (inclusive)" % (self.numFonts - 1))
			offsetTable = struct.unpack(">%dL" % self.numFonts, self.file.read(self.numFonts * 4))
			if self.Version == 0x00020000:
				pass # ignoring version 2.0 signatures
			self.file.seek(offsetTable[fontNumber])
			sstruct.unpack(sfntDirectoryFormat, self.file.read(sfntDirectorySize), self)
		elif self.sfntVersion == b"wOFF":
			self.flavor = "woff"
			self.DirectoryEntry = WOFFDirectoryEntry
			sstruct.unpack(woffDirectoryFormat, self.file.read(woffDirectorySize), self)
		else:
			sstruct.unpack(sfntDirectoryFormat, self.file.read(sfntDirectorySize), self)
		self.sfntVersion = Tag(self.sfntVersion)

		if self.sfntVersion not in ("\x00\x01\x00\x00", "OTTO", "true"):
			from fontTools import ttLib
			raise ttLib.TTLibError("Not a TrueType or OpenType font (bad sfntVersion)")
		self.tables = {}
		for i in range(self.numTables):
			entry = self.DirectoryEntry()
			entry.fromFile(self.file)
			self.tables[Tag(entry.tag)] = entry

		# Load flavor data if any
		if self.flavor == "woff":
			self.flavorData = WOFFFlavorData(self)

	def has_key(self, tag):
		return tag in self.tables

	__contains__ = has_key
	
	def keys(self):
		return self.tables.keys()
	
	def __getitem__(self, tag):
		"""Fetch the raw table data."""
		entry = self.tables[Tag(tag)]
		data = entry.loadData (self.file)
		if self.checkChecksums:
			if tag == 'head':
				# Beh: we have to special-case the 'head' table.
				checksum = calcChecksum(data[:8] + b'\0\0\0\0' + data[12:])
			else:
				checksum = calcChecksum(data)
			if self.checkChecksums > 1:
				# Be obnoxious, and barf when it's wrong
				assert checksum == entry.checksum, "bad checksum for '%s' table" % tag
			elif checksum != entry.checkSum:
				# Be friendly, and just print a warning.
				print("bad checksum for '%s' table" % tag)
		return data
	
	def __delitem__(self, tag):
		del self.tables[Tag(tag)]
	
	def close(self):
		self.file.close()


class SFNTWriter(object):
	
	def __init__(self, file, numTables, sfntVersion="\000\001\000\000",
		     flavor=None, flavorData=None):
		self.file = file
		self.numTables = numTables
		self.sfntVersion = Tag(sfntVersion)
		self.flavor = flavor
		self.flavorData = flavorData

		if self.flavor == "woff":
			self.directoryFormat = woffDirectoryFormat
			self.directorySize = woffDirectorySize
			self.DirectoryEntry = WOFFDirectoryEntry

			self.signature = "wOFF"
		else:
			assert not self.flavor,  "Unknown flavor '%s'" % self.flavor
			self.directoryFormat = sfntDirectoryFormat
			self.directorySize = sfntDirectorySize
			self.DirectoryEntry = SFNTDirectoryEntry

			self.searchRange, self.entrySelector, self.rangeShift = getSearchRange(numTables)

		self.nextTableOffset = self.directorySize + numTables * self.DirectoryEntry.formatSize
		# clear out directory area
		self.file.seek(self.nextTableOffset)
		# make sure we're actually where we want to be. (old cStringIO bug)
		self.file.write(b'\0' * (self.nextTableOffset - self.file.tell()))
		self.tables = {}
	
	def __setitem__(self, tag, data):
		"""Write raw table data to disk."""
		reuse = False
		if tag in self.tables:
			# We've written this table to file before. If the length
			# of the data is still the same, we allow overwriting it.
			entry = self.tables[tag]
			assert not hasattr(entry.__class__, 'encodeData')
			if len(data) != entry.length:
				from fontTools import ttLib
				raise ttLib.TTLibError("cannot rewrite '%s' table: length does not match directory entry" % tag)
			reuse = True
		else:
			entry = self.DirectoryEntry()
			entry.tag = tag

		if tag == 'head':
			entry.checkSum = calcChecksum(data[:8] + b'\0\0\0\0' + data[12:])
			self.headTable = data
			entry.uncompressed = True
		else:
			entry.checkSum = calcChecksum(data)

		entry.offset = self.nextTableOffset
		entry.saveData (self.file, data)

		if not reuse:
			self.nextTableOffset = self.nextTableOffset + ((entry.length + 3) & ~3)

		# Add NUL bytes to pad the table data to a 4-byte boundary.
		# Don't depend on f.seek() as we need to add the padding even if no
		# subsequent write follows (seek is lazy), ie. after the final table
		# in the font.
		self.file.write(b'\0' * (self.nextTableOffset - self.file.tell()))
		assert self.nextTableOffset == self.file.tell()
		
		self.tables[tag] = entry
	
	def close(self):
		"""All tables must have been written to disk. Now write the
		directory.
		"""
		tables = sorted(self.tables.items())
		if len(tables) != self.numTables:
			from fontTools import ttLib
			raise ttLib.TTLibError("wrong number of tables; expected %d, found %d" % (self.numTables, len(tables)))

		if self.flavor == "woff":
			self.signature = b"wOFF"
			self.reserved = 0

			self.totalSfntSize = 12
			self.totalSfntSize += 16 * len(tables)
			for tag, entry in tables:
				self.totalSfntSize += (entry.origLength + 3) & ~3

			data = self.flavorData if self.flavorData else WOFFFlavorData()
			if data.majorVersion is not None and data.minorVersion is not None:
				self.majorVersion = data.majorVersion
				self.minorVersion = data.minorVersion
			else:
				if hasattr(self, 'headTable'):
					self.majorVersion, self.minorVersion = struct.unpack(">HH", self.headTable[4:8])
				else:
					self.majorVersion = self.minorVersion = 0
			if data.metaData:
				self.metaOrigLength = len(data.metaData)
				self.file.seek(0,2)
				self.metaOffset = self.file.tell()
				import zlib
				compressedMetaData = zlib.compress(data.metaData)
				self.metaLength = len(compressedMetaData)
				self.file.write(compressedMetaData)
			else:
				self.metaOffset = self.metaLength = self.metaOrigLength = 0
			if data.privData:
				self.file.seek(0,2)
				off = self.file.tell()
				paddedOff = (off + 3) & ~3
				self.file.write('\0' * (paddedOff - off))
				self.privOffset = self.file.tell()
				self.privLength = len(data.privData)
				self.file.write(data.privData)
			else:
				self.privOffset = self.privLength = 0

			self.file.seek(0,2)
			self.length = self.file.tell()

		else:
			assert not self.flavor,  "Unknown flavor '%s'" % self.flavor
			pass
		
		directory = sstruct.pack(self.directoryFormat, self)
		
		self.file.seek(self.directorySize)
		seenHead = 0
		for tag, entry in tables:
			if tag == "head":
				seenHead = 1
			directory = directory + entry.toString()
		if seenHead:
			self.writeMasterChecksum(directory)
		self.file.seek(0)
		self.file.write(directory)

	def _calcMasterChecksum(self, directory):
		# calculate checkSumAdjustment
		tags = list(self.tables.keys())
		checksums = []
		for i in range(len(tags)):
			checksums.append(self.tables[tags[i]].checkSum)

		# TODO(behdad) I'm fairly sure the checksum for woff is not working correctly.
		# Haven't debugged.
		if self.DirectoryEntry != SFNTDirectoryEntry:
			# Create a SFNT directory for checksum calculation purposes
			self.searchRange, self.entrySelector, self.rangeShift = getSearchRange(self.numTables)
			directory = sstruct.pack(sfntDirectoryFormat, self)
			tables = sorted(self.tables.items())
			for tag, entry in tables:
				sfntEntry = SFNTDirectoryEntry()
				for item in ['tag', 'checkSum', 'offset', 'length']:
					setattr(sfntEntry, item, getattr(entry, item))
				directory = directory + sfntEntry.toString()

		directory_end = sfntDirectorySize + len(self.tables) * sfntDirectoryEntrySize
		assert directory_end == len(directory)

		checksums.append(calcChecksum(directory))
		checksum = sum(checksums) & 0xffffffff
		# BiboAfba!
		checksumadjustment = (0xB1B0AFBA - checksum) & 0xffffffff
		return checksumadjustment

	def writeMasterChecksum(self, directory):
		checksumadjustment = self._calcMasterChecksum(directory)
		# write the checksum to the file
		self.file.seek(self.tables['head'].offset + 8)
		self.file.write(struct.pack(">L", checksumadjustment))


# -- sfnt directory helpers and cruft

ttcHeaderFormat = """
		> # big endian
		TTCTag:                  4s # "ttcf"
		Version:                 L  # 0x00010000 or 0x00020000
		numFonts:                L  # number of fonts
		# OffsetTable[numFonts]: L  # array with offsets from beginning of file
		# ulDsigTag:             L  # version 2.0 only
		# ulDsigLength:          L  # version 2.0 only
		# ulDsigOffset:          L  # version 2.0 only
"""

ttcHeaderSize = sstruct.calcsize(ttcHeaderFormat)

sfntDirectoryFormat = """
		> # big endian
		sfntVersion:    4s
		numTables:      H    # number of tables
		searchRange:    H    # (max2 <= numTables)*16
		entrySelector:  H    # log2(max2 <= numTables)
		rangeShift:     H    # numTables*16-searchRange
"""

sfntDirectorySize = sstruct.calcsize(sfntDirectoryFormat)

sfntDirectoryEntryFormat = """
		> # big endian
		tag:            4s
		checkSum:       L
		offset:         L
		length:         L
"""

sfntDirectoryEntrySize = sstruct.calcsize(sfntDirectoryEntryFormat)

woffDirectoryFormat = """
		> # big endian
		signature:      4s   # "wOFF"
		sfntVersion:    4s
		length:         L    # total woff file size
		numTables:      H    # number of tables
		reserved:       H    # set to 0
		totalSfntSize:  L    # uncompressed size
		majorVersion:   H    # major version of WOFF file
		minorVersion:   H    # minor version of WOFF file
		metaOffset:     L    # offset to metadata block
		metaLength:     L    # length of compressed metadata
		metaOrigLength: L    # length of uncompressed metadata
		privOffset:     L    # offset to private data block
		privLength:     L    # length of private data block
"""

woffDirectorySize = sstruct.calcsize(woffDirectoryFormat)

woffDirectoryEntryFormat = """
		> # big endian
		tag:            4s
		offset:         L
		length:         L    # compressed length
		origLength:     L    # original length
		checkSum:       L    # original checksum
"""

woffDirectoryEntrySize = sstruct.calcsize(woffDirectoryEntryFormat)


class DirectoryEntry(object):
	
	def __init__(self):
		self.uncompressed = False # if True, always embed entry raw

	def fromFile(self, file):
		sstruct.unpack(self.format, file.read(self.formatSize), self)
	
	def fromString(self, str):
		sstruct.unpack(self.format, str, self)
	
	def toString(self):
		return sstruct.pack(self.format, self)
	
	def __repr__(self):
		if hasattr(self, "tag"):
			return "<%s '%s' at %x>" % (self.__class__.__name__, self.tag, id(self))
		else:
			return "<%s at %x>" % (self.__class__.__name__, id(self))

	def loadData(self, file):
		file.seek(self.offset)
		data = file.read(self.length)
		assert len(data) == self.length
		if hasattr(self.__class__, 'decodeData'):
			data = self.decodeData(data)
		return data

	def saveData(self, file, data):
		if hasattr(self.__class__, 'encodeData'):
			data = self.encodeData(data)
		self.length = len(data)
		file.seek(self.offset)
		file.write(data)

	def decodeData(self, rawData):
		return rawData

	def encodeData(self, data):
		return data

class SFNTDirectoryEntry(DirectoryEntry):

	format = sfntDirectoryEntryFormat
	formatSize = sfntDirectoryEntrySize

class WOFFDirectoryEntry(DirectoryEntry):

	format = woffDirectoryEntryFormat
	formatSize = woffDirectoryEntrySize
	zlibCompressionLevel = 6

	def decodeData(self, rawData):
		import zlib
		if self.length == self.origLength:
			data = rawData
		else:
			assert self.length < self.origLength
			data = zlib.decompress(rawData)
			assert len (data) == self.origLength
		return data

	def encodeData(self, data):
		import zlib
		self.origLength = len(data)
		if not self.uncompressed:
			compressedData = zlib.compress(data, self.zlibCompressionLevel)
		if self.uncompressed or len(compressedData) >= self.origLength:
			# Encode uncompressed
			rawData = data
			self.length = self.origLength
		else:
			rawData = compressedData
			self.length = len(rawData)
		return rawData

class WOFFFlavorData():

	Flavor = 'woff'

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
				import zlib
				data = zlib.decompress(rawData)
				assert len(data) == reader.metaOrigLength
				self.metaData = data
			if reader.privLength:
				reader.file.seek(reader.privOffset)
				data = reader.file.read(reader.privLength)
				assert len(data) == reader.privLength
				self.privData = data


def calcChecksum(data):
	"""Calculate the checksum for an arbitrary block of data.
	Optionally takes a 'start' argument, which allows you to
	calculate a checksum in chunks by feeding it a previous
	result.
	
	If the data length is not a multiple of four, it assumes
	it is to be padded with null byte. 

		>>> print calcChecksum(b"abcd")
		1633837924
		>>> print calcChecksum(b"abcdxyz")
		3655064932
	"""
	remainder = len(data) % 4
	if remainder:
		data += b"\0" * (4 - remainder)
	value = 0
	blockSize = 4096
	assert blockSize % 4 == 0
	for i in range(0, len(data), blockSize):
		block = data[i:i+blockSize]
		longs = struct.unpack(">%dL" % (len(block) // 4), block)
		value = (value + sum(longs)) & 0xffffffff
	return value


def maxPowerOfTwo(x):
	"""Return the highest exponent of two, so that
	(2 ** exponent) <= x
	"""
	exponent = 0
	while x:
		x = x >> 1
		exponent = exponent + 1
	return max(exponent - 1, 0)


def getSearchRange(n):
	"""Calculate searchRange, entrySelector, rangeShift for the
	sfnt directory. 'n' is the number of tables.
	"""
	# This stuff needs to be stored in the file, because?
	exponent = maxPowerOfTwo(n)
	searchRange = (2 ** exponent) * 16
	entrySelector = exponent
	rangeShift = n * 16 - searchRange
	return searchRange, entrySelector, rangeShift


if __name__ == "__main__":
    import doctest
    doctest.testmod()
