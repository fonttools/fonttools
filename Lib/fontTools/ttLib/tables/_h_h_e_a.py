from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from . import DefaultTable


hheaFormat = """
		>  # big endian
		tableVersion:           16.16F
		ascent:                 h
		descent:                h
		lineGap:                h
		advanceWidthMax:        H
		minLeftSideBearing:     h
		minRightSideBearing:    h
		xMaxExtent:             h
		caretSlopeRise:         h
		caretSlopeRun:          h
		caretOffset:            h
		reserved0:              h
		reserved1:              h
		reserved2:              h
		reserved3:              h
		metricDataFormat:       h
		numberOfHMetrics:       H
"""


class table__h_h_e_a(DefaultTable.DefaultTable):
	
	dependencies = ['hmtx', 'glyf']
	
	def decompile(self, data, ttFont):
		sstruct.unpack(hheaFormat, data, self)
	
	def compile(self, ttFont):
		if ttFont.isLoaded('glyf') and ttFont.recalcBBoxes:
			self.recalc(ttFont)
		return sstruct.pack(hheaFormat, self)
	
	def recalc(self, ttFont):
		hmtxTable = ttFont['hmtx']
		if 'glyf' in ttFont:
			glyfTable = ttFont['glyf']
			INFINITY = 100000
			advanceWidthMax = 0
			minLeftSideBearing = +INFINITY  # arbitrary big number
			minRightSideBearing = +INFINITY # arbitrary big number
			xMaxExtent = -INFINITY          # arbitrary big negative number
			
			for name in ttFont.getGlyphOrder():
				width, lsb = hmtxTable[name]
				advanceWidthMax = max(advanceWidthMax, width)
				g = glyfTable[name]
				if g.numberOfContours == 0:
					continue
				if g.numberOfContours < 0 and not hasattr(g, "xMax"):
					# Composite glyph without extents set.
					# Calculate those.
					g.recalcBounds(glyfTable)
				minLeftSideBearing = min(minLeftSideBearing, lsb)
				rsb = width - lsb - (g.xMax - g.xMin)
				minRightSideBearing = min(minRightSideBearing, rsb)
				extent = lsb + (g.xMax - g.xMin)
				xMaxExtent = max(xMaxExtent, extent)

			if xMaxExtent == -INFINITY:
				# No glyph has outlines.
				minLeftSideBearing = 0
				minRightSideBearing = 0
				xMaxExtent = 0

			self.advanceWidthMax = advanceWidthMax
			self.minLeftSideBearing = minLeftSideBearing
			self.minRightSideBearing = minRightSideBearing
			self.xMaxExtent = xMaxExtent
		else:
			# XXX CFF recalc...
			pass
	
	def toXML(self, writer, ttFont):
		formatstring, names, fixes = sstruct.getformat(hheaFormat)
		for name in names:
			value = getattr(self, name)
			writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		setattr(self, name, safeEval(attrs["value"]))

