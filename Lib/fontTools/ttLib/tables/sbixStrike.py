from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from .sbixGlyph import *
import struct

sbixBitmapSetHeaderFormat = """
  >
  ppem:            H    # The PPEM for which this strike was designed (e.g., 9,
                        # 12, 24)
  resolution:      H    # The screen resolution (in dpi) for which this strike
                        # was designed (e.g., 72)
"""

sbixBitmapOffsetEntryFormat = """
	>
	ulOffset:        L    # 00 00 07 E0 # Offset from start of first offset entry to each bitmap
"""

sbixBitmapSetHeaderFormatSize = sstruct.calcsize(sbixBitmapSetHeaderFormat)
sbixBitmapOffsetEntryFormatSize = sstruct.calcsize(sbixBitmapOffsetEntryFormat)


class Strike(object):
	def __init__(self, rawdata=None, ppem=0, resolution=72):
		self.data = rawdata
		self.ppem = ppem
		self.resolution = resolution
		self.bitmaps = {}

	def decompile(self, ttFont):
		if self.data is None:
			from fontTools import ttLib
			raise ttLib.TTLibError
		if len(self.data) < sbixBitmapSetHeaderFormatSize:
			from fontTools import ttLib
			raise(ttLib.TTLibError, "Strike header too short: Expected %x, got %x.") \
				% (sbixBitmapSetHeaderFormatSize, len(self.data))

		# read Strike header from raw data
		sstruct.unpack(sbixBitmapSetHeaderFormat, self.data[:sbixBitmapSetHeaderFormatSize], self)

		# calculate number of bitmaps
		firstBitmapOffset, = struct.unpack(">L", \
			self.data[sbixBitmapSetHeaderFormatSize : sbixBitmapSetHeaderFormatSize + sbixBitmapOffsetEntryFormatSize])
		self.numBitmaps = (firstBitmapOffset - sbixBitmapSetHeaderFormatSize) // sbixBitmapOffsetEntryFormatSize - 1
		# ^ -1 because there's one more offset than bitmaps

		# build offset list for single bitmap offsets
		self.bitmapOffsets = []
		for i in range(self.numBitmaps + 1): # + 1 because there's one more offset than bitmaps
			start = i * sbixBitmapOffsetEntryFormatSize + sbixBitmapSetHeaderFormatSize
			myOffset, = struct.unpack(">L", self.data[start : start + sbixBitmapOffsetEntryFormatSize])
			self.bitmapOffsets.append(myOffset)

		# iterate through offset list and slice raw data into bitmaps
		for i in range(self.numBitmaps):
			myBitmap = Bitmap(rawdata=self.data[self.bitmapOffsets[i] : self.bitmapOffsets[i+1]], gid=i)
			myBitmap.decompile(ttFont)
			self.bitmaps[myBitmap.glyphName] = myBitmap
		del self.bitmapOffsets
		del self.data

	def compile(self, ttFont):
		self.bitmapOffsets = ""
		self.bitmapData = ""

		glyphOrder = ttFont.getGlyphOrder()

		# first bitmap starts right after the header
		bitmapOffset = sbixBitmapSetHeaderFormatSize + sbixBitmapOffsetEntryFormatSize * (len(glyphOrder) + 1)
		for glyphName in glyphOrder:
			if glyphName in self.bitmaps:
				# we have a bitmap for this glyph
				myBitmap = self.bitmaps[glyphName]
			else:
				# must add empty bitmap for this glyph
				myBitmap = Bitmap(glyphName=glyphName)
			myBitmap.compile(ttFont)
			myBitmap.ulOffset = bitmapOffset
			self.bitmapData += myBitmap.rawdata
			bitmapOffset += len(myBitmap.rawdata)
			self.bitmapOffsets += sstruct.pack(sbixBitmapOffsetEntryFormat, myBitmap)

		# add last "offset", really the end address of the last bitmap
		dummy = Bitmap()
		dummy.ulOffset = bitmapOffset
		self.bitmapOffsets += sstruct.pack(sbixBitmapOffsetEntryFormat, dummy)

		# pack header
		self.data = sstruct.pack(sbixBitmapSetHeaderFormat, self)
		# add offsets and image data after header
		self.data += self.bitmapOffsets + self.bitmapData

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.begintag("strike")
		xmlWriter.newline()
		xmlWriter.simpletag("ppem", value=self.ppem)
		xmlWriter.newline()
		xmlWriter.simpletag("resolution", value=self.resolution)
		xmlWriter.newline()
		glyphOrder = ttFont.getGlyphOrder()
		for i in range(len(glyphOrder)):
			if glyphOrder[i] in self.bitmaps:
				self.bitmaps[glyphOrder[i]].toXML(xmlWriter, ttFont)
				# TODO: what if there are more bitmaps than glyphs?
		xmlWriter.endtag("strike")
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["ppem", "resolution"]:
			setattr(self, name, int(attrs["value"]))
		elif name == "bitmap":
			if "format" in attrs:
				myFormat = attrs["format"]
			else:
				myFormat = None
			if "glyphname" in attrs:
				myGlyphName = attrs["glyphname"]
			else:
				from fontTools import ttLib
				raise ttLib.TTLibError("Bitmap must have a glyph name.")
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
			self.bitmaps[myBitmap.glyphName] = myBitmap
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)
