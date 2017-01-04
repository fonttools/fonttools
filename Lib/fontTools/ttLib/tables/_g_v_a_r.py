from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.ttLib import TTLibError
from . import DefaultTable
import array
import sys
import struct
import logging
import fontTools.ttLib.tables.TupleVariation as tv


log = logging.getLogger(__name__)
TupleVariation = tv.TupleVariation


# https://www.microsoft.com/typography/otspec/gvar.htm
# https://www.microsoft.com/typography/otspec/otvarcommonformats.htm
#
# Apple's documentation of 'gvar':
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
#
# FreeType2 source code for parsing 'gvar':
# http://git.savannah.gnu.org/cgit/freetype/freetype2.git/tree/src/truetype/ttgxvar.c

GVAR_HEADER_FORMAT = """
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
TUPLE_INDEX_MASK = 0x0fff


class table__g_v_a_r(DefaultTable.DefaultTable):

	dependencies = ["fvar", "glyf"]

	def compile(self, ttFont):
		axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]

		sharedCoords = self.compileSharedCoords_(axisTags)
		sharedCoordIndices = {coord:i for i, coord in enumerate(sharedCoords)}
		sharedCoordSize = sum([len(c) for c in sharedCoords])

		compiledGlyphs = self.compileGlyphs_(ttFont, axisTags, sharedCoordIndices)
		offset = 0
		offsets = []
		for glyph in compiledGlyphs:
			offsets.append(offset)
			offset += len(glyph)
		offsets.append(offset)
		compiledOffsets, tableFormat = self.compileOffsets_(offsets)

		header = {}
		header["version"] = self.version
		header["reserved"] = self.reserved
		header["axisCount"] = len(axisTags)
		header["sharedCoordCount"] = len(sharedCoords)
		header["offsetToCoord"] = GVAR_HEADER_SIZE + len(compiledOffsets)
		header["glyphCount"] = len(compiledGlyphs)
		header["flags"] = tableFormat
		header["offsetToData"] = header["offsetToCoord"] + sharedCoordSize
		compiledHeader = sstruct.pack(GVAR_HEADER_FORMAT, header)

		result = [compiledHeader, compiledOffsets]
		result.extend(sharedCoords)
		result.extend(compiledGlyphs)
		return bytesjoin(result)

	def compileSharedCoords_(self, axisTags):
		coordCount = {}
		for variations in self.variations.values():
			for gvar in variations:
				coord = gvar.compileCoord(axisTags)
				coordCount[coord] = coordCount.get(coord, 0) + 1
		sharedCoords = [(count, coord) for (coord, count) in coordCount.items() if count > 1]
		sharedCoords.sort(reverse=True)
		MAX_NUM_SHARED_COORDS = TUPLE_INDEX_MASK + 1
		sharedCoords = sharedCoords[:MAX_NUM_SHARED_COORDS]
		return [c[1] for c in sharedCoords]  # Strip off counts.

	def compileGlyphs_(self, ttFont, axisTags, sharedCoordIndices):
		result = []
		for glyphName in ttFont.getGlyphOrder():
			glyph = ttFont["glyf"][glyphName]
			numPointsInGlyph = self.getNumPoints_(glyph)
			result.append(self.compileGlyph_(glyphName, numPointsInGlyph, axisTags, sharedCoordIndices))
		return result

	def compileGlyph_(self, glyphName, numPointsInGlyph, axisTags, sharedCoordIndices):
		variations = self.variations.get(glyphName, [])
		variations = [v for v in variations if v.hasImpact()]
		if len(variations) == 0:
			return b""

		# Each glyph variation tuples modifies a set of control points. To indicate
		# which exact points are getting modified, a single tuple can either refer
		# to a shared set of points, or the tuple can supply its private point numbers.
		# Because the impact of sharing can be positive (no need for a private point list)
		# or negative (need to supply 0,0 deltas for unused points), it is not obvious
		# how to determine which tuples should take their points from the shared
		# pool versus have their own. Perhaps we should resort to brute force,
		# and try all combinations? However, if a glyph has n variation tuples,
		# we would need to try 2^n combinations (because each tuple may or may not
		# be part of the shared set). How many variations tuples do glyphs have?
		#
		#   Skia.ttf: {3: 1, 5: 11, 6: 41, 7: 62, 8: 387, 13: 1, 14: 3}
		#   JamRegular.ttf: {3: 13, 4: 122, 5: 1, 7: 4, 8: 1, 9: 1, 10: 1}
		#   BuffaloGalRegular.ttf: {1: 16, 2: 13, 4: 2, 5: 4, 6: 19, 7: 1, 8: 3, 9: 18}
		#   (Reading example: In Skia.ttf, 41 glyphs have 6 variation tuples).
		#
		# Is this even worth optimizing? If we never use a shared point list,
		# the private lists will consume 112K for Skia, 5K for BuffaloGalRegular,
		# and 15K for JamRegular. If we always use a shared point list,
		# the shared lists will consume 16K for Skia, 3K for BuffaloGalRegular,
		# and 10K for JamRegular. However, in the latter case the delta arrays
		# will become larger, but I haven't yet measured by how much. From
		# gut feeling (which may be wrong), the optimum is to share some but
		# not all points; however, then we would need to try all combinations.
		#
		# For the time being, we try two variants and then pick the better one:
		# (a) each tuple supplies its own private set of points;
		# (b) all tuples refer to a shared set of points, which consists of
		#     "every control point in the glyph".
		allPoints = set(range(numPointsInGlyph))
		tuples = []
		data = []
		someTuplesSharePoints = False
		for gvar in variations:
			privateTuple, privateData = gvar.compile(axisTags, sharedCoordIndices, sharedPoints=None)
			sharedTuple, sharedData = gvar.compile(axisTags, sharedCoordIndices, sharedPoints=allPoints)
			# TODO: If we use shared points, Apple MacOS X 10.9.5 cannot display our fonts.
			# This is probably a problem with our code; find the problem and fix it.
			#if (len(sharedTuple) + len(sharedData)) < (len(privateTuple) + len(privateData)):
			if False:
				tuples.append(sharedTuple)
				data.append(sharedData)
				someTuplesSharePoints = True
			else:
				tuples.append(privateTuple)
				data.append(privateData)
		if someTuplesSharePoints:
			data = bytechr(0) + bytesjoin(data)  # 0x00 = "all points in glyph"
			tupleCount = TUPLES_SHARE_POINT_NUMBERS | len(tuples)
		else:
			data = bytesjoin(data)
			tupleCount = len(tuples)
		tuples = bytesjoin(tuples)
		result = struct.pack(">HH", tupleCount, 4 + len(tuples)) + tuples + data
		if len(result) % 2 != 0:
			result = result + b"\0"  # padding
		return result

	def decompile(self, data, ttFont):
		axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
		glyphs = ttFont.getGlyphOrder()
		sstruct.unpack(GVAR_HEADER_FORMAT, data[0:GVAR_HEADER_SIZE], self)
		assert len(glyphs) == self.glyphCount
		assert len(axisTags) == self.axisCount
		offsets = self.decompileOffsets_(data[GVAR_HEADER_SIZE:], tableFormat=(self.flags & 1), glyphCount=self.glyphCount)
		sharedCoords = self.decompileSharedCoords_(axisTags, data)
		self.variations = {}
		for i in range(self.glyphCount):
			glyphName = glyphs[i]
			glyph = ttFont["glyf"][glyphName]
			numPointsInGlyph = self.getNumPoints_(glyph)
			gvarData = data[self.offsetToData + offsets[i] : self.offsetToData + offsets[i + 1]]
			self.variations[glyphName] = \
				self.decompileGlyph_(numPointsInGlyph, sharedCoords, axisTags, gvarData)

	def decompileSharedCoords_(self, axisTags, data):
		result, _pos = TupleVariation.decompileCoords_(axisTags, self.sharedCoordCount, data, self.offsetToCoord)
		return result

	@staticmethod
	def decompileOffsets_(data, tableFormat, glyphCount):
		if tableFormat == 0:
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
		if tableFormat == 0:
			offsets = [off * 2 for off in offsets]

		return offsets

	@staticmethod
	def compileOffsets_(offsets):
		"""Packs a list of offsets into a 'gvar' offset table.

		Returns a pair (bytestring, tableFormat). Bytestring is the
		packed offset table. Format indicates whether the table
		uses short (tableFormat=0) or long (tableFormat=1) integers.
		The returned tableFormat should get packed into the flags field
		of the 'gvar' header.
		"""
		assert len(offsets) >= 2
		for i in range(1, len(offsets)):
			assert offsets[i - 1] <= offsets[i]
		if max(offsets) <= 0xffff * 2:
			packed = array.array("H", [n >> 1 for n in offsets])
			tableFormat = 0
		else:
			packed = array.array("I", offsets)
			tableFormat = 1
		if sys.byteorder != "big":
			packed.byteswap()
		return (packed.tostring(), tableFormat)

	def decompileGlyph_(self, numPointsInGlyph, sharedCoords, axisTags, data):
		if len(data) < 4:
			return []
		numAxes = len(axisTags)
		tuples = []
		flags, offsetToData = struct.unpack(">HH", data[:4])
		pos = 4
		dataPos = offsetToData
		if (flags & TUPLES_SHARE_POINT_NUMBERS) != 0:
			sharedPoints, dataPos = TupleVariation.decompilePoints_(numPointsInGlyph, data, dataPos)
		else:
			sharedPoints = []
		for _ in range(flags & TUPLE_COUNT_MASK):
			dataSize, flags = struct.unpack(">HH", data[pos:pos+4])
			tupleSize = TupleVariation.getTupleSize_(flags, numAxes)
			tupleData = data[pos : pos + tupleSize]
			pointDeltaData = data[dataPos : dataPos + dataSize]
			tuples.append(self.decompileTuple_(numPointsInGlyph, sharedCoords, sharedPoints, axisTags, tupleData, pointDeltaData))
			pos += tupleSize
			dataPos += dataSize
		return tuples

	@staticmethod
	def decompileTuple_(numPointsInGlyph, sharedCoords, sharedPoints, axisTags, data, tupleData):
		flags = struct.unpack(">H", data[2:4])[0]

		pos = 4
		if (flags & tv.EMBEDDED_PEAK_TUPLE) == 0:
			coord = sharedCoords[flags & TUPLE_INDEX_MASK]
		else:
			coord, pos = TupleVariation.decompileCoord_(axisTags, data, pos)
		if (flags & tv.INTERMEDIATE_REGION) != 0:
			minCoord, pos = TupleVariation.decompileCoord_(axisTags, data, pos)
			maxCoord, pos = TupleVariation.decompileCoord_(axisTags, data, pos)
		else:
			minCoord, maxCoord = table__g_v_a_r.computeMinMaxCoord_(coord)
		axes = {}
		for axis in axisTags:
			coords = minCoord[axis], coord[axis], maxCoord[axis]
			if coords != (0.0, 0.0, 0.0):
				axes[axis] = coords
		pos = 0
		if (flags & tv.PRIVATE_POINT_NUMBERS) != 0:
			points, pos = TupleVariation.decompilePoints_(numPointsInGlyph, tupleData, pos)
		else:
			points = sharedPoints
		deltas_x, pos = TupleVariation.decompileDeltas_(len(points), tupleData, pos)
		deltas_y, pos = TupleVariation.decompileDeltas_(len(points), tupleData, pos)
		deltas = [None] * numPointsInGlyph
		for p, x, y in zip(points, deltas_x, deltas_y):
				if 0 <= p < numPointsInGlyph:
					deltas[p] = (x, y)
		return TupleVariation(axes, deltas)

	@staticmethod
	def computeMinMaxCoord_(coord):
		minCoord = {}
		maxCoord = {}
		for (axis, value) in coord.items():
			minCoord[axis] = min(value, 0.0)  # -0.3 --> -0.3; 0.7 --> 0.0
			maxCoord[axis] = max(value, 0.0)  # -0.3 -->  0.0; 0.7 --> 0.7
		return (minCoord, maxCoord)

	def toXML(self, writer, ttFont, progress=None):
		writer.simpletag("version", value=self.version)
		writer.newline()
		writer.simpletag("reserved", value=self.reserved)
		writer.newline()
		axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
		for glyphName in ttFont.getGlyphOrder():
			variations = self.variations.get(glyphName)
			if not variations:
				continue
			writer.begintag("glyphVariations", glyph=glyphName)
			writer.newline()
			for gvar in variations:
				gvar.toXML(writer, axisTags)
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
			numPointsInGlyph = self.getNumPoints_(glyph)
			glyphVariations = []
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					if name == "tuple":
						gvar = TupleVariation({}, [None] * numPointsInGlyph)
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
