import DefaultTable
import sstruct
from fontTools.misc.textTools import safeEval


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
		if ttFont.has_key('glyf'):
			glyfTable = ttFont['glyf']
			advanceWidthMax = -100000    # arbitrary big negative number
			minLeftSideBearing = 100000  # arbitrary big number
			minRightSideBearing = 100000 # arbitrary big number
			xMaxExtent = -100000         # arbitrary big negative number
			
			for name in ttFont.getGlyphOrder():
				width, lsb = hmtxTable[name]
				g = glyfTable[name]
				if g.numberOfContours <= 0:
					continue
				advanceWidthMax = max(advanceWidthMax, width)
				minLeftSideBearing = min(minLeftSideBearing, lsb)
				rsb = width - lsb - (g.xMax - g.xMin)
				minRightSideBearing = min(minRightSideBearing, rsb)
				extent = lsb + (g.xMax - g.xMin)
				xMaxExtent = max(xMaxExtent, extent)
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
			if type(value) == type(0L):
				value = int(value)
			writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		setattr(self, name, safeEval(attrs["value"]))

