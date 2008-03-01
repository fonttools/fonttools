import sys
import DefaultTable
import Numeric
from fontTools import ttLib
from fontTools.misc.textTools import safeEval


class table__h_m_t_x(DefaultTable.DefaultTable):
	
	headerTag = 'hhea'
	advanceName = 'width'
	sideBearingName = 'lsb'
	numberOfMetricsName = 'numberOfHMetrics'
	
	def decompile(self, data, ttFont):
		numberOfMetrics = int(getattr(ttFont[self.headerTag], self.numberOfMetricsName))
		metrics = Numeric.fromstring(data[:4 * numberOfMetrics], 
				Numeric.Int16)
		if sys.byteorder <> "big":
			metrics = metrics.byteswapped()
		metrics.shape = (numberOfMetrics, 2)
		data = data[4 * numberOfMetrics:]
		numberOfSideBearings = ttFont['maxp'].numGlyphs - numberOfMetrics
		numberOfSideBearings = int(numberOfSideBearings)
		if numberOfSideBearings:
			assert numberOfSideBearings > 0, "bad hmtx/vmtx table"
			lastAdvance = metrics[-1][0]
			advances = Numeric.array([lastAdvance] * numberOfSideBearings, 
					Numeric.Int16)
			sideBearings = Numeric.fromstring(data[:2 * numberOfSideBearings], 
					Numeric.Int16)
			if sys.byteorder <> "big":
				sideBearings = sideBearings.byteswapped()
			data = data[2 * numberOfSideBearings:]
			additionalMetrics = Numeric.array([advances, sideBearings], 
					Numeric.Int16)
			metrics = Numeric.concatenate((metrics, 
					Numeric.transpose(additionalMetrics)))
		if data:
			sys.stderr.write("too much data for hmtx/vmtx table\n")
		metrics = metrics.tolist()
		self.metrics = {}
		for i in range(len(metrics)):
			glyphName = ttFont.getGlyphName(i)
			self.metrics[glyphName] = metrics[i]
	
	def compile(self, ttFont):
		metrics = []
		for glyphName in ttFont.getGlyphOrder():
			metrics.append(self.metrics[glyphName])
		lastAdvance = metrics[-1][0]
		lastIndex = len(metrics)
		while metrics[lastIndex-2][0] == lastAdvance:
			lastIndex = lastIndex - 1
			if lastIndex <= 1:
				# all advances are equal
				lastIndex = 1
				break
		additionalMetrics = metrics[lastIndex:]
		additionalMetrics = map(lambda (advance, sb): sb, additionalMetrics)
		metrics = metrics[:lastIndex]
		setattr(ttFont[self.headerTag], self.numberOfMetricsName, len(metrics))
		
		metrics = Numeric.array(metrics, Numeric.Int16)
		if sys.byteorder <> "big":
			metrics = metrics.byteswapped()
		data = metrics.tostring()
		
		additionalMetrics = Numeric.array(additionalMetrics, Numeric.Int16)
		if sys.byteorder <> "big":
			additionalMetrics = additionalMetrics.byteswapped()
		data = data + additionalMetrics.tostring()
		return data
	
	def toXML(self, writer, ttFont):
		names = self.metrics.keys()
		names.sort()
		for glyphName in names:
			advance, sb = self.metrics[glyphName]
			writer.simpletag("mtx", [
					("name", glyphName), 
					(self.advanceName, advance), 
					(self.sideBearingName, sb),
					])
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if not hasattr(self, "metrics"):
			self.metrics = {}
		if name == "mtx":
			self.metrics[attrs["name"]] = [safeEval(attrs[self.advanceName]), 
					safeEval(attrs[self.sideBearingName])]
	
	def __getitem__(self, glyphName):
		return self.metrics[glyphName]
	
	def __setitem__(self, glyphName, (advance, sb)):
		self.metrics[glyphName] = advance, sb

