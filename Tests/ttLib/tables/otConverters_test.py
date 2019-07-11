# coding: utf-8
from __future__ import print_function, division, absolute_import, \
    unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.misc.testTools import FakeFont, makeXMLWriter
from fontTools.misc.textTools import deHexStr
import fontTools.ttLib.tables.otConverters as otConverters
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
import unittest


class Char64Test(unittest.TestCase):
    font = FakeFont([])
    converter = otConverters.Char64("char64", 0, None, None)

    def test_read(self):
        reader = OTTableReader(b"Hello\0junk after zero byte" + 100 * b"\0")
        self.assertEqual(self.converter.read(reader, self.font, {}), "Hello")
        self.assertEqual(reader.pos, 64)

    def test_read_replace_not_ascii(self):
        reader = OTTableReader(b"Hello \xE4 world" + 100 * b"\0")
        with CapturingLogHandler(otConverters.log, "WARNING") as captor:
            data = self.converter.read(reader, self.font, {})
        self.assertEqual(data, "Hello � world")
        self.assertEqual(reader.pos, 64)
        self.assertIn('replaced non-ASCII characters in "Hello � world"',
                      [r.msg for r in captor.records])

    def test_write(self):
        writer = OTTableWriter()
        self.converter.write(writer, self.font, {}, "Hello world")
        self.assertEqual(writer.getData(), b"Hello world" + 53 * b"\0")

    def test_write_replace_not_ascii(self):
        writer = OTTableWriter()
        with CapturingLogHandler(otConverters.log, "WARNING") as captor:
            self.converter.write(writer, self.font, {}, "Hello ☃")
        self.assertEqual(writer.getData(), b"Hello ?" + 57 * b"\0")
        self.assertIn('replacing non-ASCII characters in "Hello ☃"',
                      [r.msg for r in captor.records])

    def test_write_truncated(self):
        writer = OTTableWriter()
        with CapturingLogHandler(otConverters.log, "WARNING") as captor:
            self.converter.write(writer, self.font, {}, "A" * 80)
        self.assertEqual(writer.getData(), b"A" * 64)
        self.assertIn('truncating overlong "' + "A" * 80 + '" to 64 bytes',
                      [r.msg for r in captor.records])

    def test_xmlRead(self):
        value = self.converter.xmlRead({"value": "Foo"}, [], self.font)
        self.assertEqual(value, "Foo")

    def test_xmlWrite(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.font, "Hello world", "Element",
                                [("attr", "v")])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(xml, '<Element attr="v" value="Hello world"/>')


class GlyphIDTest(unittest.TestCase):
    font = FakeFont(".notdef A B C".split())
    converter = otConverters.GlyphID('GlyphID', 0, None, None)

    def test_readArray(self):
        reader = OTTableReader(deHexStr("0002 0001 DEAD 0002"))
        self.assertEqual(self.converter.readArray(reader, self.font, {}, 4),
                         ["B", "A", "glyph57005", "B"])
        self.assertEqual(reader.pos, 8)

    def test_read(self):
        reader = OTTableReader(deHexStr("0003"))
        self.assertEqual(self.converter.read(reader, self.font, {}), "C")
        self.assertEqual(reader.pos, 2)

    def test_write(self):
        writer = OTTableWriter()
        self.converter.write(writer, self.font, {}, "B")
        self.assertEqual(writer.getData(), deHexStr("0002"))


class LongTest(unittest.TestCase):
    font = FakeFont([])
    converter = otConverters.Long('Long', 0, None, None)

    def test_read(self):
        reader = OTTableReader(deHexStr("FF0000EE"))
        self.assertEqual(self.converter.read(reader, self.font, {}), -16776978)
        self.assertEqual(reader.pos, 4)

    def test_write(self):
        writer = OTTableWriter()
        self.converter.write(writer, self.font, {}, -16777213)
        self.assertEqual(writer.getData(), deHexStr("FF000003"))

    def test_xmlRead(self):
        value = self.converter.xmlRead({"value": "314159"}, [], self.font)
        self.assertEqual(value, 314159)

    def test_xmlWrite(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.font, 291, "Foo", [("attr", "v")])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(xml, '<Foo attr="v" value="291"/>')


class NameIDTest(unittest.TestCase):
    converter = otConverters.NameID('NameID', 0, None, None)

    def makeFont(self):
        nameTable = newTable('name')
        nameTable.setName(u"Demibold Condensed", 0x123, 3, 0, 0x409)
        nameTable.setName(u"Copyright 2018", 0, 3, 0, 0x409)
        return {"name": nameTable}

    def test_read(self):
        font = self.makeFont()
        reader = OTTableReader(deHexStr("0123"))
        self.assertEqual(self.converter.read(reader, font, {}), 0x123)

    def test_write(self):
        writer = OTTableWriter()
        self.converter.write(writer, self.makeFont(), {}, 0x123)
        self.assertEqual(writer.getData(), deHexStr("0123"))

    def test_xmlWrite(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.makeFont(), 291,
                                "FooNameID", [("attr", "val")])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(
            xml,
            '<FooNameID attr="val" value="291"/>  <!-- Demibold Condensed -->')

    def test_xmlWrite_missingID(self):
        writer = makeXMLWriter()
        with CapturingLogHandler(otConverters.log, "WARNING") as captor:
            self.converter.xmlWrite(writer, self.makeFont(), 666,
                                    "Entity", [("attrib", "val")])
        self.assertIn("name id 666 missing from name table",
                      [r.msg for r in captor.records])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(
            xml,
            '<Entity attrib="val"'
            ' value="666"/>  <!-- missing from name table -->')

    def test_xmlWrite_NULL(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.makeFont(), 0,
                                "FooNameID", [("attr", "val")])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(
            xml, '<FooNameID attr="val" value="0"/>')


class UInt8Test(unittest.TestCase):
    font = FakeFont([])
    converter = otConverters.UInt8("UInt8", 0, None, None)

    def test_read(self):
        reader = OTTableReader(deHexStr("FE"))
        self.assertEqual(self.converter.read(reader, self.font, {}), 254)
        self.assertEqual(reader.pos, 1)

    def test_write(self):
        writer = OTTableWriter()
        self.converter.write(writer, self.font, {}, 253)
        self.assertEqual(writer.getData(), deHexStr("FD"))

    def test_xmlRead(self):
        value = self.converter.xmlRead({"value": "254"}, [], self.font)
        self.assertEqual(value, 254)

    def test_xmlWrite(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.font, 251, "Foo", [("attr", "v")])
        xml = writer.file.getvalue().decode("utf-8").rstrip()
        self.assertEqual(xml, '<Foo attr="v" value="251"/>')


class AATLookupTest(unittest.TestCase):
    font = FakeFont(".notdef A B C D E F G H A.alt B.alt".split())
    converter = otConverters.AATLookup("AATLookup", 0, None,
                                       tableClass=otConverters.GlyphID)

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_readFormat0(self):
        reader = OTTableReader(deHexStr("0000 0000 0001 0002 0000 7D00 0001"))
        self.assertEqual(self.converter.read(reader, self.font, None), {
            ".notdef": ".notdef",
            "A": "A",
            "B": "B",
            "C": ".notdef",
            "D": "glyph32000",
            "E": "A"
        })

    def test_readFormat2(self):
        reader = OTTableReader(deHexStr(
            "0002 0006 0002 000C 0001 0006 "
            "0002 0001 0003 "   # glyph A..B: map to C
            "0007 0005 0008 "   # glyph E..G: map to H
            "FFFF FFFF FFFF"))  # end of search table
        self.assertEqual(self.converter.read(reader, self.font, None), {
            "A": "C",
            "B": "C",
            "E": "H",
            "F": "H",
            "G": "H",
        })

    def test_readFormat4(self):
        reader = OTTableReader(deHexStr(
            "0004 0006 0003 000C 0001 0006 "
            "0002 0001 001E "  # glyph 1..2: mapping at offset 0x1E
            "0005 0004 001E "  # glyph 4..5: mapping at offset 0x1E
            "FFFF FFFF FFFF "  # end of search table
            "0007 0008"))      # offset 0x18: glyphs [7, 8] = [G, H]
        self.assertEqual(self.converter.read(reader, self.font, None), {
            "A": "G",
            "B": "H",
            "D": "G",
            "E": "H",
        })

    def test_readFormat6(self):
        reader = OTTableReader(deHexStr(
            "0006 0004 0002 0008 0001 0004 "
            "0003 0001 "   # C --> A
            "0005 0002 "   # E --> B
            "FFFF FFFF"))  # end of search table
        self.assertEqual(self.converter.read(reader, self.font, None), {
            "C": "A",
            "E": "B",
        })

    def test_readFormat8(self):
        reader = OTTableReader(deHexStr(
            "0008 "
            "0003 0003 "        # first: C, count: 3
            "0007 0001 0002"))  # [G, A, B]
        self.assertEqual(self.converter.read(reader, self.font, None), {
            "C": "G",
            "D": "A",
            "E": "B",
        })

    def test_readUnknownFormat(self):
        reader = OTTableReader(deHexStr("0009"))
        self.assertRaisesRegex(
            AssertionError,
            "unsupported lookup format: 9",
            self.converter.read, reader, self.font, None)

    def test_writeFormat0(self):
        writer = OTTableWriter()
        font = FakeFont(".notdef A B C".split())
        self.converter.write(writer, font, {}, {
            ".notdef": ".notdef",
            "A": "C",
            "B": "C",
            "C": "A"
        })
        self.assertEqual(writer.getData(), deHexStr("0000 0000 0003 0003 0001"))

    def test_writeFormat2(self):
        writer = OTTableWriter()
        font = FakeFont(".notdef A B C D E F G H".split())
        self.converter.write(writer, font, {}, {
            "B": "C",
            "C": "C",
            "D": "C",
            "E": "C",
            "G": "A",
            "H": "A",
        })
        self.assertEqual(writer.getData(), deHexStr(
            "0002 "            # format=2
            "0006 "            # binSrchHeader.unitSize=6
            "0002 "            # binSrchHeader.nUnits=2
            "000C "            # binSrchHeader.searchRange=12
            "0001 "            # binSrchHeader.entrySelector=1
            "0000 "            # binSrchHeader.rangeShift=0
            "0005 0002 0003 "  # segments[0].lastGlyph=E, firstGlyph=B, value=C
            "0008 0007 0001 "  # segments[1].lastGlyph=H, firstGlyph=G, value=A
            "FFFF FFFF 0000 "  # segments[2]=<END>
        ))

    def test_writeFormat6(self):
        writer = OTTableWriter()
        font = FakeFont(".notdef A B C D E".split())
        self.converter.write(writer, font, {}, {
            "A": "C",
            "C": "B",
            "D": "D",
            "E": "E",
        })
        self.assertEqual(writer.getData(), deHexStr(
            "0006 "         # format=6
            "0004 "         # binSrchHeader.unitSize=4
            "0004 "         # binSrchHeader.nUnits=4
            "0010 "         # binSrchHeader.searchRange=16
            "0002 "         # binSrchHeader.entrySelector=2
            "0000 "         # binSrchHeader.rangeShift=0
            "0001 0003 "    # entries[0].glyph=A, .value=C
            "0003 0002 "    # entries[1].glyph=C, .value=B
            "0004 0004 "    # entries[2].glyph=D, .value=D
            "0005 0005 "    # entries[3].glyph=E, .value=E
            "FFFF 0000 "    # entries[4]=<END>
        ))

    def test_writeFormat8(self):
        writer = OTTableWriter()
        font = FakeFont(".notdef A B C D E F G H".split())
        self.converter.write(writer, font, {}, {
            "B": "B",
            "C": "A",
            "D": "B",
            "E": "C",
            "F": "B",
            "G": "A",
        })
        self.assertEqual(writer.getData(), deHexStr(
            "0008 "                          # format=8
            "0002 "                          # firstGlyph=B
            "0006 "                          # glyphCount=6
            "0002 0001 0002 0003 0002 0001"  # valueArray=[B, A, B, C, B, A]
        ))

    def test_xmlRead(self):
        value = self.converter.xmlRead({}, [
            ("Lookup", {"glyph": "A", "value": "A.alt"}, []),
            ("Lookup", {"glyph": "B", "value": "B.alt"}, []),
        ], self.font)
        self.assertEqual(value, {"A": "A.alt", "B": "B.alt"})

    def test_xmlWrite(self):
        writer = makeXMLWriter()
        self.converter.xmlWrite(writer, self.font,
                                value={"A": "A.alt", "B": "B.alt"},
                                name="Foo", attrs=[("attr", "val")])
        xml = writer.file.getvalue().decode("utf-8").splitlines()
        self.assertEqual(xml, [
            '<Foo attr="val">',
            '  <Lookup glyph="A" value="A.alt"/>',
            '  <Lookup glyph="B" value="B.alt"/>',
            '</Foo>',
        ])


class LazyListTest(unittest.TestCase):

    def test_slice(self):
        ll = otConverters._LazyList([10, 11, 12, 13])
        sl = ll[:]

        self.assertIsNot(sl, ll)
        self.assertIsInstance(sl, list)
        self.assertEqual([10, 11, 12, 13], sl)

        self.assertEqual([11, 12], ll[1:3])

    def test_getitem(self):
        count = 2
        reader = OTTableReader(b"\x00\xFE\xFF\x00\x00\x00", offset=1)
        converter = otConverters.UInt8("UInt8", 0, None, None)
        recordSize = converter.staticSize
        l = otConverters._LazyList()
        l.reader = reader
        l.pos = l.reader.pos
        l.font = None
        l.conv = converter
        l.recordSize = recordSize
        l.extend(otConverters._MissingItem([i]) for i in range(count))
        reader.advance(count * recordSize)

        self.assertEqual(l[0], 254)
        self.assertEqual(l[1], 255)

    def test_add_both_LazyList(self):
        ll1 = otConverters._LazyList([1])
        ll2 = otConverters._LazyList([2])

        l3 = ll1 + ll2

        self.assertIsInstance(l3, list)
        self.assertEqual([1, 2], l3)

    def test_add_LazyList_and_list(self):
        ll1 = otConverters._LazyList([1])
        l2 = [2]

        l3 = ll1 + l2

        self.assertIsInstance(l3, list)
        self.assertEqual([1, 2], l3)

    def test_add_not_implemented(self):
        with self.assertRaises(TypeError):
            otConverters._LazyList() + 0
        with self.assertRaises(TypeError):
            otConverters._LazyList() + tuple()

    def test_radd_list_and_LazyList(self):
        l1 = [1]
        ll2 = otConverters._LazyList([2])

        l3 = l1 + ll2

        self.assertIsInstance(l3, list)
        self.assertEqual([1, 2], l3)

    def test_radd_not_implemented(self):
        with self.assertRaises(TypeError):
            0 + otConverters._LazyList()
        with self.assertRaises(TypeError):
            tuple() + otConverters._LazyList()


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
