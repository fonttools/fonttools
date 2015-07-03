from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
from fontTools.ttLib import TTLibError
from . import DefaultTable

# Apple's documentation of 'meta':
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6meta.html

META_HEADER_FORMAT = """
    > # big endian
    version:     L
    flags:       L
    dataOffset:  L
    numDataMaps: L
"""

# According to Apple's spec, the dataMaps entries contain a dataOffset
# that is documented as "Offset from the beginning of the data section
# to the data for this tag". However, this is *not* the case with
# the fonts that Apple ships pre-installed on MacOS X Yosemite 10.10.4,
# and it also does not reflect how Apple's ftxdumperfuser tool is parsing
# the 'meta' table (tested ftxdumperfuser build 330, FontToolbox.framework
# build 187). Instead of what is claimed in the spec, the data maps contain
# a dataOffset relative to the very beginning of the 'meta' table.
# The dataOffset field of the 'meta' header apparently gets ignored.

DATA_MAP_FORMAT = """
    > # big endian
    tag:         4s
    dataOffset:  L
    dataLength:  L
"""


class table__m_e_t_a(DefaultTable.DefaultTable):
    def __init__(self, tag="meta"):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.data = {}

    def decompile(self, data, ttFont):
        headerSize = sstruct.calcsize(META_HEADER_FORMAT)
        header = sstruct.unpack(META_HEADER_FORMAT, data[0 : headerSize])
        if header["version"] != 1:
            raise TTLibError("unsupported 'meta' version %d" %
                             header["version"])
        dataMapSize = sstruct.calcsize(DATA_MAP_FORMAT)
        for i in range(header["numDataMaps"]):
            dataMapOffset = headerSize + i * dataMapSize
            dataMap = sstruct.unpack(
                DATA_MAP_FORMAT,
                data[dataMapOffset : dataMapOffset + dataMapSize])
            tag = dataMap["tag"]
            offset = dataMap["dataOffset"]
            self.data[tag] = data[offset : offset + dataMap["dataLength"]]

    def compile(self, ttFont):
        keys = sorted(self.data.keys())
        headerSize = sstruct.calcsize(META_HEADER_FORMAT)
        dataOffset = headerSize + len(keys) * sstruct.calcsize(DATA_MAP_FORMAT)
        header = sstruct.pack(META_HEADER_FORMAT, {
                "version": 1,
                "flags": 0,
                "dataOffset": dataOffset,
                "numDataMaps": len(keys)
        })
        dataMaps = []
        dataBlocks = []
        for tag in keys:
            data = self.data[tag]
            dataMaps.append(sstruct.pack(DATA_MAP_FORMAT, {
                "tag": tag,
                "dataOffset": dataOffset,
                "dataLength": len(data)
            }))
            dataBlocks.append(data)
            dataOffset += len(data)
        return bytesjoin([header] + dataMaps + dataBlocks)

    def toXML(self, writer, ttFont, progress=None):
        for tag in sorted(self.data.keys()):
            writer.begintag("hexdata", tag=tag)
            writer.newline()
            writer.dumphex(self.data[tag])
            writer.endtag("hexdata")
            writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "hexdata":
            self.data[attrs["tag"]] = readHex(content)
        else:
            raise TTLibError("can't handle '%s' element" % name)
