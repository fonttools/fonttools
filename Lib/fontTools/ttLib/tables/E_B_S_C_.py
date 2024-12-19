from fontTools.misc import sstruct
from . import DefaultTable
from fontTools.misc.textTools import bytesjoin, safeEval
import logging

log = logging.getLogger(__name__)

ebscHeaderFormat = """
	> # big endian
	version:  16.16F
	numSizes: I
"""
# The compound type for hori and vert.
sbitLineMetricsFormat = """
	> # big endian
	ascender:              b
	descender:             b
	widthMax:              B
	caretSlopeNumerator:   b
	caretSlopeDenominator: b
	caretOffset:           b
	minOriginSB:           b
	minAdvanceSB:          b
	maxBeforeBL:           b
	minAfterBL:            b
	pad1:                  b
	pad2:                  b
"""
# remaining data
bitmapScaleTableFormatRemains = """
	> # big endian
	ppemX:                 B
	ppemY:                 B
	substitutePpemX:       B
	substitutePpemY:       B
"""


class table_E_B_S_C_(DefaultTable.DefaultTable):

    def decompile(self, data, ttFont):
        dummy, data = sstruct.unpack2(ebscHeaderFormat, data, self)

        self.bitmapScales = []
        for curScaleIndex in range(self.numSizes):
            curTable = BitmapScale()
            self.bitmapScales.append(curTable)
            for metric in ("hori", "vert"):
                metricObj = SbitLineMetrics()
                vars(curTable)[metric] = metricObj
                dummy, data = sstruct.unpack2(
                    sbitLineMetricsFormat, data, metricObj
                )
            dummy, data = sstruct.unpack2(
                bitmapScaleTableFormatRemains, data, curTable
            )

    def compile(self, ttFont):
        dataList = []
        self.numSizes = len(self.bitmapScales)
        dataList.append(sstruct.pack(ebscHeaderFormat, self))

        for curTable in self.bitmapScales:
            for metric in ("hori", "vert"):
                metricObj = vars(curTable)[metric]
                data = sstruct.pack(sbitLineMetricsFormat, metricObj)
                dataList.append(data)
            data = sstruct.pack(bitmapScaleTableFormatRemains, curTable)
            dataList.append(data)

        return bytesjoin(dataList)

    def toXML(self, writer, ttFont):
        writer.simpletag("header", [("version", self.version)])
        writer.newline()
        for curScale in self.bitmapScales:
            curScale.toXML(writer, ttFont)

    def fromXML(self, name, attrs, content, ttFont):
        if name == "header":
            self.version = safeEval(attrs["version"])
        elif name == "strike":
            if not hasattr(self, "bitmapScales"):
                self.bitmapScales = []
            curScale = BitmapScale()
            curScale.fromXML(name, attrs, content, ttFont, self)


class BitmapScale(object):
    # Returns all the simple metric names that bitmap size table
    # cares about in terms of XML creation.
    def _getXMLMetricNames(self):
        return sstruct.getformat(bitmapScaleTableFormatRemains)[1]

    def toXML(self, writer, ttFont):
        writer.begintag("BitmapScale")
        writer.newline()
        for metric in ("hori", "vert"):
            getattr(self, metric).toXML(metric, writer, ttFont)
        for metricName in self._getXMLMetricNames():
            writer.simpletag(metricName, value=getattr(self, metricName))
            writer.newline()
        writer.endtag("BitmapScale")
        writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        # Create a lookup for all the simple names that make sense to
        # bitmap size table. Only read the information from these names.
        dataNames = set(self._getXMLMetricNames())
        for element in content:
            if not isinstance(element, tuple):
                continue
            name, attrs, content = element
            if name == "sbitLineMetrics":
                direction = attrs["direction"]
                assert direction in (
                    "hori",
                    "vert",
                ), "SbitLineMetrics direction specified invalid."
                metricObj = SbitLineMetrics()
                metricObj.fromXML(name, attrs, content, ttFont)
                vars(self)[direction] = metricObj
            elif name in dataNames:
                vars(self)[name] = safeEval(attrs["value"])
            else:
                log.warning("unknown name '%s' being ignored in BitmapScale.", name)


class SbitLineMetrics(object):
    def toXML(self, name, writer, ttFont):
        writer.begintag("sbitLineMetrics", [("direction", name)])
        writer.newline()
        for metricName in sstruct.getformat(sbitLineMetricsFormat)[1]:
            writer.simpletag(metricName, value=getattr(self, metricName))
            writer.newline()
        writer.endtag("sbitLineMetrics")
        writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        metricNames = set(sstruct.getformat(sbitLineMetricsFormat)[1])
        for element in content:
            if not isinstance(element, tuple):
                continue
            name, attrs, content = element
            if name in metricNames:
                vars(self)[name] = safeEval(attrs["value"])

