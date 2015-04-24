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

GVAR_HEADER_FORMAT = b"""
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

GVAR_HEADER_SIZE = sstruct.calcsize(GVAR_HEADER_FORMAT)

TUPLES_SHARE_POINT_NUMBERS = 0x8000
TUPLE_COUNT_MASK = 0x0fff

EMBEDDED_TUPLE_COORD = 0x8000
INTERMEDIATE_TUPLE = 0x4000
PRIVATE_POINT_NUMBERS = 0x2000
TUPLE_INDEX_MASK = 0x0fff

DELTAS_ARE_ZERO = 0x80
DELTAS_ARE_WORDS = 0x40
DELTA_RUN_COUNT_MASK = 0x3f

class table__g_v_a_r(DefaultTable.DefaultTable):

	dependencies = ["fvar", "glyf"]

	def decompile(self, data, ttFont):
		data = buffer(data)  # We do a lot of slicing; no need to copy all those sub-buffers.
		axisTags = [axis.AxisTag for axis in ttFont['fvar'].table.VariationAxis]
		glyphs = ttFont.getGlyphOrder()
		sstruct.unpack(GVAR_HEADER_FORMAT, data[0:GVAR_HEADER_SIZE], self)
		assert len(glyphs) == self.glyphCount
		assert len(axisTags) == self.axisCount
		offsets = self.decompileOffsets_(data[GVAR_HEADER_SIZE:],
						 format=(self.flags & 1), glyphCount=self.glyphCount)
		sharedCoords = self.decompileSharedCoords_(axisTags, data)
		self.variations = {}
		for i in xrange(self.glyphCount):
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
		for i in xrange(self.sharedCoordCount):
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

	@staticmethod
	def decompileOffsets_(data, format, glyphCount):
		if format == 0:
			# Short format: array of UInt16
			offsets = array.array("H")
			offsetsSize = (glyphCount + 1) * 2
		else:
			# Long format: array of UInt32
			offsets = array.array("I")
			offsetsSize = (glyphCount + 1) * 4
		offsets.fromstring(data[0 : offsetsSize])
		if sys.byteorder != "big":
			offsets.byteswap()

		# In the short format, offsets need to be multiplied by 2.
		# This is not documented in Apple's TrueType specification,
		# but can be inferred from the FreeType implementation, and
		# we could verify it with two sample GX fonts.
		if format == 0:
			offsets = [off * 2 for off in offsets]

		return offsets

	@staticmethod
	def compileOffsets_(offsets):
		"""Packs a list of offsets into a 'gvar' offset table.

		Returns a pair (bytestring, flag). Bytestring is the
		packed offset table. Format indicates whether the table
		uses short (0) or long (1) integers, and should be stored
		into the flags field of the 'gvar' header.
		"""
		assert len(offsets) >= 2
		for i in xrange(1, len(offsets)):
			assert offsets[i - 1] <= offsets[i]
		if max(offsets) <= 0xffff * 2:
			packed = array.array(b"H", [n >> 1 for n in offsets])
			format = 0
		else:
			packed = array.array(b"I", offsets)
			format = 1
		if sys.byteorder != "big":
			packed.byteswap()
		return (packed.tostring(), format)

	def decompileVariations_(self, numPoints, sharedCoords, axisTags, data):
		if len(data) < 4:
			return []
		tuples = []
		tupleCount, offsetToData = struct.unpack(b">HH", data[:4])
		tuplesSharePointNumbers = (tupleCount & TUPLES_SHARE_POINT_NUMBERS) != 0
		tupleCount = tupleCount & TUPLE_COUNT_MASK
		tuplePos = 4
		dataPos = offsetToData
		for i in xrange(tupleCount):
			tupleSize, tupleIndex = struct.unpack(b">HH", data[tuplePos:tuplePos+4])
			if (tupleIndex & EMBEDDED_TUPLE_COORD) != 0:
				coord = self.decompileCoord_(axisTags, data[tuplePos+4:])
			else:
				coord = sharedCoords[tupleIndex & TUPLE_INDEX_MASK].copy()
			gvar = GlyphVariation(coord)
			tuples.append(gvar)
			tuplePos += self.getTupleSize_(tupleIndex, self.axisCount)
		return []

	@staticmethod
	def getTupleSize_(tupleIndex, axisCount):
		"""Returns the byte size of a tuple given the value of its tupleIndex field."""
		size = 4
		if (tupleIndex & EMBEDDED_TUPLE_COORD) != 0:
			size += axisCount * 2
		if (tupleIndex & INTERMEDIATE_TUPLE) != 0:
			size += axisCount * 4
		return size

	@staticmethod
	def decompileDeltas_(numDeltas, data):
		"""(numDeltas, data) --> ([delta, delta, ...], numBytesConsumed)"""
		result = []
		pos = 0
		while len(result) < numDeltas:
			runHeader = ord(data[pos])
			pos += 1
			numDeltasInRun = (runHeader & DELTA_RUN_COUNT_MASK) + 1
			if (runHeader & DELTAS_ARE_ZERO) != 0:
				result.extend([0] * numDeltasInRun)
			elif (runHeader & DELTAS_ARE_WORDS) != 0:
				for i in xrange(numDeltasInRun):
					result.append(struct.unpack(">h", data[pos:pos+2])[0])
					pos += 2
			else:
				for i in xrange(numDeltasInRun):
					result.append(struct.unpack(">b", data[pos])[0])
					pos += 1
		assert len(result) == numDeltas
		return (result, pos)

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
