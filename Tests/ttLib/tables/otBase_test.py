from fontTools.misc.textTools import deHexStr
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
import unittest


class OTTableReaderTest(unittest.TestCase):
    def test_readShort(self):
        reader = OTTableReader(deHexStr("CA FE"))
        self.assertEqual(reader.readShort(), -13570)
        self.assertEqual(reader.pos, 2)

    def test_readLong(self):
        reader = OTTableReader(deHexStr("CA FE BE EF"))
        self.assertEqual(reader.readLong(), -889274641)
        self.assertEqual(reader.pos, 4)

    def test_readUInt8(self):
        reader = OTTableReader(deHexStr("C3"))
        self.assertEqual(reader.readUInt8(), 0xC3)
        self.assertEqual(reader.pos, 1)

    def test_readUShort(self):
        reader = OTTableReader(deHexStr("CA FE"))
        self.assertEqual(reader.readUShort(), 0xCAFE)
        self.assertEqual(reader.pos, 2)

    def test_readUShortArray(self):
        reader = OTTableReader(deHexStr("DE AD BE EF CA FE"))
        self.assertEqual(list(reader.readUShortArray(3)), [0xDEAD, 0xBEEF, 0xCAFE])
        self.assertEqual(reader.pos, 6)

    def test_readUInt24(self):
        reader = OTTableReader(deHexStr("C3 13 37"))
        self.assertEqual(reader.readUInt24(), 0xC31337)
        self.assertEqual(reader.pos, 3)

    def test_readULong(self):
        reader = OTTableReader(deHexStr("CA FE BE EF"))
        self.assertEqual(reader.readULong(), 0xCAFEBEEF)
        self.assertEqual(reader.pos, 4)

    def test_readTag(self):
        reader = OTTableReader(deHexStr("46 6F 6F 64"))
        self.assertEqual(reader.readTag(), "Food")
        self.assertEqual(reader.pos, 4)

    def test_readData(self):
        reader = OTTableReader(deHexStr("48 65 6C 6C 6F"))
        self.assertEqual(reader.readData(5), b"Hello")
        self.assertEqual(reader.pos, 5)

    def test_getSubReader(self):
        reader = OTTableReader(deHexStr("CAFE F00D"))
        sub = reader.getSubReader(2)
        self.assertEqual(sub.readUShort(), 0xF00D)
        self.assertEqual(reader.readUShort(), 0xCAFE)


class OTTableWriterTest(unittest.TestCase):
    def test_writeShort(self):
        writer = OTTableWriter()
        writer.writeShort(-12345)
        self.assertEqual(writer.getData(), deHexStr("CF C7"))

    def test_writeLong(self):
        writer = OTTableWriter()
        writer.writeLong(-12345678)
        self.assertEqual(writer.getData(), deHexStr("FF 43 9E B2"))

    def test_writeUInt8(self):
        writer = OTTableWriter()
        writer.writeUInt8(0xBE)
        self.assertEqual(writer.getData(), deHexStr("BE"))

    def test_writeUShort(self):
        writer = OTTableWriter()
        writer.writeUShort(0xBEEF)
        self.assertEqual(writer.getData(), deHexStr("BE EF"))

    def test_writeUInt24(self):
        writer = OTTableWriter()
        writer.writeUInt24(0xBEEF77)
        self.assertEqual(writer.getData(), deHexStr("BE EF 77"))

    def test_writeULong(self):
        writer = OTTableWriter()
        writer.writeULong(0xBEEFCAFE)
        self.assertEqual(writer.getData(), deHexStr("BE EF CA FE"))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
