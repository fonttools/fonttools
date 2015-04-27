from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import fixedToFloat
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from . import DefaultTable
import array
import sys
import struct

# Apple's documentation of 'gvar':
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
#
# FreeType2 source code for parsing 'gvar':
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

POINTS_ARE_WORDS = 0x80
POINT_RUN_COUNT_MASK = 0x7f


class table__g_v_a_r(DefaultTable.DefaultTable):

	dependencies = ["fvar", "glyf"]

	def decompile(self, data, ttFont):
		axisTags = [axis.AxisTag for axis in ttFont["fvar"].table.VariationAxis]
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
			self.variations[glyphName] = self.decompileTuples_(numPoints, sharedCoords, axisTags, gvarData)

	def decompileSharedCoords_(self, axisTags, data):
		result = []
		pos = self.offsetToCoord
		for i in xrange(self.sharedCoordCount):
			coord, pos = self.decompileCoord_(axisTags, data, pos)
			result.append(coord)
		return result

	@staticmethod
	def decompileCoord_(axisTags, data, offset):
		coord = {}
		pos = offset
		for axis in axisTags:
			coord[axis] = fixedToFloat(struct.unpack(b">h", data[pos:pos+2])[0], 14)
			pos += 2
		return coord, pos

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

		Returns a pair (bytestring, format). Bytestring is the
		packed offset table. Format indicates whether the table
		uses short (format=0) or long (format=1) integers.
		The returned format should get packed into the flags field
		of the 'gvar' header.
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

	def decompileTuples_(self, numPoints, sharedCoords, axisTags, data):
		if len(data) < 4:
			return []
		tuples = []
		flags, offsetToData = struct.unpack(b">HH", data[:4])
		pos = 4
		dataPos = offsetToData
		if (flags & TUPLES_SHARE_POINT_NUMBERS) != 0:
			sharedPoints, dataPos = self.decompilePoints_(numPoints, data, dataPos)
		else:
			sharedPoints = []
		for i in xrange(flags & TUPLE_COUNT_MASK):
			dataSize, flags = struct.unpack(b">HH", data[pos:pos+4])
			tupleSize = self.getTupleSize_(flags, self.axisCount)
			tuple = data[pos : pos + tupleSize]
			tupleData = data[dataPos : dataPos + dataSize]
			tuples.append(self.decompileTuple_(numPoints, sharedCoords, sharedPoints, axisTags, tuple, tupleData))
			pos += tupleSize
			dataPos += dataSize
		return tuples

	@staticmethod
	def getTupleSize_(flags, axisCount):
		size = 4
		if (flags & EMBEDDED_TUPLE_COORD) != 0:
			size += axisCount * 2
		if (flags & INTERMEDIATE_TUPLE) != 0:
			size += axisCount * 4
		return size

	@staticmethod
	def decompileTuple_(numPoints, sharedCoords, sharedPoints, axisTags, data, tupleData):
		flags = struct.unpack(b">H", data[2:4])[0]

		pos = 4
		coordSize = len(axisTags) * 2
		if (flags & EMBEDDED_TUPLE_COORD) == 0:
			coord = sharedCoords[flags & TUPLE_INDEX_MASK]
		else:
			coord, pos = table__g_v_a_r.decompileCoord_(axisTags, data, pos)
		minCoord = maxCoord = coord
		if (flags & INTERMEDIATE_TUPLE) != 0:
			minCoord, pos = table__g_v_a_r.decompileCoord_(axisTags, data, pos)
			maxCoord, pos = table__g_v_a_r.decompileCoord_(axisTags, data, pos)
		axes = {}
		for axis in axisTags:
			coords = minCoord[axis], coord[axis], maxCoord[axis]
			if coords != (0.0, 0.0, 0.0):
				axes[axis] = coords
		pos = 0
		if (flags & PRIVATE_POINT_NUMBERS) != 0:
			points, pos = table__g_v_a_r.decompilePoints_(numPoints, tupleData, pos)
		else:
			points = sharedPoints
		deltas_x, pos = table__g_v_a_r.decompileDeltas_(len(points), tupleData, pos)
		deltas_y, pos = table__g_v_a_r.decompileDeltas_(len(points), tupleData, pos)
		deltas = GlyphCoordinates.zeros(numPoints)
		for p, x, y in zip(points, deltas_x, deltas_y):
				deltas[p] = (x, y)
		return GlyphVariation(axes, deltas)

	@staticmethod
	def decompilePoints_(numPoints, data, offset):
		"""(numPoints, data, offset) --> ([point1, point2, ...], newOffset)"""
		pos = offset
		numPointsInData = ord(data[pos])
		pos += 1
		if (numPointsInData & POINTS_ARE_WORDS) != 0:
			numPointsInData = (numPointsInData & POINT_RUN_COUNT_MASK) << 8 | ord(data[pos])
			pos += 1
		if numPointsInData == 0:
			return (range(numPoints), pos)
		result = []
		while len(result) < numPointsInData:
			runHeader = ord(data[pos])
			pos += 1
			numPointsInRun = (runHeader & POINT_RUN_COUNT_MASK) + 1
			point = 0
			if (runHeader & POINTS_ARE_WORDS) == 0:
				for i in xrange(numPointsInRun):
					point += ord(data[pos])
					pos += 1
					result.append(point)
			else:
				for i in xrange(numPointsInRun):
					point += struct.unpack(">H", data[pos:pos+2])[0]
					pos += 2
					result.append(point)
		if max(result) >= numPoints:
			raise ttLib.TTLibError("malformed 'gvar' table")
		return (result, pos)

	@staticmethod
	def decompileDeltas_(numDeltas, data, offset):
		"""(numDeltas, data, offset) --> ([delta, delta, ...], newOffset)"""
		result = []
		pos = offset
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
		writer.simpletag("version", value=self.version)
		writer.newline()
		writer.simpletag("reserved", value=self.reserved)
		writer.newline()
		axisTags = [axis.AxisTag for axis in ttFont["fvar"].table.VariationAxis]
		for glyphName in ttFont.getGlyphOrder():
			tuples = self.variations.get(glyphName)
			if not tuples:
				continue
			writer.begintag("glyphVariation", glyph=glyphName)
			writer.newline()
			for tupleIndex in xrange(len(tuples)):
				tuple = tuples[tupleIndex]
				writer.begintag("tuple")
				writer.newline()
				for axis in axisTags:
					value = tuple.axes.get(axis)
					if value != None:
						minValue, value, maxValue = value
						if minValue == value and maxValue == value:
							writer.simpletag("coord", axis=axis, value=value)
						else:
							writer.simpletag("coord", axis=axis, value=value,
									 min=minValue, max=maxValue)
						writer.newline()
				wrote_any_points = False
				for i in xrange(len(tuple.coordinates)):
					x, y = tuple.coordinates[i]
					if x != 0 or y != 0:
						writer.simpletag("delta", pt=i, x=x, y=y)
						writer.newline()
						wrote_any_points = True
				if not wrote_any_points:
					writer.comment("all deltas are (0,0)")
					writer.newline()
				writer.endtag("tuple")
				writer.newline()
			writer.endtag("glyphVariation")
			writer.newline()


class GlyphVariation:
	def __init__(self, axes, coordinates):
		self.axes = axes
		self.coordinates = coordinates

	def __repr__(self):
		axes = ",".join(sorted(['%s=%s' % (name, value) for (name, value) in self.axes.items()]))
		return '<GlyphVariation %s %s>' % (axes, self.coordinates)
