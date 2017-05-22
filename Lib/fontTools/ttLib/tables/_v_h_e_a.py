from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.misc.fixedTools import (
	ensureVersionIsLong as fi2ve, versionToFixed as ve2fi)
from . import DefaultTable
import math


vheaFormat = """
		>	# big endian
		tableVersion:		L
		ascent:			h
		descent:		h
		lineGap:		h
		advanceHeightMax:	H
		minTopSideBearing:	h
		minBottomSideBearing:	h
		yMaxExtent:		h
		caretSlopeRise:		h
		caretSlopeRun:		h
		caretOffset:		h
		reserved1:		h
		reserved2:		h
		reserved3:		h
		reserved4:		h
		metricDataFormat:	h
		numberOfVMetrics:	H
"""

class table__v_h_e_a(DefaultTable.DefaultTable):

	# Note: Keep in sync with table__h_h_e_a

	dependencies = ['vmtx', 'glyf', 'CFF ']

	def decompile(self, data, ttFont):
		sstruct.unpack(vheaFormat, data, self)

	def compile(self, ttFont):
		if ttFont.recalcBBoxes and (ttFont.isLoaded('glyf') or ttFont.isLoaded('CFF ')):
			self.recalc(ttFont)
		self.tableVersion = fi2ve(self.tableVersion)
		return sstruct.pack(vheaFormat, self)

	def recalc(self, ttFont):
		vmtxTable = ttFont['vmtx']
		self.advanceHeightMax = max(adv for adv, _ in vmtxTable.metrics.values())

		boundsHeightDict = {}
		if 'glyf' in ttFont:
			glyfTable = ttFont['glyf']
			for name in ttFont.getGlyphOrder():
				g = glyfTable[name]
				if g.numberOfContours == 0:
					continue
				if g.numberOfContours < 0 and not hasattr(g, "yMax"):
					# Composite glyph without extents set.
					# Calculate those.
					g.recalcBounds(glyfTable)
				boundsHeightDict[name] = g.yMax - g.yMin
		elif 'CFF ' in ttFont:
			topDict = ttFont['CFF '].cff.topDictIndex[0]
			for name in ttFont.getGlyphOrder():
				cs = topDict.CharStrings[name]
				if not hasattr(cs, 'bounds'):
					cs.recalcBounds()
				if cs.bounds is None:
					continue
				boundsHeightDict[name] = math.ceil(cs.bounds[3]) - math.floor(cs.bounds[1])

		minTopSideBearing = float('inf')
		minBottomSideBearing = float('inf')
		yMaxExtent = -float('inf')

		for name, boundsHeight in boundsHeightDict.items():
			advanceHeight, tsb = vmtxTable[name]
			minTopSideBearing = min(minTopSideBearing, tsb)
			bsb = advanceHeight - tsb - boundsHeight
			minBottomSideBearing = min(minBottomSideBearing, bsb)
			extent = tsb + boundsHeight
			yMaxExtent = max(yMaxExtent, extent)

		if yMaxExtent == -float('inf'):
			# No glyph has outlines.
			minTopSideBearing = 0
			minBottomSideBearing = 0
			yMaxExtent = 0

		self.minTopSideBearing = minTopSideBearing
		self.minBottomSideBearing = minBottomSideBearing
		self.yMaxExtent = yMaxExtent

	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(vheaFormat)
		for name in names:
			value = getattr(self, name)
			if name == "tableVersion":
				value = fi2ve(value)
				value = "0x%08x" % value
			writer.simpletag(name, value=value)
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if name == "tableVersion":
			setattr(self, name, ve2fi(attrs["value"]))
			return
		setattr(self, name, safeEval(attrs["value"]))

	# reserved0 is caretOffset for legacy reasons
	@property
	def reserved0(self):
		return self.caretOffset

	@reserved0.setter
	def reserved0(self, value):
		self.caretOffset = value
