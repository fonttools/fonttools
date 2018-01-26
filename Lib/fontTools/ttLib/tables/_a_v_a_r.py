from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc import sstruct
from fontTools.misc.fixedTools import fixedToFloat, floatToFixed
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
        axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
        header = {
            "majorVersion": 1,
            "minorVersion": 0,
            "reserved": 0,
            "axisCount": len(axisTags)
        }
        result = [sstruct.pack(AVAR_HEADER_FORMAT, header)]
        for axis in axisTags:
            mappings = sorted(self.segments[axis].items())
            result.append(struct.pack(">H", len(mappings)))
            for key, value in mappings:
                fixedKey = floatToFixed(key, 14)
                fixedValue = floatToFixed(value, 14)
                result.append(struct.pack(">hh", fixedKey, fixedValue))
        return bytesjoin(result)

    def decompile(self, data, ttFont):
        axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
        header = {}
        headerSize = sstruct.calcsize(AVAR_HEADER_FORMAT)
        header = sstruct.unpack(AVAR_HEADER_FORMAT, data[0:headerSize])
        majorVersion = header["majorVersion"]
        if majorVersion != 1:
            raise TTLibError("unsupported 'avar' version %d" % majorVersion)
        pos = headerSize
        for axis in axisTags:
            segments = self.segments[axis] = {}
            numPairs = struct.unpack(">H", data[pos:pos+2])[0]
            pos = pos + 2
            for _ in range(numPairs):
                fromValue, toValue = struct.unpack(">hh", data[pos:pos+4])
                segments[fixedToFloat(fromValue, 14)] = fixedToFloat(toValue, 14)
                pos = pos + 4

    def toXML(self, writer, ttFont):
        axisTags = [axis.axisTag for axis in ttFont["fvar"].axes]
        for axis in axisTags:
            writer.begintag("segment", axis=axis)
            writer.newline()
            for key, value in sorted(self.segments[axis].items()):
                # roundtrip float -> fixed -> float to normalize TTX output
                # as dumped after decompiling or straight from varLib
                key = fixedToFloat(floatToFixed(key, 14), 14)
                value = fixedToFloat(floatToFixed(value, 14), 14)
                writer.simpletag("mapping", **{"from": key, "to": value})
                writer.newline()
            writer.endtag("segment")
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "segment":
            axis = attrs["axis"]
            segment = self.segments[axis] = {}
            for element in content:
                if isinstance(element, tuple):
                    elementName, elementAttrs, _ = element
                    if elementName == "mapping":
                        fromValue = safeEval(elementAttrs["from"])
                        toValue = safeEval(elementAttrs["to"])
                        if fromValue in segment:
                            log.warning("duplicate entry for %s in axis '%s'",
                                        fromValue, axis)
                        segment[fromValue] = toValue
