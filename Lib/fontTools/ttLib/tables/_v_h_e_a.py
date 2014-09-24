from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from . import DefaultTable

vheaFormat = """
		>	# big endian
		tableVersion:		16.16F
		ascent:			h
		descent:		h
		lineGap:		h
		advanceHeightMax:	H
		minTopSideBearing:	h
		minBottomSideBearing:	h
		yMaxExtent:		h
		caretSlopeRise:		h
		caretSlopeRun:		h
		reserved0:		h
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
		self.recalc(ttFont)
		return sstruct.pack(vheaFormat, self)
	
	def recalc(self, ttFont):
		vtmxTable = ttFont['vmtx']
		if 'glyf' in ttFont:
			glyfTable = ttFont['glyf']
			INFINITY = 100000
			advanceHeightMax = 0
			minTopSideBearing = +INFINITY    # arbitrary big number
			minBottomSideBearing = +INFINITY # arbitrary big number
			yMaxExtent = -INFINITY           # arbitrary big negative number

			for name in ttFont.getGlyphOrder():
				height, tsb = vtmxTable[name]
				advanceHeightMax = max(advanceHeightMax, height)
				g = glyfTable[name]
				if g.numberOfContours == 0:
					continue
				if g.numberOfContours < 0 and not hasattr(g, "yMax"):
					# Composite glyph without extents set.
					# Calculate those.
					g.recalcBounds(glyfTable)
				minTopSideBearing = min(minTopSideBearing, tsb)
				bsb = height - tsb - (g.yMax - g.yMin)
				minBottomSideBearing = min(minBottomSideBearing, bsb)
				extent = tsb + (g.yMax - g.yMin)
				yMaxExtent = max(yMaxExtent, extent)

			if yMaxExtent == -INFINITY:
				# No glyph has outlines.
				minTopSideBearing = 0
				minBottomSideBearing = 0
				yMaxExtent = 0

			self.advanceHeightMax = advanceHeightMax
			self.minTopSideBearing = minTopSideBearing
			self.minBottomSideBearing = minBottomSideBearing
			self.yMaxExtent = yMaxExtent
		else:
			# XXX CFF recalc...
			pass
	
	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(vheaFormat)
		for name in names:
			value = getattr(self, name)
			writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		setattr(self, name, safeEval(attrs["value"]))

