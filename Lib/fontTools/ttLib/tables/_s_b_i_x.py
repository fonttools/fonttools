from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from . import DefaultTable
from .sbixGlyph import *
from .sbixStrike import *
import struct

"""
sbix Table organization:

UInt16        version
UInt16        flags
UInt32        numStrikes               number of strikes (bitmap set for a specific size)
UInt32        strikeOffset[numStrikes] offsetEntries
(Variable)    storage for bitmap sets


strikeOffset:

UInt32        strikeOffset             Offset from begining of table to data for the individual strike


strike:

UInt16        ppem
UInt16        resolution
UInt32        glyphDataOffset[numGlyphs+1]
(Variable)    storage for glyph data


glyphDataOffset:

UInt32        glyphDataOffset          offset from start of bitmap set to individual bitmap


glyph:

SInt16        originOffsetX            00 00
SInt16        originOffsetY                  00 00
char[4]       format                   data type, e.g. "png "
(Variable)    glyph data
"""

sbixHeaderFormat = """
  >
  version:         H    # Version number (set to 1)
  flags:           H    # The only two bits used in the flags field are bits 0
                        # and 1. For historical reasons, bit 0 must always be 1.
                        # Bit 1 is a sbixDrawOutlines flag and is interpreted as
                        # follows:
                        #     0: Draw only 'sbix' bitmaps
                        #     1: Draw both 'sbix' bitmaps and outlines, in that
                        #        order
  numStrikes:      L    # Number of bitmap strikes to follow
"""
sbixHeaderFormatSize = sstruct.calcsize(sbixHeaderFormat)


sbixStrikeOffsetFormat = """
  >
  strikeOffset:    L    # Offset from begining of table to data for the
                        # individual strike
"""
sbixStrikeOffsetFormatSize = sstruct.calcsize(sbixStrikeOffsetFormat)


class table__s_b_i_x(DefaultTable.DefaultTable):
	def __init__(self, tag):
		self.tableTag = tag
		self.version = 1
		self.flags = 1
		self.numStrikes = 0
		self.strikes = {}
		self.strikeOffsets = []

	def decompile(self, data, ttFont):
		# read table header
		sstruct.unpack(sbixHeaderFormat, data[ : sbixHeaderFormatSize], self)
		# collect offsets to individual strikes in self.strikeOffsets
		for i in range(self.numStrikes):
			myOffset = sbixHeaderFormatSize + i * sbixStrikeOffsetFormatSize
			offsetEntry = sbixBitmapSetOffset()
			sstruct.unpack(sbixStrikeOffsetFormat, \
				data[myOffset : myOffset+sbixStrikeOffsetFormatSize], \
				offsetEntry)
			self.strikeOffsets.append(offsetEntry.strikeOffset)

		# decompile Strikes
		for i in range(self.numStrikes-1, -1, -1):
			myBitmapSet = Strike(rawdata=data[self.strikeOffsets[i]:])
			data = data[:self.strikeOffsets[i]]
			myBitmapSet.decompile(ttFont)
			#print "  Strike length: %xh" % len(bitmapSetData)
			#print "Number of Bitmaps:", len(myBitmapSet.glyphs)
			if myBitmapSet.ppem in self.strikes:
				from fontTools import ttLib
				raise ttLib.TTLibError("Pixel 'ppem' must be unique for each Strike")
			self.strikes[myBitmapSet.ppem] = myBitmapSet

		# after the glyph data records have been extracted, we don't need the offsets anymore
		del self.strikeOffsets

	def compile(self, ttFont):
		sbixData = ""
		self.numStrikes = len(self.strikes)
		sbixHeader = sstruct.pack(sbixHeaderFormat, self)

		# calculate offset to start of first strike
		setOffset = sbixHeaderFormatSize + sbixStrikeOffsetFormatSize * self.numStrikes

		for si in sorted(self.strikes.keys()):
			myBitmapSet = self.strikes[si]
			myBitmapSet.compile(ttFont)
			# append offset to this strike to table header
			myBitmapSet.strikeOffset = setOffset
			sbixHeader += sstruct.pack(sbixStrikeOffsetFormat, myBitmapSet)
			setOffset += len(myBitmapSet.data)
			sbixData += myBitmapSet.data

		return sbixHeader + sbixData

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.simpletag("version", value=self.version)
		xmlWriter.newline()
		xmlWriter.simpletag("flags", value=self.flags)
		xmlWriter.newline()
		for i in sorted(self.strikes.keys()):
			self.strikes[i].toXML(xmlWriter, ttFont)

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["version", "flags"]:
			setattr(self, name, int(attrs["value"]))
		elif name == "strike":
			myBitmapSet = Strike()
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					myBitmapSet.fromXML(name, attrs, content, ttFont)
			self.strikes[myBitmapSet.ppem] = myBitmapSet
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)


# Helper classes

class sbixBitmapSetOffset(object):
	pass
