from textwrap import dedent
from fontTools.misc import sstruct
from fontTools.misc.textTools import bytesjoin, strjoin, readHex
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


DATA_MAP_FORMAT = """
    > # big endian
    tag:         4s
    dataOffset:  L
    dataLength:  L
"""


REGISTERED_TAGS = ["dlng", "slng"]

KNOWN_TEXT_TAGS = REGISTERED_TAGS + [
    # private tag used to store dependencies information by e.g. gftools
    "DEPS",
]


class table__m_e_t_a(DefaultTable.DefaultTable):
    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.data = {}

    def decompile(self, data, ttFont):
        headerSize = sstruct.calcsize(META_HEADER_FORMAT)
        header = sstruct.unpack(META_HEADER_FORMAT, data[0:headerSize])
        if header["version"] != 1:
            raise TTLibError("unsupported 'meta' version %d" % header["version"])
        dataMapSize = sstruct.calcsize(DATA_MAP_FORMAT)
        for i in range(header["numDataMaps"]):
            dataMapOffset = headerSize + i * dataMapSize
            dataMap = sstruct.unpack(
                DATA_MAP_FORMAT, data[dataMapOffset : dataMapOffset + dataMapSize]
            )
            tag = dataMap["tag"]
            offset = dataMap["dataOffset"]
            self.data[tag] = data[offset : offset + dataMap["dataLength"]]
            if tag in KNOWN_TEXT_TAGS:
                self.data[tag] = self.data[tag].decode("utf-8")

    def compile(self, ttFont):
        keys = sorted(self.data.keys())
        headerSize = sstruct.calcsize(META_HEADER_FORMAT)
        dataOffset = headerSize + len(keys) * sstruct.calcsize(DATA_MAP_FORMAT)
        header = sstruct.pack(
            META_HEADER_FORMAT,
            {
                "version": 1,
                "flags": 0,
                "dataOffset": dataOffset,
                "numDataMaps": len(keys),
            },
        )
        dataMaps = []
        dataBlocks = []
        for tag in keys:
            if tag in KNOWN_TEXT_TAGS:
                data = self.data[tag].encode("utf-8")
            else:
                data = self.data[tag]
            dataMaps.append(
                sstruct.pack(
                    DATA_MAP_FORMAT,
                    {"tag": tag, "dataOffset": dataOffset, "dataLength": len(data)},
                )
            )
            dataBlocks.append(data)
            dataOffset += len(data)
        return bytesjoin([header] + dataMaps + dataBlocks)

    def toXML(self, writer, ttFont):
        for tag in sorted(self.data.keys()):
            if tag in KNOWN_TEXT_TAGS:
                writer.begintag("text", tag=tag)
                writer.newline()
                writer.write_multiline_indented(self.data[tag])
                writer.newline()
                writer.endtag("text")
                writer.newline()
            else:
                writer.begintag("hexdata", tag=tag)
                writer.newline()
                data = self.data[tag]
                if min(data) >= 0x20 and max(data) <= 0x7E:
                    writer.comment("ascii: " + data.decode("ascii"))
                    writer.newline()
                writer.dumphex(data)
                writer.endtag("hexdata")
                writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == "hexdata":
            self.data[attrs["tag"]] = readHex(content)
        elif name == "text" and attrs["tag"] in KNOWN_TEXT_TAGS:
            print(content)
            self.data[attrs["tag"]] = dedent(strjoin(content)).strip()
        else:
            raise TTLibError("can't handle '%s' element" % name)


def main():
    """Print the content of the given 'meta' table tag to stdout"""
    import argparse
    from fontTools.ttLib import TTFont

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("font", help="font file")
    parser.add_argument("tag", help="metadata tag to print")

    args = parser.parse_args()

    font = TTFont(args.font)
    meta = font.get("meta")
    if meta is None:
        parser.error("no 'meta' table found")

    try:
        print(meta.data[args.tag])
    except KeyError:
        parser.error("tag '%s' not found" % args.tag)


if __name__ == "__main__":
    main()
