from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.misc.fixedTools import (
	ensureVersionIsLong as fi2ve, versionToFixed as ve2fi)
from . import DefaultTable

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

	dependencies = ['vmtx', 'glyf']

	def decompile(self, data, ttFont):
		sstruct.unpack(vheaFormat, data, self)

	def compile(self, ttFont):
		if ttFont.isLoaded('glyf') and ttFont.recalcBBoxes:
			self.recalc(ttFont)
		self.tableVersion = fi2ve(self.tableVersion)
		return sstruct.pack(vheaFormat, self)

	def recalc(self, ttFont):
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
		else:
			# XXX CFF recalc...
			pass

		advanceHeightMax = 0
		minTopSideBearing = float('inf')
		minBottomSideBearing = float('inf')
		yMaxExtent = -float('inf')

		vmtxTable = ttFont['vmtx']
		for name, boundsHeight in boundsHeightDict.items():
			advanceHeight, tsb = vmtxTable[name]
			advanceHeightMax = max(advanceHeightMax, advanceHeight)
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

		self.advanceHeightMax = advanceHeightMax
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
