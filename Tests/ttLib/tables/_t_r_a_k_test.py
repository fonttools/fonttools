from fontTools.misc.testTools import parseXML, getXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib.tables._t_r_a_k import *
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e, NameRecord
import unittest


# /Library/Fonts/Osaka.ttf from OSX has trak table with both horiz and vertData
OSAKA_TRAK_TABLE_DATA = deHexStr(
    "00 01 00 00 00 00 00 0c 00 40 00 00 00 03 00 02 00 00 00 2c ff ff "
    "00 00 01 06 00 34 00 00 00 00 01 07 00 38 00 01 00 00 01 08 00 3c "
    "00 0c 00 00 00 18 00 00 ff f4 ff f4 00 00 00 00 00 0c 00 0c 00 03 "
    "00 02 00 00 00 60 ff ff 00 00 01 09 00 68 00 00 00 00 01 0a 00 6c "
    "00 01 00 00 01 0b 00 70 00 0c 00 00 00 18 00 00 ff f4 ff f4 00 00 "
    "00 00 00 0c 00 0c"
)

# decompiled horizData and vertData entries from Osaka.ttf
OSAKA_HORIZ_TRACK_ENTRIES = {
    -1.0: TrackTableEntry({24.0: -12, 12.0: -12}, nameIndex=262),
    0.0: TrackTableEntry({24.0: 0, 12.0: 0}, nameIndex=263),
    1.0: TrackTableEntry({24.0: 12, 12.0: 12}, nameIndex=264),
}

OSAKA_VERT_TRACK_ENTRIES = {
    -1.0: TrackTableEntry({24.0: -12, 12.0: -12}, nameIndex=265),
    0.0: TrackTableEntry({24.0: 0, 12.0: 0}, nameIndex=266),
    1.0: TrackTableEntry({24.0: 12, 12.0: 12}, nameIndex=267),
}

OSAKA_TRAK_TABLE_XML = [
    '<version value="1.0"/>',
    '<format value="0"/>',
    "<horizData>",
    "  <!-- nTracks=3, nSizes=2 -->",
    '  <trackEntry value="-1.0" nameIndex="262">',
    "    <!-- Tight -->",
    '    <track size="12.0" value="-12"/>',
    '    <track size="24.0" value="-12"/>',
    "  </trackEntry>",
    '  <trackEntry value="0.0" nameIndex="263">',
    "    <!-- Normal -->",
    '    <track size="12.0" value="0"/>',
    '    <track size="24.0" value="0"/>',
    "  </trackEntry>",
    '  <trackEntry value="1.0" nameIndex="264">',
    "    <!-- Loose -->",
    '    <track size="12.0" value="12"/>',
    '    <track size="24.0" value="12"/>',
    "  </trackEntry>",
    "</horizData>",
    "<vertData>",
    "  <!-- nTracks=3, nSizes=2 -->",
    '  <trackEntry value="-1.0" nameIndex="265">',
    "    <!-- Tight -->",
    '    <track size="12.0" value="-12"/>',
    '    <track size="24.0" value="-12"/>',
    "  </trackEntry>",
    '  <trackEntry value="0.0" nameIndex="266">',
    "    <!-- Normal -->",
    '    <track size="12.0" value="0"/>',
    '    <track size="24.0" value="0"/>',
    "  </trackEntry>",
    '  <trackEntry value="1.0" nameIndex="267">',
    "    <!-- Loose -->",
    '    <track size="12.0" value="12"/>',
    '    <track size="24.0" value="12"/>',
    "  </trackEntry>",
    "</vertData>",
]

# made-up table containing only vertData (no horizData)
OSAKA_VERT_ONLY_TRAK_TABLE_DATA = deHexStr(
    "00 01 00 00 00 00 00 00 00 0c 00 00 00 03 00 02 00 00 00 2c ff ff "
    "00 00 01 09 00 34 00 00 00 00 01 0a 00 38 00 01 00 00 01 0b 00 3c "
    "00 0c 00 00 00 18 00 00 ff f4 ff f4 00 00 00 00 00 0c 00 0c"
)

OSAKA_VERT_ONLY_TRAK_TABLE_XML = [
    '<version value="1.0"/>',
    '<format value="0"/>',
    "<horizData>",
    "  <!-- nTracks=0, nSizes=0 -->",
    "</horizData>",
    "<vertData>",
    "  <!-- nTracks=3, nSizes=2 -->",
    '  <trackEntry value="-1.0" nameIndex="265">',
    "    <!-- Tight -->",
    '    <track size="12.0" value="-12"/>',
    '    <track size="24.0" value="-12"/>',
    "  </trackEntry>",
    '  <trackEntry value="0.0" nameIndex="266">',
    "    <!-- Normal -->",
    '    <track size="12.0" value="0"/>',
    '    <track size="24.0" value="0"/>',
    "  </trackEntry>",
    '  <trackEntry value="1.0" nameIndex="267">',
    "    <!-- Loose -->",
    '    <track size="12.0" value="12"/>',
    '    <track size="24.0" value="12"/>',
    "  </trackEntry>",
    "</vertData>",
]


# also /Library/Fonts/Skia.ttf contains a trak table with horizData
SKIA_TRAK_TABLE_DATA = deHexStr(
    "00 01 00 00 00 00 00 0c 00 00 00 00 00 03 00 05 00 00 00 2c ff ff "
    "00 00 01 13 00 40 00 00 00 00 01 2f 00 4a 00 01 00 00 01 14 00 54 "
    "00 09 00 00 00 0a 00 00 00 0c 00 00 00 12 00 00 00 13 00 00 ff f6 "
    "ff e2 ff c4 ff c1 ff c1 00 0f 00 00 ff fb ff e7 ff e7 00 8c 00 82 "
    "00 7d 00 73 00 73"
)

SKIA_TRACK_ENTRIES = {
    -1.0: TrackTableEntry(
        {9.0: -10, 10.0: -30, 19.0: -63, 12.0: -60, 18.0: -63}, nameIndex=275
    ),
    0.0: TrackTableEntry(
        {9.0: 15, 10.0: 0, 19.0: -25, 12.0: -5, 18.0: -25}, nameIndex=303
    ),
    1.0: TrackTableEntry(
        {9.0: 140, 10.0: 130, 19.0: 115, 12.0: 125, 18.0: 115}, nameIndex=276
    ),
}

SKIA_TRAK_TABLE_XML = [
    '<version value="1.0"/>',
    '<format value="0"/>',
    "<horizData>",
    "  <!-- nTracks=3, nSizes=5 -->",
    '  <trackEntry value="-1.0" nameIndex="275">',
    "    <!-- Tight -->",
    '    <track size="9.0" value="-10"/>',
    '    <track size="10.0" value="-30"/>',
    '    <track size="12.0" value="-60"/>',
    '    <track size="18.0" value="-63"/>',
    '    <track size="19.0" value="-63"/>',
    "  </trackEntry>",
    '  <trackEntry value="0.0" nameIndex="303">',
    "    <!-- Normal -->",
    '    <track size="9.0" value="15"/>',
    '    <track size="10.0" value="0"/>',
    '    <track size="12.0" value="-5"/>',
    '    <track size="18.0" value="-25"/>',
    '    <track size="19.0" value="-25"/>',
    "  </trackEntry>",
    '  <trackEntry value="1.0" nameIndex="276">',
    "    <!-- Loose -->",
    '    <track size="9.0" value="140"/>',
    '    <track size="10.0" value="130"/>',
    '    <track size="12.0" value="125"/>',
    '    <track size="18.0" value="115"/>',
    '    <track size="19.0" value="115"/>',
    "  </trackEntry>",
    "</horizData>",
    "<vertData>",
    "  <!-- nTracks=0, nSizes=0 -->",
    "</vertData>",
]


class TrackingTableTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        table = table__t_r_a_k()
        table.version = 1.0
        table.format = 0
        self.font = {"trak": table}

    def test_compile_horiz(self):
        table = self.font["trak"]
        table.horizData = TrackData(SKIA_TRACK_ENTRIES)
        trakData = table.compile(self.font)
        self.assertEqual(trakData, SKIA_TRAK_TABLE_DATA)

    def test_compile_vert(self):
        table = self.font["trak"]
        table.vertData = TrackData(OSAKA_VERT_TRACK_ENTRIES)
        trakData = table.compile(self.font)
        self.assertEqual(trakData, OSAKA_VERT_ONLY_TRAK_TABLE_DATA)

    def test_compile_horiz_and_vert(self):
        table = self.font["trak"]
        table.horizData = TrackData(OSAKA_HORIZ_TRACK_ENTRIES)
        table.vertData = TrackData(OSAKA_VERT_TRACK_ENTRIES)
        trakData = table.compile(self.font)
        self.assertEqual(trakData, OSAKA_TRAK_TABLE_DATA)

    def test_compile_longword_aligned(self):
        table = self.font["trak"]
        # without padding, this 'horizData' would end up 46 byte long
        table.horizData = TrackData(
            {0.0: TrackTableEntry(nameIndex=256, values={12.0: 0, 24.0: 0, 36.0: 0})}
        )
        table.vertData = TrackData(
            {0.0: TrackTableEntry(nameIndex=257, values={12.0: 0, 24.0: 0, 36.0: 0})}
        )
        trakData = table.compile(self.font)
        self.assertTrue(table.vertOffset % 4 == 0)

    def test_compile_sizes_mismatch(self):
        table = self.font["trak"]
        table.horizData = TrackData(
            {
                -1.0: TrackTableEntry(nameIndex=256, values={9.0: -10, 10.0: -30}),
                0.0: TrackTableEntry(nameIndex=257, values={8.0: 20, 12.0: 0}),
            }
        )
        with self.assertRaisesRegex(TTLibError, "entries must specify the same sizes"):
            table.compile(self.font)

    def test_decompile_horiz(self):
        table = self.font["trak"]
        table.decompile(SKIA_TRAK_TABLE_DATA, self.font)
        self.assertEqual(table.horizData, SKIA_TRACK_ENTRIES)
        self.assertEqual(table.vertData, TrackData())

    def test_decompile_vert(self):
        table = self.font["trak"]
        table.decompile(OSAKA_VERT_ONLY_TRAK_TABLE_DATA, self.font)
        self.assertEqual(table.horizData, TrackData())
        self.assertEqual(table.vertData, OSAKA_VERT_TRACK_ENTRIES)

    def test_decompile_horiz_and_vert(self):
        table = self.font["trak"]
        table.decompile(OSAKA_TRAK_TABLE_DATA, self.font)
        self.assertEqual(table.horizData, OSAKA_HORIZ_TRACK_ENTRIES)
        self.assertEqual(table.vertData, OSAKA_VERT_TRACK_ENTRIES)

    def test_roundtrip_decompile_compile(self):
        for trakData in (
            OSAKA_TRAK_TABLE_DATA,
            OSAKA_VERT_ONLY_TRAK_TABLE_DATA,
            SKIA_TRAK_TABLE_DATA,
        ):
            table = table__t_r_a_k()
            table.decompile(trakData, ttFont=None)
            newTrakData = table.compile(ttFont=None)
            self.assertEqual(trakData, newTrakData)

    def test_fromXML_horiz(self):
        table = self.font["trak"]
        for name, attrs, content in parseXML(SKIA_TRAK_TABLE_XML):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.version, 1.0)
        self.assertEqual(table.format, 0)
        self.assertEqual(table.horizData, SKIA_TRACK_ENTRIES)
        self.assertEqual(table.vertData, TrackData())

    def test_fromXML_horiz_and_vert(self):
        table = self.font["trak"]
        for name, attrs, content in parseXML(OSAKA_TRAK_TABLE_XML):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.version, 1.0)
        self.assertEqual(table.format, 0)
        self.assertEqual(table.horizData, OSAKA_HORIZ_TRACK_ENTRIES)
        self.assertEqual(table.vertData, OSAKA_VERT_TRACK_ENTRIES)

    def test_fromXML_vert(self):
        table = self.font["trak"]
        for name, attrs, content in parseXML(OSAKA_VERT_ONLY_TRAK_TABLE_XML):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.version, 1.0)
        self.assertEqual(table.format, 0)
        self.assertEqual(table.horizData, TrackData())
        self.assertEqual(table.vertData, OSAKA_VERT_TRACK_ENTRIES)

    def test_toXML_horiz(self):
        table = self.font["trak"]
        table.horizData = TrackData(SKIA_TRACK_ENTRIES)
        add_name(self.font, "Tight", nameID=275)
        add_name(self.font, "Normal", nameID=303)
        add_name(self.font, "Loose", nameID=276)
        self.assertEqual(SKIA_TRAK_TABLE_XML, getXML(table.toXML, self.font))

    def test_toXML_horiz_and_vert(self):
        table = self.font["trak"]
        table.horizData = TrackData(OSAKA_HORIZ_TRACK_ENTRIES)
        table.vertData = TrackData(OSAKA_VERT_TRACK_ENTRIES)
        add_name(self.font, "Tight", nameID=262)
        add_name(self.font, "Normal", nameID=263)
        add_name(self.font, "Loose", nameID=264)
        add_name(self.font, "Tight", nameID=265)
        add_name(self.font, "Normal", nameID=266)
        add_name(self.font, "Loose", nameID=267)
        self.assertEqual(OSAKA_TRAK_TABLE_XML, getXML(table.toXML, self.font))

    def test_toXML_vert(self):
        table = self.font["trak"]
        table.vertData = TrackData(OSAKA_VERT_TRACK_ENTRIES)
        add_name(self.font, "Tight", nameID=265)
        add_name(self.font, "Normal", nameID=266)
        add_name(self.font, "Loose", nameID=267)
        self.assertEqual(OSAKA_VERT_ONLY_TRAK_TABLE_XML, getXML(table.toXML, self.font))

    def test_roundtrip_fromXML_toXML(self):
        font = {}
        add_name(font, "Tight", nameID=275)
        add_name(font, "Normal", nameID=303)
        add_name(font, "Loose", nameID=276)
        add_name(font, "Tight", nameID=262)
        add_name(font, "Normal", nameID=263)
        add_name(font, "Loose", nameID=264)
        add_name(font, "Tight", nameID=265)
        add_name(font, "Normal", nameID=266)
        add_name(font, "Loose", nameID=267)
        for input_xml in (
            SKIA_TRAK_TABLE_XML,
            OSAKA_TRAK_TABLE_XML,
            OSAKA_VERT_ONLY_TRAK_TABLE_XML,
        ):
            table = table__t_r_a_k()
            font["trak"] = table
            for name, attrs, content in parseXML(input_xml):
                table.fromXML(name, attrs, content, font)
            output_xml = getXML(table.toXML, font)
            self.assertEqual(input_xml, output_xml)


def add_name(font, string, nameID):
    nameTable = font.get("name")
    if nameTable is None:
        nameTable = font["name"] = table__n_a_m_e()
        nameTable.names = []
    namerec = NameRecord()
    namerec.nameID = nameID
    namerec.string = string.encode("mac_roman")
    namerec.platformID, namerec.platEncID, namerec.langID = (1, 0, 0)
    nameTable.names.append(namerec)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
