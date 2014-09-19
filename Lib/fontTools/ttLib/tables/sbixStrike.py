from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from .sbixBitmap import *
import struct

sbixBitmapSetHeaderFormat = """
	>
	size:            H    # 00 28
	resolution:      H    #       00 48
"""

sbixBitmapOffsetEntryFormat = """
	>
	ulOffset:        L    # 00 00 07 E0 # Offset from start of first offset entry to each bitmap
"""

sbixBitmapSetHeaderFormatSize = sstruct.calcsize(sbixBitmapSetHeaderFormat)
sbixBitmapOffsetEntryFormatSize = sstruct.calcsize(sbixBitmapOffsetEntryFormat)


class BitmapSet(object):
	def __init__(self, rawdata=None, size=0, resolution=72):
		self.data = rawdata
		self.size = size
		self.resolution = resolution
		self.bitmaps = {}

	def decompile(self, ttFont):
		if self.data is None:
			from fontTools import ttLib
			raise ttLib.TTLibError
		if len(self.data) < sbixBitmapSetHeaderFormatSize:
			from fontTools import ttLib
			raise(ttLib.TTLibError, "BitmapSet header too short: Expected %x, got %x.") \
				% (sbixBitmapSetHeaderFormatSize, len(self.data))

		# read BitmapSet header from raw data
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

		# bitmap sets are padded to 4 byte boundaries
		dataLength = len(self.bitmapOffsets) + len(self.bitmapData)
		if dataLength % 4 != 0:
			padding = 4 - (dataLength % 4)
		else:
			padding = 0

		# pack header
		self.data = sstruct.pack(sbixBitmapSetHeaderFormat, self)
		# add offset, image data and padding after header
		self.data += self.bitmapOffsets + self.bitmapData + "\0" * padding

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.begintag("bitmapSet")
		xmlWriter.newline()
		xmlWriter.simpletag("size", value=self.size)
		xmlWriter.newline()
		xmlWriter.simpletag("resolution", value=self.resolution)
		xmlWriter.newline()
		glyphOrder = ttFont.getGlyphOrder()
		for i in range(len(glyphOrder)):
			if glyphOrder[i] in self.bitmaps:
				self.bitmaps[glyphOrder[i]].toXML(xmlWriter, ttFont)
				# TODO: what if there are more bitmaps than glyphs?
		xmlWriter.endtag("bitmapSet")
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["size", "resolution"]:
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
			myBitmap = Bitmap(glyphName=myGlyphName, imageFormatTag=myFormat)
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					myBitmap.fromXML(name, attrs, content, ttFont)
					myBitmap.compile(ttFont)
			self.bitmaps[myBitmap.glyphName] = myBitmap
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)
