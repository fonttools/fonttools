from fontTools.ttLib import TTFont, newTable, getTableModule
from fontTools.ttLib.tables.O_S_2f_2 import *
import unittest


class OS2TableTest(unittest.TestCase):
    @staticmethod
    def makeOS2_cmap(mapping):
        font = TTFont()
        font["OS/2"] = os2 = newTable("OS/2")
        os2.version = 4
        font["cmap"] = cmap = newTable("cmap")
        st = getTableModule("cmap").CmapSubtable.newSubtable(4)
        st.platformID, st.platEncID, st.language = 3, 1, 0
        st.cmap = mapping
        cmap.tables = []
        cmap.tables.append(st)
        return font, os2, cmap

    def test_getUnicodeRanges(self):
        table = table_O_S_2f_2()
        table.ulUnicodeRange1 = 0xFFFFFFFF
        table.ulUnicodeRange2 = 0xFFFFFFFF
        table.ulUnicodeRange3 = 0xFFFFFFFF
        table.ulUnicodeRange4 = 0xFFFFFFFF
        bits = table.getUnicodeRanges()
        for i in range(127):
            self.assertIn(i, bits)

    def test_setUnicodeRanges(self):
        table = table_O_S_2f_2()
        table.ulUnicodeRange1 = 0
        table.ulUnicodeRange2 = 0
        table.ulUnicodeRange3 = 0
        table.ulUnicodeRange4 = 0
        bits = set(range(123))
        table.setUnicodeRanges(bits)
        self.assertEqual(table.getUnicodeRanges(), bits)
        with self.assertRaises(ValueError):
            table.setUnicodeRanges([-1, 127, 255])

    def test_recalcUnicodeRanges(self):
        font, os2, cmap = self.makeOS2_cmap(
            {0x0041: "A", 0x03B1: "alpha", 0x0410: "Acyr"}
        )
        os2.setUnicodeRanges({0, 1, 9})
        # 'pruneOnly' will clear any bits for which there's no intersection:
        # bit 1 ('Latin 1 Supplement'), in this case. However, it won't set
        # bit 7 ('Greek and Coptic') despite the "alpha" character is present.
        self.assertEqual(os2.recalcUnicodeRanges(font, pruneOnly=True), {0, 9})
        # try again with pruneOnly=False: bit 7 is now set.
        self.assertEqual(os2.recalcUnicodeRanges(font), {0, 7, 9})
        # add a non-BMP char from 'Mahjong Tiles' block (bit 122)
        cmap.tables[0].cmap[0x1F000] = "eastwindtile"
        # the bit 122 and the special bit 57 ('Non Plane 0') are also enabled
        self.assertEqual(os2.recalcUnicodeRanges(font), {0, 7, 9, 57, 122})

    def test_intersectUnicodeRanges(self):
        self.assertEqual(intersectUnicodeRanges([0x0410]), {9})
        self.assertEqual(intersectUnicodeRanges([0x0410, 0x1F000]), {9, 57, 122})
        self.assertEqual(
            intersectUnicodeRanges([0x0410, 0x1F000], inverse=True),
            (set(range(123)) - {9, 57, 122}),
        )

    def test_getCodePageRanges(self):
        table = table_O_S_2f_2()
        # version 0 doesn't define these fields so by definition defines no cp ranges
        table.version = 0
        self.assertEqual(table.getCodePageRanges(), set())
        # version 1 and above do contain ulCodePageRange1 and 2 fields
        table.version = 1
        table.ulCodePageRange1 = 0xFFFFFFFF
        table.ulCodePageRange2 = 0xFFFFFFFF
        bits = table.getCodePageRanges()
        for i in range(63):
            self.assertIn(i, bits)

    def test_setCodePageRanges(self):
        table = table_O_S_2f_2()
        table.version = 4
        table.ulCodePageRange1 = 0
        table.ulCodePageRange2 = 0
        bits = set(range(64))
        table.setCodePageRanges(bits)
        self.assertEqual(table.getCodePageRanges(), bits)
        with self.assertRaises(ValueError):
            table.setCodePageRanges([-1])
        with self.assertRaises(ValueError):
            table.setCodePageRanges([64])
        with self.assertRaises(ValueError):
            table.setCodePageRanges([255])

    def test_setCodePageRanges_bump_version(self):
        # Setting codepage ranges on a OS/2 table version 0 automatically makes it
        # a version 1 table
        table = table_O_S_2f_2()
        table.version = 0
        self.assertEqual(table.getCodePageRanges(), set())
        table.setCodePageRanges({0, 1, 2})
        self.assertEqual(table.getCodePageRanges(), {0, 1, 2})
        self.assertEqual(table.version, 1)

    def test_recalcCodePageRanges(self):
        font, os2, cmap = self.makeOS2_cmap(
            {ord("A"): "A", ord("Ά"): "Alphatonos", ord("Б"): "Be"}
        )
        os2.setCodePageRanges({0, 2, 9})

        # With pruneOnly=True, should clear any CodePage for which there are no
        # characters in the cmap.
        self.assertEqual(os2.recalcCodePageRanges(font, pruneOnly=True), {2})

        # With pruneOnly=False, should also set CodePages not initially set.
        self.assertEqual(os2.recalcCodePageRanges(font), {2, 3})

        # Add a Korean character, should set CodePage 21 (Korean Johab)
        cmap.tables[0].cmap[ord("곴")] = "goss"
        self.assertEqual(os2.recalcCodePageRanges(font), {2, 3, 21})

        # Remove all characters from cmap, should still set CodePage 0 (Latin 1)
        cmap.tables[0].cmap = {}
        self.assertEqual(os2.recalcCodePageRanges(font), {0})


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
