# Since bitmap glyph metrics are shared between EBLC and EBDT
# this class gets its own python file.
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval


bigGlyphMetricsFormat = """
  > # big endian
  height:       B
  width:        B
  horiBearingX: b
  horiBearingY: b
  horiAdvance:  B
  vertBearingX: b
  vertBearingY: b
  vertAdvance:  B
"""

smallGlyphMetricsFormat = """
  > # big endian
  height:   B
  width:    B
  BearingX: b
  BearingY: b
  Advance:  B
"""

class BitmapGlyphMetrics:

	def toXML(self, writer, ttFont):
		writer.begintag(self.__class__.__name__)
		writer.newline()
		for metricName in sstruct.getformat(self.__class__.binaryFormat)[1]:
			writer.simpletag(metricName, value=getattr(self, metricName))
			writer.newline()
		writer.endtag(self.__class__.__name__)
		writer.newline()

	def fromXML(self, args, ttFont):
		(name, attrs, content) = args
		metricNames = set(sstruct.getformat(self.__class__.binaryFormat)[1])
		for element in content:
			if type(element) != tuple:
				continue
			name, attrs, content = element
			# Make sure this is a metric that is needed by GlyphMetrics.
			if name in metricNames:
				vars(self)[name] = safeEval(attrs['value'])
			else:
				print("Warning: unknown name '%s' being ignored in %s." % name, self.__class__.__name__)


class BigGlyphMetrics(BitmapGlyphMetrics):
	binaryFormat = bigGlyphMetricsFormat
	
class SmallGlyphMetrics(BitmapGlyphMetrics):
	binaryFormat = smallGlyphMetricsFormat
