# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from . import DefaultTable
import struct


class table_C_P_A_L_(DefaultTable.DefaultTable):

	def decompile(self, data, ttFont):
		self.version, self.numPaletteEntries, numPalettes, numColorRecords, goffsetFirstColorRecord = struct.unpack(">HHHHL", data[:12])
		assert (self.version == 0), "Version of COLR table is higher than I know how to handle"
		self.palettes = []
		pos = 12
		for i in range(numPalettes):
			startIndex = struct.unpack(">H", data[pos:pos+2])[0]
			assert (startIndex + self.numPaletteEntries <= numColorRecords)
			pos += 2
			palette = []
			ppos = goffsetFirstColorRecord + startIndex * 4
			for j in range(self.numPaletteEntries):
				palette.append( Color(*struct.unpack(">BBBB", data[ppos:ppos+4])) )
				ppos += 4
			self.palettes.append(palette)

	def compile(self, ttFont):
		dataList = [struct.pack(">HHHHL", self.version, self.numPaletteEntries, len(self.palettes), self.numPaletteEntries * len(self.palettes), 12+2*len(self.palettes))]
		for i in range(len(self.palettes)):
			dataList.append(struct.pack(">H", i*self.numPaletteEntries))
		for palette in self.palettes:
			assert(len(palette) == self.numPaletteEntries)
			for color in palette:
				dataList.append(struct.pack(">BBBB", color.blue,color.green,color.red,color.alpha))
		data = bytesjoin(dataList)
		return data

	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		writer.simpletag("numPaletteEntries", value=self.numPaletteEntries)
		writer.newline()
		for index, palette in enumerate(self.palettes):
			writer.begintag("palette", index=index)
			writer.newline()
			assert(len(palette) == self.numPaletteEntries)
			for cindex, color in enumerate(palette):
				color.toXML(writer, ttFont, cindex)
			writer.endtag("palette")
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "palettes"):
			self.palettes = []
		if name == "palette":
			palette = []
			for element in content:
				if isinstance(element, basestring):
					continue
			palette = []
			for element in content:
				if isinstance(element, basestring):
					continue
				color = Color()
				color.fromXML(element[0], element[1], element[2], ttFont)
				palette.append (color)
			self.palettes.append(palette)
		elif "value" in attrs:
			value =  safeEval(attrs["value"])
			setattr(self, name, value)

class Color(object):

	def __init__(self, blue=None, green=None, red=None, alpha=None):
		self.blue  = blue
		self.green = green
		self.red   = red
		self.alpha = alpha

	def hex(self):
		return "#%02X%02X%02X%02X" % (self.red, self.green, self.blue, self.alpha)

	def __repr__(self):
		return self.hex()

	def toXML(self, writer, ttFont, index=None):
		writer.simpletag("color", value=self.hex(), index=index)
		writer.newline()

	def fromXML(self, eltname, attrs, content, ttFont):
		value = attrs["value"]
		if value[0] == '#':
			value = value[1:]
		self.red   = int(value[0:2], 16)
		self.green = int(value[2:4], 16)
		self.blue  = int(value[4:6], 16)
		self.alpha = int(value[6:8], 16) if len (value) >= 8 else 0xFF
