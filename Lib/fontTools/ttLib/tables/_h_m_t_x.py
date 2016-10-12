from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from . import DefaultTable
import sys
import struct
import array
import logging


log = logging.getLogger(__name__)


class table__h_m_t_x(DefaultTable.DefaultTable):

	headerTag = 'hhea'
	advanceName = 'width'
	sideBearingName = 'lsb'
	numberOfMetricsName = 'numberOfHMetrics'

	def decompile(self, data, ttFont):
		numGlyphs = ttFont['maxp'].numGlyphs
		numberOfMetrics = int(getattr(ttFont[self.headerTag], self.numberOfMetricsName))
		if numberOfMetrics > numGlyphs:
			numberOfMetrics = numGlyphs  # We warn later.
		if len(data) < 4 * numberOfMetrics:
			raise ttLib.TTLibError("not enough '%s' table data" % self.tableTag)
		# Note: advanceWidth is unsigned, but some font editors might
		# read/write as signed. We can't be sure whether it was a mistake
		# or not, so we read as unsigned but also issue a warning...
		longHorMetricFormat = ">" + "Hh"*numberOfMetrics
		metrics = struct.unpack(longHorMetricFormat, data[:4 * numberOfMetrics])
		data = data[4 * numberOfMetrics:]
		numberOfSideBearings = numGlyphs - numberOfMetrics
		sideBearings = array.array("h", data[:2 * numberOfSideBearings])
		data = data[2 * numberOfSideBearings:]

		if sys.byteorder != "big":
			sideBearings.byteswap()
		if data:
			log.warning("too much '%s' table data" % self.tableTag)
		self.metrics = {}
		glyphOrder = ttFont.getGlyphOrder()
		for i in range(numberOfMetrics):
			glyphName = glyphOrder[i]
			advanceWidth, lsb = metrics[i*2:i*2+2]
			if advanceWidth > 32767:
				log.warning(
					"Glyph %r has a huge advance %s (%d); is it intentional or "
					"an (invalid) negative value?", glyphName, self.advanceName,
					advanceWidth)
			self.metrics[glyphName] = [advanceWidth, lsb]
		lastAdvance = metrics[-2]
		for i in range(numberOfSideBearings):
			glyphName = glyphOrder[i + numberOfMetrics]
			self.metrics[glyphName] = [lastAdvance, sideBearings[i]]

	def compile(self, ttFont):
		metrics = []
		for glyphName in ttFont.getGlyphOrder():
			metrics.append(self.metrics[glyphName])
		lastAdvance = metrics[-1][0]
		lastIndex = len(metrics)
		while metrics[lastIndex-2][0] == lastAdvance:
			lastIndex -= 1
			if lastIndex <= 1:
				# all advances are equal
				lastIndex = 1
				break
		additionalMetrics = metrics[lastIndex:]
		additionalMetrics = [sb for advance, sb in additionalMetrics]
		metrics = metrics[:lastIndex]
		numberOfMetrics = len(metrics)
		setattr(ttFont[self.headerTag], self.numberOfMetricsName, numberOfMetrics)

		allMetrics = []
		for item in metrics:
			allMetrics.extend(item)
		longHorMetricFormat = ">" + "Hh"*numberOfMetrics
		data = struct.pack(longHorMetricFormat, *allMetrics)

		additionalMetrics = array.array("h", additionalMetrics)
		if sys.byteorder != "big":
			additionalMetrics.byteswap()
		data = data + additionalMetrics.tostring()
		return data

	def toXML(self, writer, ttFont):
		names = sorted(self.metrics.keys())
		for glyphName in names:
			advance, sb = self.metrics[glyphName]
			writer.simpletag("mtx", [
					("name", glyphName),
					(self.advanceName, advance),
					(self.sideBearingName, sb),
					])
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "metrics"):
			self.metrics = {}
		if name == "mtx":
			self.metrics[attrs["name"]] = [safeEval(attrs[self.advanceName]),
					safeEval(attrs[self.sideBearingName])]

	def __delitem__(self, glyphName):
		del self.metrics[glyphName]

	def __getitem__(self, glyphName):
		return self.metrics[glyphName]

	def __setitem__(self, glyphName, advance_sb_pair):
		self.metrics[glyphName] = tuple(advance_sb_pair)
