from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from . import DefaultTable
from .sbixBitmap import *
from .sbixBitmapSet import *
import struct

"""
sbix Table organization:

USHORT        version?
USHORT        version?
USHORT        count                    number of bitmap sets
offsetEntry   offsetEntry[count]       offsetEntries
(Variable)    storage for bitmap sets


offsetEntry:

ULONG         offset                   offset from table start to bitmap set


bitmap set:

USHORT        size                     height and width in pixels
USHORT        resolution               ?
offsetRecord  offsetRecord[]
(Variable)    storage for bitmaps


offsetRecord:

ULONG         bitmapOffset             offset from start of bitmap set to individual bitmap


bitmap:

ULONG         reserved                 00 00 00 00
char[4]       format                   data type, e.g. "png "
(Variable)    bitmap data
"""

sbixHeaderFormat = """
	>
	usVal1:          H    # 00 01
	usVal2:          H    #       00 01
	numSets:         L    # 00 00 00 02 # number of bitmap sets
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
		self.usVal1 = 1
		self.usVal2 = 1
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
			setOffset += sbixBitmapSetHeaderFormatSize + len(myBitmapSet.data)
			sbixData += myBitmapSet.data

		return sbixHeader + sbixData

	def toXML(self, xmlWriter, ttFont):
		xmlWriter.simpletag("usVal1", value=self.usVal1)
		xmlWriter.newline()
		xmlWriter.simpletag("usVal2", value=self.usVal2)
		xmlWriter.newline()
		for i in sorted(self.bitmapSets.keys()):
			self.bitmapSets[i].toXML(xmlWriter, ttFont)

	def fromXML(self, name, attrs, content, ttFont):
		if name in ["usVal1", "usVal2"]:
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
