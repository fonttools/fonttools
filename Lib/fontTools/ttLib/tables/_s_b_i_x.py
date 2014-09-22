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
UInt32        count                    number of bitmap sets
offsetEntry   offsetEntry[count]       offsetEntries
(Variable)    storage for bitmap sets


offsetEntry:

UInt32        offset                   offset from table start to bitmap set


bitmap set:

USHORT        size                     height and width in pixels
USHORT        resolution               ?
offsetRecord  offsetRecord[]
(Variable)    storage for bitmaps


offsetRecord:

ULONG         bitmapOffset             offset from start of bitmap set to individual bitmap


bitmap:

SInt16        reserved                 00 00
SInt16        reserved                       00 00
char[4]       format                   data type, e.g. "png "
(Variable)    bitmap data
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
  numSets:         L    # Number of bitmap strikes to follow
"""
sbixHeaderFormatSize = sstruct.calcsize(sbixHeaderFormat)


sbixBitmapSetOffsetFormat = """
	>
	offset:          L    # 00 00 00 10 # offset from table start to each bitmap set
"""
sbixBitmapSetOffsetFormatSize = sstruct.calcsize(sbixBitmapSetOffsetFormat)


class table__s_b_i_x(DefaultTable.DefaultTable):
	def __init__(self, tag):
		self.tableTag = tag
		self.version = 1
		self.flags = 1
		self.numSets = 0
		self.bitmapSets = {}
		self.bitmapSetOffsets = []

	def decompile(self, data, ttFont):
		# read table header
		sstruct.unpack(sbixHeaderFormat, data[ : sbixHeaderFormatSize], self)
		# collect offsets to individual bitmap sets in self.bitmapSetOffsets
		for i in range(self.numSets):
			myOffset = sbixHeaderFormatSize + i * sbixBitmapSetOffsetFormatSize
			offsetEntry = sbixBitmapSetOffset()
			sstruct.unpack(sbixBitmapSetOffsetFormat, \
				data[myOffset : myOffset+sbixBitmapSetOffsetFormatSize], \
				offsetEntry)
			self.bitmapSetOffsets.append(offsetEntry.offset)

		# decompile BitmapSets
		for i in range(self.numSets-1, -1, -1):
			myBitmapSet = BitmapSet(rawdata=data[self.bitmapSetOffsets[i]:])
			data = data[:self.bitmapSetOffsets[i]]
			myBitmapSet.decompile(ttFont)
			#print "  BitmapSet length: %xh" % len(bitmapSetData)
			#print "Number of Bitmaps:", myBitmapSet.numBitmaps
			if myBitmapSet.size in self.bitmapSets:
				from fontTools import ttLib
				raise ttLib.TTLibError("Pixel 'size' must be unique for each BitmapSet")
			self.bitmapSets[myBitmapSet.size] = myBitmapSet

		# after the bitmaps have been extracted, we don't need the offsets anymore
		del self.bitmapSetOffsets

	def compile(self, ttFont):
		sbixData = ""
		self.numSets = len(self.bitmapSets)
		sbixHeader = sstruct.pack(sbixHeaderFormat, self)

		# calculate offset to start of first bitmap set
		setOffset = sbixHeaderFormatSize + sbixBitmapSetOffsetFormatSize * self.numSets

		for si in sorted(self.bitmapSets.keys()):
			myBitmapSet = self.bitmapSets[si]
			myBitmapSet.compile(ttFont)
			# append offset to this bitmap set to table header
			myBitmapSet.offset = setOffset
			sbixHeader += sstruct.pack(sbixBitmapSetOffsetFormat, myBitmapSet)
			setOffset += len(myBitmapSet.data)
			sbixData += myBitmapSet.data

		return sbixHeader + sbixData

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.simpletag("version", value=self.version)
		xmlWriter.newline()
		xmlWriter.simpletag("flags", value=self.flags)
		xmlWriter.newline()
		for i in sorted(self.bitmapSets.keys()):
			self.bitmapSets[i].toXML(xmlWriter, ttFont)

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["version", "flags"]:
			setattr(self, name, int(attrs["value"]))
		elif name == "bitmapSet":
			myBitmapSet = BitmapSet()
			for element in content:
				if isinstance(element, tuple):
					name, attrs, content = element
					myBitmapSet.fromXML(name, attrs, content, ttFont)
			self.bitmapSets[myBitmapSet.size] = myBitmapSet
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)


# Helper classes

class sbixBitmapSetOffset(object):
	pass
