from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from .sbixGlyph import *
import struct

sbixStrikeHeaderFormat = """
  >
  ppem:            H    # The PPEM for which this strike was designed (e.g., 9,
                        # 12, 24)
  resolution:      H    # The screen resolution (in dpi) for which this strike
                        # was designed (e.g., 72)
"""

sbixGlyphDataOffsetFormat = """
  >
  glyphDataOffset: L    # Offset from the beginning of the strike data record
                        # to data for the individual glyph
"""

sbixStrikeHeaderFormatSize = sstruct.calcsize(sbixStrikeHeaderFormat)
sbixGlyphDataOffsetFormatSize = sstruct.calcsize(sbixGlyphDataOffsetFormat)


class Strike(object):
	def __init__(self, rawdata=None, ppem=0, resolution=72):
		self.data = rawdata
		self.ppem = ppem
		self.resolution = resolution
		self.glyphs = {}

	def decompile(self, ttFont):
		if self.data is None:
			from fontTools import ttLib
			raise ttLib.TTLibError
		if len(self.data) < sbixStrikeHeaderFormatSize:
			from fontTools import ttLib
			raise(ttLib.TTLibError, "Strike header too short: Expected %x, got %x.") \
				% (sbixStrikeHeaderFormatSize, len(self.data))

		# read Strike header from raw data
		sstruct.unpack(sbixStrikeHeaderFormat, self.data[:sbixStrikeHeaderFormatSize], self)

		# calculate number of glyphs
		firstGlyphDataOffset, = struct.unpack(">L", \
			self.data[sbixStrikeHeaderFormatSize : sbixStrikeHeaderFormatSize + sbixGlyphDataOffsetFormatSize])
		self.numGlyphs = (firstGlyphDataOffset - sbixStrikeHeaderFormatSize) // sbixGlyphDataOffsetFormatSize - 1
		# ^ -1 because there's one more offset than glyphs

		# build offset list for single glyph data offsets
		self.glyphDataOffsets = []
		for i in range(self.numGlyphs + 1): # + 1 because there's one more offset than glyphs
			start = i * sbixGlyphDataOffsetFormatSize + sbixStrikeHeaderFormatSize
			myOffset, = struct.unpack(">L", self.data[start : start + sbixGlyphDataOffsetFormatSize])
			self.glyphDataOffsets.append(myOffset)

		# iterate through offset list and slice raw data into glyph data records
		for i in range(self.numGlyphs):
			myBitmap = Bitmap(rawdata=self.data[self.glyphDataOffsets[i] : self.glyphDataOffsets[i+1]], gid=i)
			myBitmap.decompile(ttFont)
			self.glyphs[myBitmap.glyphName] = myBitmap
		del self.glyphDataOffsets
		del self.numGlyphs
		del self.data

	def compile(self, ttFont):
		self.glyphDataOffsets = ""
		self.bitmapData = ""

		glyphOrder = ttFont.getGlyphOrder()

		# first glyph starts right after the header
		currentGlyphDataOffset = sbixStrikeHeaderFormatSize + sbixGlyphDataOffsetFormatSize * (len(glyphOrder) + 1)
		for glyphName in glyphOrder:
			if glyphName in self.glyphs:
				# we have glyph data for this glyph
				myBitmap = self.glyphs[glyphName]
			else:
				# must add empty glyph data record for this glyph
				myBitmap = Bitmap(glyphName=glyphName)
			myBitmap.compile(ttFont)
			myBitmap.glyphDataOffset = currentGlyphDataOffset
			self.bitmapData += myBitmap.rawdata
			currentGlyphDataOffset += len(myBitmap.rawdata)
			self.glyphDataOffsets += sstruct.pack(sbixGlyphDataOffsetFormat, myBitmap)

		# add last "offset", really the end address of the last glyph data record
		dummy = Bitmap()
		dummy.glyphDataOffset = currentGlyphDataOffset
		self.glyphDataOffsets += sstruct.pack(sbixGlyphDataOffsetFormat, dummy)

		# pack header
		self.data = sstruct.pack(sbixStrikeHeaderFormat, self)
		# add offsets and image data after header
		self.data += self.glyphDataOffsets + self.bitmapData

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.begintag("strike")
		xmlWriter.newline()
		xmlWriter.simpletag("ppem", value=self.ppem)
		xmlWriter.newline()
		xmlWriter.simpletag("resolution", value=self.resolution)
		xmlWriter.newline()
		glyphOrder = ttFont.getGlyphOrder()
		for i in range(len(glyphOrder)):
			if glyphOrder[i] in self.glyphs:
				self.glyphs[glyphOrder[i]].toXML(xmlWriter, ttFont)
				# TODO: what if there are more glyph data records than (glyf table) glyphs?
		xmlWriter.endtag("strike")
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["ppem", "resolution"]:
			setattr(self, name, int(attrs["value"]))
		elif name == "glyph":
			if "format" in attrs:
				myFormat = attrs["format"]
			else:
				myFormat = None
			if "glyphname" in attrs:
				myGlyphName = attrs["glyphname"]
			elif "name" in attrs:
				myGlyphName = attrs["name"]
			else:
				from fontTools import ttLib
				raise ttLib.TTLibError("Glyph must have a glyph name.")
			if "originOffsetX" in attrs:
				myOffsetX = int(attrs["originOffsetX"])
			else:
				myOffsetX = 0
			if "originOffsetY" in attrs:
				myOffsetY = int(attrs["originOffsetY"])
			else:
				myOffsetY = 0
			myBitmap = Bitmap(
				glyphName=myGlyphName,
				imageFormatTag=myFormat,
				originOffsetX=myOffsetX,
				originOffsetY=myOffsetY,
			)
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					myBitmap.fromXML(name, attrs, content, ttFont)
					myBitmap.compile(ttFont)
			self.glyphs[myBitmap.glyphName] = myBitmap
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)
