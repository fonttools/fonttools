from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import fixedToFloat
from fontTools.misc.textTools import safeEval
from . import DefaultTable
import array
import sys
import struct

# Apple's documentation of 'gvar':
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
#
# TrueType source code for parsing 'gvar':
# http://git.savannah.gnu.org/cgit/freetype/freetype2.git/tree/src/truetype/ttgxvar.c

gvarHeaderFormat = b"""
	> # big endian
	version:		H
	reserved:		H
	axisCount:		H
	sharedCoordCount:	H
	offsetToCoord:		I
	glyphCount:		H
	flags:			H
	offsetToData:		I
"""

gvarItemFormat = b"""
	> # big endian
	tupleCount:	H
	offsetToData:	H
"""

GVAR_HEADER_SIZE = sstruct.calcsize(gvarHeaderFormat)
gvarItemSize = sstruct.calcsize(gvarItemFormat)

TUPLES_SHARE_POINT_NUMBERS = 0x8000
TUPLE_COUNT_MASK = 0x0fff

EMBEDDED_TUPLE_COORD = 0x8000
INTERMEDIATE_TUPLE = 0x4000
PRIVATE_POINT_NUMBERS = 0x2000
TUPLE_INDEX_MASK = 0x0fff

class table__g_v_a_r(DefaultTable.DefaultTable):

	dependencies = ["fvar", "glyf"]

	def decompile(self, data, ttFont):
		axisTags = [axis.AxisTag for axis in ttFont['fvar'].table.VariationAxis]
		glyphs = ttFont.getGlyphOrder()
		sstruct.unpack(gvarHeaderFormat, data[0:GVAR_HEADER_SIZE], self)
		assert len(glyphs) == self.glyphCount
		assert len(axisTags) == self.axisCount
		offsets = self.decompileOffsets_(data)
		sharedCoords = self.decompileSharedCoords_(axisTags, data)
		self.variations = {}
		for i in range(self.glyphCount):
			glyphName = glyphs[i]
			glyph = ttFont["glyf"][glyphName]
			if glyph.isComposite():
				numPoints = len(glyph.components) + 4
			else:
				# Empty glyphs (eg. space, nonmarkingreturn) have no "coordinates" attribute.
				numPoints = len(getattr(glyph, "coordinates", [])) + 4
			gvarData = data[self.offsetToData + offsets[i] : self.offsetToData + offsets[i + 1]]
			self.variations[glyphName] = self.decompileVariations_(numPoints, sharedCoords, axisTags, gvarData)

	def decompileSharedCoords_(self, axisTags, data):
		result = []
		pos = self.offsetToCoord
		stride = len(axisTags) * 2
		for i in range(self.sharedCoordCount):
			coord = self.decompileCoord_(axisTags, data[pos:pos+stride])
			result.append(coord)
			pos += stride
		return result

	@staticmethod
	def decompileCoord_(axisTags, data):
		coord = {}
		pos = 0
		for axis in axisTags:
			coord[axis] = fixedToFloat(struct.unpack(b">h", data[pos:pos+2])[0], 14)
			pos += 2
		return coord

	def decompileOffsets_(self, data):
		if (self.flags & 1) == 0:
			# Short format: array of UInt16
			offsets = array.array("H")
			offsetsSize = (self.glyphCount + 1) * 2
		else:
			# Long format: array of UInt32
			offsets = array.array("I")
			offsetsSize = (self.glyphCount + 1) * 4
		offsetsData = data[GVAR_HEADER_SIZE : GVAR_HEADER_SIZE + offsetsSize]
		offsets.fromstring(offsetsData)
		if sys.byteorder != "big":
			offsets.byteswap()

		# In the short format, offsets need to be multiplied by 2.
		# This is not documented in Apple's TrueType specification,
		# but can be inferred from the FreeType implementation, and
		# we could verify it with two sample GX fonts.
		if (self.flags & 1) == 0:
			offsets = [off * 2 for off in offsets]

		return offsets

	def decompileVariations_(self, numPoints, sharedCoords, axisTags, data):
		if len(data) < 4:
			return []
		tupleCount, offsetToData = struct.unpack(b">HH", data[:4])
		tuplesSharePointNumbers = (tupleCount & TUPLES_SHARE_POINT_NUMBERS) != 0
		tupleCount = tupleCount & TUPLE_COUNT_MASK
		tuplePos = 4
		dataPos = offsetToData
		for i in range(tupleCount):
			tupleSize, tupleIndex = struct.unpack(b">HH", data[tuplePos:tuplePos+4])
			if (tupleIndex & EMBEDDED_TUPLE_COORD) != 0:
				print('****** %d ' % (tupleIndex & TUPLE_INDEX_MASK))
				print(' '.join(x.encode('hex') for x in data))
				coord = self.decompileCoord_(axisTags, data[tuplePos+4:])
			else:
				pass #coord = sharedCoords[tupleIndex & TUPLE_INDEX_MASK].copy()
			tuplePos += self.getTupleSize(tupleIndex)
		return []

									     
									     
	# -------------------- from here comes junk ---------------------------------------------------
	# TODO: Remove glyphName argument, it is just for debugging.
	def OBSOLETE_decompileGlyphVariation(self, glyphName, sharedCoords, data):
		tracing = False or (glyphName == 'I')
		if tracing: print(' '.join(x.encode('hex') for x in data))
		if len(data) == 0:
			return []
		result = []
		tupleCount, offsetToData = struct.unpack(b">HH", data[:4])
		tuplesSharePointNumbers = (tupleCount & 0x8000) != 0
		tupleCount = tupleCount & 0xfff
		pos = 4
		dataPos = offsetToData
		if tracing: print('tuplesSharePointNumbers=%s' % tuplesSharePointNumbers)
		for i in range(tupleCount):
			tupleSize, tupleIndex = struct.unpack(b">HH", data[pos:pos+4])
			if (tupleIndex & kEmbeddedTupleCoord) != 0:
				coord = None  # TODO: Implement
			else:
				coord = sharedCoords[tupleIndex & kTupleIndexMask].copy()
			if tracing:
				print('Tuple %d: pos=%d, tupleSize=%04x, byteSize=%d, index=%04x' % (i, pos, tupleSize, self.getTupleSize(tupleSize), tupleIndex))
			tupleData = buffer(data, dataPos, tupleSize)
			tuple = self.decompileTupleData(tuplesSharePointNumbers, coord, tupleData)
			result.append(tuple)
			pos += self.getTupleSize(tupleIndex)
			dataPos += tupleSize
		print(result)
		return result

	def OBSOLETE_decompileTupleData(self, tuplesSharePointNumbers, coord, data):
		#print("    tuplesSharePointNumbers: %s" % tuplesSharePointNumbers)
		#print("    tupleData: %s" % ' '.join([c.encode('hex') for c in data]))
		tuple = GlyphVariation(coord)
		#t.decompilePackedPoints(data)
		#pos = 0
		#numPoints = ord(data[pos])
		#if numPoints >= 0x80:
		#	pos += 1
		#	numPoints = (numPoints & 0x7f) << 8 + ord(data[pos])
		#pos += 1
		#
		# 0 means "all points in glyph"; TODO: how to find out this number?
		#if numPoints != 0:
		#	# TODO
		#	pass

		#print("    numPoints: %d" % numPoints)
		#assert not tuplesSharePointNumbers  # TODO: implement shared point numbers
		# TODO: decode deltas
		return tuple

	def getTupleSize(self, tupleIndex):
		"""Returns the byte size of a tuple given the value of its tupleIndex field."""
		size = 4
		if (tupleIndex & EMBEDDED_TUPLE_COORD) != 0:
			size += self.axisCount * 2
		if (tupleIndex & INTERMEDIATE_TUPLE) != 0:
			size += self.axisCount * 4
		return size

	def toXML(self, writer, ttFont):
		writer.simpletag("Version", value=self.version)
		writer.newline()
		writer.simpletag("Reserved", value=self.reserved)
		writer.newline()


POINTS_ARE_WORDS = 0x80
POINT_RUN_COUNT_MASK = 0x7F

class GlyphVariation:
	def __init__(self, axes):
		self.axes = axes
		self.coordinates = []

	def __repr__(self):
		axes = ','.join(sorted(['%s=%s' % (name, value) for (name, value) in self.axes.items()]))
		return '<GlyphVariation %s>' % axes

	@staticmethod
	def decompilePoints(data):
		pos = 0
		return None

	#def decompilePackedPoints(self, data):
	#	pos = 0
	#	numPoints = ord(data[pos])
	#	if numPoints >= 0x80:
	#		pos += 1
	#		numPoints = (numPoints & 0x7f) << 8 | ord(data[pos])
	#	pos += 1
	#	points = []
	#	if numPoints == 0:
	#		return (points, data[pos:])
	#	i = 0
	#	while i < numPoints:
	#		controlByte = ord(data[pos])
	#		if (controlByte & 0x80) != 0:
	#			
	#			pos += 1
	#			numPointsInRun = (numPointsInRun & 0x7f) << 8 | ord(data[pos])
	#		print('********************** numPointsInRun: %d' % numPointsInRun)
	#		break
