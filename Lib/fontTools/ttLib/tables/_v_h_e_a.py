from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from . import DefaultTable

vheaFormat = """
		>	# big endian
		tableVersion:			16.16F
		ascent:					h
		descent:				h
		lineGap:				h
		advanceHeightMax:		H
		minTopSideBearing:		h
		minBottomSideBearing:	h
		yMaxExtent:				h
		caretSlopeRise:			h
		caretSlopeRun:			h
		reserved0:				h
		reserved1:				h
		reserved2:				h
		reserved3:				h
		reserved4:				h
		metricDataFormat:		h
		numberOfVMetrics:		H
"""

class table__v_h_e_a(DefaultTable.DefaultTable):
	
	dependencies = ['vmtx', 'glyf']
	
	def decompile(self, data, ttFont):
		sstruct.unpack(vheaFormat, data, self)
	
	def compile(self, ttFont):
		self.recalc(ttFont)
		return sstruct.pack(vheaFormat, self)
	
	def recalc(self, ttFont):
		vtmxTable = ttFont['vmtx']
		if 'glyf' in ttFont:
			if not ttFont.isLoaded('glyf'):
				return
			glyfTable = ttFont['glyf']
			advanceHeightMax = -100000    # arbitrary big negative number
			minTopSideBearing = 100000    # arbitrary big number
			minBottomSideBearing = 100000 # arbitrary big number
			yMaxExtent = -100000          # arbitrary big negative number
			
			for name in ttFont.getGlyphOrder():
				height, tsb = vtmxTable[name]
				g = glyfTable[name]
				if g.numberOfContours <= 0:
					continue
				advanceHeightMax = max(advanceHeightMax, height)
				minTopSideBearing = min(minTopSideBearing, tsb)
				rsb = height - tsb - (g.yMax - g.yMin)
				minBottomSideBearing = min(minBottomSideBearing, rsb)
				extent = tsb + (g.yMax - g.yMin)
				yMaxExtent = max(yMaxExtent, extent)
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

