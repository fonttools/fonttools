from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import fixedToFloat, floatToFixed
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from . import DefaultTable
import array
import io
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

	def compile(self, ttFont):
		axisTags = [axis.AxisTag for axis in ttFont["fvar"].table.VariationAxis]

		sharedCoords = self.compileSharedCoords_(ttFont, axisTags)
		sharedCoordIndices = dict([(sharedCoords[i], i) for i in xrange(len(sharedCoords))])
		sharedCoordSize = sum([len(c) for c in sharedCoords])

		compiledGlyphs = self.compileGlyphs_(ttFont, axisTags, sharedCoordIndices)

		offset = 0
		offsets = []
		for glyph in compiledGlyphs:
			offsets.append(offset)
			offset += len(glyph)
		offsets.append(offset)
		compiledGlyphsSize = offset
		compiledOffsets, format = self.compileOffsets_(offsets)

		header = {}
		header["version"] = self.version
		header["reserved"] = self.reserved
		header["axisCount"] = len(axisTags)
		header["sharedCoordCount"] = len(sharedCoords)
		header["offsetToCoord"] = GVAR_HEADER_SIZE + len(compiledOffsets)
		header["glyphCount"] = len(compiledGlyphs)
		header["flags"] = format
		header["offsetToData"] = header["offsetToCoord"] + sharedCoordSize
		compiledHeader = sstruct.pack(GVAR_HEADER_FORMAT, header)

		result = [compiledHeader, compiledOffsets]
		result.extend(sharedCoords)
		result.extend(compiledGlyphs)
		return bytesjoin(result)

	def compileSharedCoords_(self, ttFont, axisTags):
		coordCount = {}
		for glyph in ttFont.getGlyphOrder():
			if glyph in self.variations:
				for gvar in self.variations[glyph]:
					coord = gvar.compileCoord(axisTags)
					coordCount[coord] = coordCount.get(coord, 0) + 1
		sharedCoords = [(count, coord) for (coord, count) in coordCount.items() if count > 1]
		sharedCoords.sort(reverse=True)
		MAX_NUM_SHARED_COORDS = TUPLE_INDEX_MASK + 1
		sharedCoords = sharedCoords[:MAX_NUM_SHARED_COORDS]
		return [c[1] for c in sharedCoords]  # Strip off counts.

	def compileGlyphs_(self, ttFont, axisTags, sharedCoordIndices):
		result = [self.compileGlyph_(g, axisTags, sharedCoordIndices) for g in ttFont.getGlyphOrder()]
		return result

	# TODO: Remove this once the code works.
	@staticmethod
	def visualizePoints_(points):
		result = []
		for p in xrange(max(points) + 1):
			if p in points:
				result.append("*")
			else:
				result.append("_")
		return ''.join(result)

	def compileGlyph_(self, glyph, axisTags, sharedCoordIndices):
		variations = self.variations.get(glyph, [])
		# Omit variations that have no user-visible impact because their deltas
		# are all (0, 0).  In the Apple Skia font, about 5% of all glyph variation
		# tuples can be omitted.  On the other hand, in the JamRegular and
		# BuffaloGalRegular fonts, all tuples have at least one non-zero delta.
		variations = [v for v in variations if v.hasImpact()]
		if len(variations) == 0:
			return b""

		# TODO: Find a heuristic for using shared versus private point lists.
		#
		# The variation tuples modify a set of points. To indicate which points
		# it affects, a single tuple can either refer to a shared set of points,
		# or the tuple can supply its private point numbers. Because the impact
		# of sharing can be positive (no need for private point list) or negative
		# (need to supply 0,0 deltas for unused points), it is not obvious how
		# to determine which tuples should take their points from the shared
		# pool versus have their own. Perhaps we should resort to brute force,
		# and try all combinations? However, if a glyph has n variation tuples,
		# we would need to try 2^n combinations (because each tuple may or may not
		# be part of the shared set). How many variations tuples do glyphs have?
		#
		#   Skia.ttf: {3: 1, 5: 11, 6: 41, 7: 62, 8: 387, 13: 1, 14: 3}
		#   JamRegular.ttf: {3: 13, 4: 122, 5: 1, 7: 4, 8: 1, 9: 1, 10: 1}
		#   BuffaloGalRegular.ttf: {1: 16, 2: 13, 4: 2, 5: 4, 6: 19, 7: 1, 8: 3, 9: 18}
		#
		# Reading example: In Skia.ttf, 41 glyphs have 6 variation tuples.
		# Is it even worth optimizing? If we never use a shared point list,
		# the private lists will consume 112K for Skia, 5K for BuffaloGalRegular,
		# and 15K for JamRegular. If we always use a shared point list,
		# the shared lists will consume 16K for Skia, 3K for BuffaloGalRegular,
		# and 10K for JamRegular. However, in the latter case the delta arrays
		# will become larger, but I haven't yet measured by how much. From
		# gut feeling (which may be wrong), the optimum is to share some but
		# not all points; however, then we would need to try all combinations.
		usedPoints = [gvar.getUsedPoints() for gvar in variations]
		usedPointsUnion = set.union(*usedPoints)
		print('-------------------- %s %s' % (glyph, len(usedPoints)))
		for gvar, used in zip(variations, usedPoints):
			print('    %s    len=%d' % (self.visualizePoints_(used), len(GlyphVariation.compilePoints(used))))
		print('--> %s    len=%d' % (self.visualizePoints_(usedPointsUnion), len(GlyphVariation.compilePoints(usedPointsUnion))))
		return b"TODO"

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
			numPoints = self.getNumPoints_(glyph)
			gvarData = data[self.offsetToData + offsets[i] : self.offsetToData + offsets[i + 1]]
			self.variations[glyphName] = self.decompileGlyph_(numPoints, sharedCoords, axisTags, gvarData)

	def decompileSharedCoords_(self, axisTags, data):
		result, pos = GlyphVariation.decompileCoords_(axisTags, self.sharedCoordCount, data, self.offsetToCoord)
		return result

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

	def decompileGlyph_(self, numPoints, sharedCoords, axisTags, data):
		if len(data) < 4:
			return []
		tuples = []
		flags, offsetToData = struct.unpack(b">HH", data[:4])
		pos = 4
		dataPos = offsetToData
		if (flags & TUPLES_SHARE_POINT_NUMBERS) != 0:
			sharedPoints, dataPos = GlyphVariation.decompilePoints_(numPoints, data, dataPos)
		else:
			sharedPoints = []
		for i in xrange(flags & TUPLE_COUNT_MASK):
			dataSize, flags = struct.unpack(b">HH", data[pos:pos+4])
			tupleSize = GlyphVariation.getTupleSize_(flags, self.axisCount)
			tuple = data[pos : pos + tupleSize]
			tupleData = data[dataPos : dataPos + dataSize]
			tuples.append(self.decompileTuple_(numPoints, sharedCoords, sharedPoints, axisTags, tuple, tupleData))
			pos += tupleSize
			dataPos += dataSize
		return tuples

	@staticmethod
	def decompileTuple_(numPoints, sharedCoords, sharedPoints, axisTags, data, tupleData):
		flags = struct.unpack(b">H", data[2:4])[0]

		pos = 4
		coordSize = len(axisTags) * 2
		if (flags & EMBEDDED_TUPLE_COORD) == 0:
			coord = sharedCoords[flags & TUPLE_INDEX_MASK]
		else:
			coord, pos = GlyphVariation.decompileCoord_(axisTags, data, pos)
		if (flags & INTERMEDIATE_TUPLE) != 0:
			minCoord, pos = GlyphVariation.decompileCoord_(axisTags, data, pos)
			maxCoord, pos = GlyphVariation.decompileCoord_(axisTags, data, pos)
		else:
			minCoord, maxCoord = table__g_v_a_r.computeMinMaxCoord_(coord)
		axes = {}
		for axis in axisTags:
			coords = minCoord[axis], coord[axis], maxCoord[axis]
			if coords != (0.0, 0.0, 0.0):
				axes[axis] = coords
		pos = 0
		if (flags & PRIVATE_POINT_NUMBERS) != 0:
			points, pos = GlyphVariation.decompilePoints_(numPoints, tupleData, pos)
		else:
			points = sharedPoints
		deltas_x, pos = GlyphVariation.decompileDeltas_(len(points), tupleData, pos)
		deltas_y, pos = GlyphVariation.decompileDeltas_(len(points), tupleData, pos)
		deltas = GlyphCoordinates.zeros(numPoints)
		for p, x, y in zip(points, deltas_x, deltas_y):
				deltas[p] = (x, y)
		return GlyphVariation(axes, deltas)

	@staticmethod
	def computeMinMaxCoord_(coord):
		minCoord = {}
		maxCoord = {}
		for (axis, value) in coord.iteritems():
			minCoord[axis] = min(value, 0.0)  # -0.3 --> -0.3; 0.7 --> 0.0
			maxCoord[axis] = max(value, 0.0)  # -0.3 -->  0.0; 0.7 --> 0.7
		return (minCoord, maxCoord)

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
			writer.begintag("glyphVariations", glyph=glyphName)
			writer.newline()
			for tuple in tuples:
				tuple.toXML(writer, axisTags)
			writer.endtag("glyphVariations")
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name == "version":
			self.version = safeEval(attrs["value"])
		elif name == "reserved":
			self.reserved = safeEval(attrs["value"])
		elif name == "glyphVariations":
			if not hasattr(self, "variations"):
				self.variations = {}
			glyphName = attrs["glyph"]
			glyph = ttFont["glyf"][glyphName]
			numPoints = self.getNumPoints_(glyph)
			glyphVariations = []
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					if name == "tuple":
						gvar = GlyphVariation({}, GlyphCoordinates.zeros(numPoints))
						glyphVariations.append(gvar)
						for tupleElement in content:
							if isinstance(tupleElement, tuple):
								tupleName, tupleAttrs, tupleContent = tupleElement
								gvar.fromXML(tupleName, tupleAttrs, tupleContent)
			self.variations[glyphName] = glyphVariations

	@staticmethod
	def getNumPoints_(glyph):
		NUM_PHANTOM_POINTS = 4
		if glyph.isComposite():
			return len(glyph.components) + NUM_PHANTOM_POINTS
		else:
			# Empty glyphs (eg. space, nonmarkingreturn) have no "coordinates" attribute.
			return len(getattr(glyph, "coordinates", [])) + NUM_PHANTOM_POINTS


class GlyphVariation:
	def __init__(self, axes, coordinates):
		self.axes = axes
		self.coordinates = coordinates

	def __repr__(self):
		axes = ",".join(sorted(["%s=%s" % (name, value) for (name, value) in self.axes.items()]))
		return "<GlyphVariation %s %s>" % (axes, self.coordinates)

	def getUsedPoints(self):
		result = set()
		for p in xrange(len(self.coordinates)):
			if self.coordinates[p] != (0, 0):
				result.add(p)
		return result

	def hasImpact(self):
		"""Returns True if this GlyphVariation has any visible impact.

		If the result is False, the GlyphVariation can be omitted from the font
		without making any visible difference.
		"""
		for c in self.coordinates:
			if c != (0, 0):
				return True
		return False

	def toXML(self, writer, axisTags):
		writer.begintag("tuple")
		writer.newline()
		for axis in axisTags:
			value = self.axes.get(axis)
			if value != None:
				minValue, value, maxValue = value
				defaultMinValue = min(value, 0.0)  # -0.3 --> -0.3; 0.7 --> 0.0
				defaultMaxValue = max(value, 0.0)  # -0.3 -->  0.0; 0.7 --> 0.7
				if minValue == defaultMinValue and maxValue == defaultMaxValue:
					writer.simpletag("coord", axis=axis, value=value)
				else:
					writer.simpletag("coord", axis=axis, value=value,
							 min=minValue, max=maxValue)
				writer.newline()
		wrote_any_points = False
		for i in xrange(len(self.coordinates)):
			x, y = self.coordinates[i]
			if x != 0 or y != 0:
				writer.simpletag("delta", pt=i, x=x, y=y)
				writer.newline()
				wrote_any_points = True
		if not wrote_any_points:
			writer.comment("all deltas are (0,0)")
			writer.newline()
		writer.endtag("tuple")
		writer.newline()

	def fromXML(self, name, attrs, content):
		if name == "coord":
			axis = attrs["axis"]
			value = float(attrs["value"])
			defaultMinValue = min(value, 0.0)  # -0.3 --> -0.3; 0.7 --> 0.0
			defaultMaxValue = max(value, 0.0)  # -0.3 -->  0.0; 0.7 --> 0.7
			minValue = float(attrs.get("min", defaultMinValue))
			maxValue = float(attrs.get("max", defaultMaxValue))
			self.axes[axis] = (minValue, value, maxValue)
		elif name == "delta":
			point = safeEval(attrs["pt"])
			x = safeEval(attrs["x"])
			y = safeEval(attrs["y"])
			self.coordinates[point] = (x, y)

	def compileCoord(self, axisTags):
		result = []
		for axis in axisTags:
			minValue, value, maxValue = self.axes.get(axis, (0.0, 0.0, 0.0))
			result.append(struct.pack(b">h", floatToFixed(value, 14)))
		return bytesjoin(result)

	def compileIntermediateCoord(self, axisTags):
		needed = False
		for axis in axisTags:
			minValue, value, maxValue = self.axes.get(axis, (0.0, 0.0, 0.0))
			defaultMinValue = min(value, 0.0)  # -0.3 --> -0.3; 0.7 --> 0.0
			defaultMaxValue = max(value, 0.0)  # -0.3 -->  0.0; 0.7 --> 0.7
			if (minValue != defaultMinValue) or (maxValue != defaultMaxValue):
				needed = True
				break
		if not needed:
			return None
		minCoords = []
		maxCoords = []
		for axis in axisTags:
			minValue, value, maxValue = self.axes.get(axis, (0.0, 0.0, 0.0))
			minCoords.append(struct.pack(b">h", floatToFixed(minValue, 14)))
			maxCoords.append(struct.pack(b">h", floatToFixed(maxValue, 14)))
		return bytesjoin(minCoords + maxCoords)

	@staticmethod
	def decompileCoord_(axisTags, data, offset):
		coord = {}
		pos = offset
		for axis in axisTags:
			coord[axis] = fixedToFloat(struct.unpack(b">h", data[pos:pos+2])[0], 14)
			pos += 2
		return coord, pos

	@staticmethod
	def decompileCoords_(axisTags, numCoords, data, offset):
		result = []
		pos = offset
		for i in xrange(numCoords):
			coord, pos = GlyphVariation.decompileCoord_(axisTags, data, pos)
			result.append(coord)
		return result, pos

	@staticmethod
	def compilePoints(points):
		# In the 'gvar' table, the packing of point numbers is a little surprising.
		# It consists of multiple runs, each being a delta-encoded list of integers.
		# For example, the point set {17, 18, 19, 20, 21, 22, 23} gets encoded as
		# [6, 17, 1, 1, 1, 1, 1, 1]. The first value (6) is the run length minus 1.
		# There are two types of runs, with values being either 8 or 16 bit unsigned
		# integers.
		points = list(points)
		points.sort()
		numPoints = len(points)

		# The binary representation starts with the total number of points in the set,
		# encoded into one or two bytes depending on the value.
		if numPoints < 0x80:
			result = [bytechr(numPoints)]
		else:
			result = [bytechr((numPoints >> 8) | 0x80) + bytechr(numPoints & 0x7f)]

		MAX_RUN_LENGTH = 127
		pos = 0
		while pos < numPoints:
			run = io.BytesIO()
			runLength = 0
			lastValue = 0
			useByteEncoding = (points[pos] <= 0xff)
			while pos < numPoints and runLength <= MAX_RUN_LENGTH:
				curValue = points[pos]
				delta = curValue - lastValue
				if useByteEncoding and delta > 0xff:
					# we need to start a new run (which will not use byte encoding)
					break
				if useByteEncoding:
					run.write(bytechr(delta))
				else:
					run.write(bytechr(delta >> 8))
					run.write(bytechr(delta & 0xff))
				lastValue = curValue
				pos += 1
				runLength += 1
			if useByteEncoding:
				runHeader = bytechr(runLength - 1)
			else:
				runHeader = bytechr((runLength - 1) | POINTS_ARE_WORDS)
			result.append(runHeader)
			result.append(run.getvalue())

		return bytesjoin(result)

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

	@staticmethod
	def getTupleSize_(flags, axisCount):
		size = 4
		if (flags & EMBEDDED_TUPLE_COORD) != 0:
			size += axisCount * 2
		if (flags & INTERMEDIATE_TUPLE) != 0:
			size += axisCount * 4
		return size
