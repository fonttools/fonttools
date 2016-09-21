from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import getSearchRange
from fontTools.misc.textTools import safeEval, readHex
from fontTools.misc.fixedTools import fixedToFloat as fi2fl, floatToFixed as fl2fi
from . import DefaultTable
import struct
import sys
import array
import logging


log = logging.getLogger(__name__)


class table__k_e_r_n(DefaultTable.DefaultTable):

	def getkern(self, format):
		for subtable in self.kernTables:
			if subtable.version == format:
				return subtable
		return None  # not found

	def decompile(self, data, ttFont):
		version, nTables = struct.unpack(">HH", data[:4])
		apple = False
		if (len(data) >= 8) and (version == 1):
			# AAT Apple's "new" format. Hm.
			version, nTables = struct.unpack(">LL", data[:8])
			self.version = fi2fl(version, 16)
			data = data[8:]
			apple = True
		else:
			self.version = version
			data = data[4:]
		tablesIndex = []
		self.kernTables = []
		for i in range(nTables):
			if self.version == 1.0:
				# Apple
				length, coverage, tupleIndex = struct.unpack(">lHH", data[:8])
				version = coverage & 0xff
			else:
				version, length = struct.unpack(">HH", data[:4])
			length = int(length)
			if version not in kern_classes:
				subtable = KernTable_format_unkown(version)
			else:
				subtable = kern_classes[version]()
			subtable.apple = apple
			subtable.decompile(data[:length], ttFont)
			self.kernTables.append(subtable)
			data = data[length:]

	def compile(self, ttFont):
		if hasattr(self, "kernTables"):
			nTables = len(self.kernTables)
		else:
			nTables = 0
		if self.version == 1.0:
			# AAT Apple's "new" format.
			data = struct.pack(">ll", fl2fi(self.version, 16), nTables)
		else:
			data = struct.pack(">HH", self.version, nTables)
		if hasattr(self, "kernTables"):
			for subtable in self.kernTables:
				data = data + subtable.compile(ttFont)
		return data

	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		for subtable in self.kernTables:
			subtable.toXML(writer, ttFont)

	def fromXML(self, name, attrs, content, ttFont):
		if name == "version":
			self.version = safeEval(attrs["value"])
			return
		if name != "kernsubtable":
			return
		if not hasattr(self, "kernTables"):
			self.kernTables = []
		format = safeEval(attrs["format"])
		if format not in kern_classes:
			subtable = KernTable_format_unkown(format)
		else:
			subtable = kern_classes[format]()
		self.kernTables.append(subtable)
		subtable.fromXML(name, attrs, content, ttFont)


class KernTable_format_0(object):

	def decompile(self, data, ttFont):
		version, length, coverage = (0,0,0)
		if not self.apple:
			version, length, coverage = struct.unpack(">HHH", data[:6])
			data = data[6:]
		else:
			version, length, coverage = struct.unpack(">LHH", data[:8])
			data = data[8:]
		self.version, self.coverage = int(version), int(coverage)

		self.kernTable = kernTable = {}

		nPairs, searchRange, entrySelector, rangeShift = struct.unpack(">HHHH", data[:8])
		data = data[8:]

		nPairs = min(nPairs, len(data) // 6)
		datas = array.array("H", data[:6 * nPairs])
		if sys.byteorder != "big":
			datas.byteswap()
		it = iter(datas)
		glyphOrder = ttFont.getGlyphOrder()
		for k in range(nPairs):
			left, right, value = next(it), next(it), next(it)
			if value >= 32768: value -= 65536
			try:
				kernTable[(glyphOrder[left], glyphOrder[right])] = value
			except IndexError:
				# Slower, but will not throw an IndexError on an invalid glyph id.
				kernTable[(ttFont.getGlyphName(left), ttFont.getGlyphName(right))] = value
		if len(data) > 6 * nPairs + 4: # Ignore up to 4 bytes excess
			log.warning("excess data in 'kern' subtable: %d bytes", len(data) - 6 * nPairs)

	def compile(self, ttFont):
		nPairs = len(self.kernTable)
		searchRange, entrySelector, rangeShift = getSearchRange(nPairs, 6)
		data = struct.pack(">HHHH", nPairs, searchRange, entrySelector, rangeShift)

		# yeehee! (I mean, turn names into indices)
		try:
			reverseOrder = ttFont.getReverseGlyphMap()
			kernTable = sorted((reverseOrder[left], reverseOrder[right], value) for ((left,right),value) in self.kernTable.items())
		except KeyError:
			# Slower, but will not throw KeyError on invalid glyph id.
			getGlyphID = ttFont.getGlyphID
			kernTable = sorted((getGlyphID(left), getGlyphID(right), value) for ((left,right),value) in self.kernTable.items())

		for left, right, value in kernTable:
			data = data + struct.pack(">HHh", left, right, value)
		return struct.pack(">HHH", self.version, len(data) + 6, self.coverage) + data

	def toXML(self, writer, ttFont):
		writer.begintag("kernsubtable", coverage=self.coverage, format=0)
		writer.newline()
		items = sorted(self.kernTable.items())
		for (left, right), value in items:
			writer.simpletag("pair", [
					("l", left),
					("r", right),
					("v", value)
					])
			writer.newline()
		writer.endtag("kernsubtable")
		writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		self.coverage = safeEval(attrs["coverage"])
		self.version = safeEval(attrs["format"])
		if not hasattr(self, "kernTable"):
			self.kernTable = {}
		for element in content:
			if not isinstance(element, tuple):
				continue
			name, attrs, content = element
			self.kernTable[(attrs["l"], attrs["r"])] = safeEval(attrs["v"])

	def __getitem__(self, pair):
		return self.kernTable[pair]

	def __setitem__(self, pair, value):
		self.kernTable[pair] = value

	def __delitem__(self, pair):
		del self.kernTable[pair]


class KernTable_format_unkown(object):

	def __init__(self, format):
		self.format = format

	def decompile(self, data, ttFont):
		self.data = data

	def compile(self, ttFont):
		return self.data

	def toXML(self, writer, ttFont):
		writer.begintag("kernsubtable", format=self.format)
		writer.newline()
		writer.comment("unknown 'kern' subtable format")
		writer.newline()
		writer.dumphex(self.data)
		writer.endtag("kernsubtable")
		writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		self.decompile(readHex(content), ttFont)


kern_classes = {0: KernTable_format_0}
