from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import (
    fixedToFloat as fi2fl,
    floatToFixed as fl2fi,
    floatToFixedToStr as fl2str,
    strToFixedToFloat as str2fl,
)
from fontTools.misc.textTools import safeEval
from fontTools.ttLib import TTLibError
from . import DefaultTable
import array
import struct
import logging


log = logging.getLogger(__name__)

# Apple's documentation of 'avar':
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6avar.html

AVAR_HEADER_FORMAT = """
    > # big endian
    majorVersion:  H
    minorVersion:  H
    reserved:      H
    axisCount:     H
"""
assert sstruct.calcsize(AVAR_HEADER_FORMAT) == 8, sstruct.calcsize(AVAR_HEADER_FORMAT)


class table__a_v_a_r(DefaultTable.DefaultTable):

    dependencies = ["fvar"]

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.segments = {}

    def compile(self, ttFont):
        axisIds = [axis.axisId for axis in ttFont["fvar"].axes]
        header = {
            "majorVersion": 1,
            "minorVersion": 0,
            "reserved": 0,
            "axisCount": len(axisIds)
        }
        result = [sstruct.pack(AVAR_HEADER_FORMAT, header)]
        for axisId in axisIds:
            mappings = sorted(self.segments[axisId].items())
            result.append(struct.pack(">H", len(mappings)))
            for key, value in mappings:
                fixedKey = fl2fi(key, 14)
                fixedValue = fl2fi(value, 14)
                result.append(struct.pack(">hh", fixedKey, fixedValue))
        return bytesjoin(result)

    def decompile(self, data, ttFont):
        axisIds = [axis.axisId for axis in ttFont["fvar"].axes]
        header = {}
        headerSize = sstruct.calcsize(AVAR_HEADER_FORMAT)
        header = sstruct.unpack(AVAR_HEADER_FORMAT, data[0:headerSize])
        majorVersion = header["majorVersion"]
        if majorVersion != 1:
            raise TTLibError("unsupported 'avar' version %d" % majorVersion)
        pos = headerSize
        for axisId in axisIds:
            segments = self.segments[axisId] = {}
            numPairs = struct.unpack(">H", data[pos:pos+2])[0]
            pos = pos + 2
            for _ in range(numPairs):
                fromValue, toValue = struct.unpack(">hh", data[pos:pos+4])
                segments[fi2fl(fromValue, 14)] = fi2fl(toValue, 14)
                pos = pos + 4

    def toXML(self, writer, ttFont):
        axisIds = [axis.axisId for axis in ttFont["fvar"].axes]
        for axisId in axisIds:
            writer.begintag("segment", axis=axisId)
            writer.newline()
            for key, value in sorted(self.segments[axisId].items()):
                key = fl2str(key, 14)
                value = fl2str(value, 14)
                writer.simpletag("mapping", **{"from": key, "to": value})
                writer.newline()
            writer.endtag("segment")
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "segment":
            axisId = attrs["axis"]
            segment = self.segments[axisId] = {}
            for element in content:
                if isinstance(element, tuple):
                    elementName, elementAttrs, _ = element
                    if elementName == "mapping":
                        fromValue = str2fl(elementAttrs["from"], 14)
                        toValue = str2fl(elementAttrs["to"], 14)
                        if fromValue in segment:
                            log.warning("duplicate entry for %s in axis '%s'",
                                        fromValue, axisId)
                        segment[fromValue] = toValue
