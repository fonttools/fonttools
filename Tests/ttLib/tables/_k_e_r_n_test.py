from __future__ import print_function, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._k_e_r_n import (
    KernTable_format_0, KernTable_format_unkown)
from fontTools.misc.textTools import deHexStr
from fontTools.misc.testTools import FakeFont, getXML, parseXML
import itertools
import pytest


KERN_VER_0_FMT_0_DATA = deHexStr(
    '0000 '            #  0: version=0
    '0001 '            #  2: nTables=1
    '0000 '            #  4: version=0 (bogus field, unused)
    '0020 '            #  6: length=32
    '00 '              #  8: format=0
    '01 '              #  9: coverage=1
    '0003 '            # 10: nPairs=3
    '000C '            # 12: searchRange=12
    '0001 '            # 14: entrySelector=1
    '0006 '            # 16: rangeShift=6
    '0004 000C FFD8 '  # 18: l=4, r=12, v=-40
    '0004 001C 0028 '  # 24: l=4, r=28, v=40
    '0005 0028 FFCE '  # 30: l=5, r=40, v=-50
)
assert len(KERN_VER_0_FMT_0_DATA) == 36

KERN_VER_0_FMT_0_XML = [
    '<version value="0"/>',
    '<kernsubtable coverage="1" format="0">',
    '  <pair l="E" r="M" v="-40"/>',
    '  <pair l="E" r="c" v="40"/>',
    '  <pair l="F" r="o" v="-50"/>',
    '</kernsubtable>',
]

KERN_VER_1_FMT_0_DATA = deHexStr(
    '0001 0000 '       #  0: version=1
    '0000 0001 '       #  4: nTables=1
    '0000 0022 '       #  8: length=34
    '00 '              # 12: coverage=0
    '00 '              # 13: format=0
    '0000 '            # 14: tupleIndex=0
    '0003 '            # 16: nPairs=3
    '000C '            # 18: searchRange=12
    '0001 '            # 20: entrySelector=1
    '0006 '            # 22: rangeShift=6
    '0004 000C FFD8 '  # 24: l=4, r=12, v=-40
    '0004 001C 0028 '  # 30: l=4, r=28, v=40
    '0005 0028 FFCE '  # 36: l=5, r=40, v=-50
)
assert len(KERN_VER_1_FMT_0_DATA) == 42

KERN_VER_1_FMT_0_XML = [
    '<version value="1.0"/>',
    '<kernsubtable coverage="0" format="0" tupleIndex="0">',
    '  <pair l="E" r="M" v="-40"/>',
    '  <pair l="E" r="c" v="40"/>',
    '  <pair l="F" r="o" v="-50"/>',
    '</kernsubtable>',
]

KERN_VER_0_FMT_UNKNOWN_DATA = deHexStr(
    '0000 '            #  0: version=0
    '0002 '            #  2: nTables=2
    '0000 '            #  4: version=0
    '000A '            #  6: length=10
    '04 '              #  8: format=4  (format 4 doesn't exist)
    '01 '              #  9: coverage=1
    '1234 5678 '       # 10: garbage...
    '0000 '            # 14: version=0
    '000A '            # 16: length=10
    '05 '              # 18: format=5  (format 5 doesn't exist)
    '01 '              # 19: coverage=1
    '9ABC DEF0 '       # 20: garbage...
)
assert len(KERN_VER_0_FMT_UNKNOWN_DATA) == 24

KERN_VER_0_FMT_UNKNOWN_XML = [
    '<version value="0"/>',
    '<kernsubtable format="4">',
    "  <!-- unknown 'kern' subtable format -->",
    '  0000000A 04011234',
    '  5678             ',
    '</kernsubtable>',
    '<kernsubtable format="5">',
    "<!-- unknown 'kern' subtable format -->",
    '  0000000A 05019ABC',
    '  DEF0             ',
    '</kernsubtable>',
]

KERN_VER_1_FMT_UNKNOWN_DATA = deHexStr(
    '0001 0000 '       #  0: version=1
    '0000 0002 '       #  4: nTables=2
    '0000 000C '       #  8: length=12
    '00 '              # 12: coverage=0
    '04 '              # 13: format=4  (format 4 doesn't exist)
    '0000 '            # 14: tupleIndex=0
    '1234 5678'        # 16: garbage...
    '0000 000C '       # 20: length=12
    '00 '              # 24: coverage=0
    '05 '              # 25: format=5  (format 5 doesn't exist)
    '0000 '            # 26: tupleIndex=0
    '9ABC DEF0 '       # 28: garbage...
)
assert len(KERN_VER_1_FMT_UNKNOWN_DATA) == 32

KERN_VER_1_FMT_UNKNOWN_XML = [
    '<version value="1"/>',
    '<kernsubtable format="4">',
    "  <!-- unknown 'kern' subtable format -->",
    '  0000000C 00040000',
    '  12345678         ',
    '</kernsubtable>',
    '<kernsubtable format="5">',
    "  <!-- unknown 'kern' subtable format -->",
    '  0000000C 00050000',
    '  9ABCDEF0         ',
    '</kernsubtable>',
]

KERN_VER_0_FMT_0_OVERFLOWING_DATA = deHexStr(
    '0000 '  #  0: version=0
    '0001 '  #  2: nTables=1
    '0000 '  #  4: version=0 (bogus field, unused)
    '0274 '  #  6: length=628 (bogus value for 66164 % 0x10000)
    '00 '    #  8: format=0
    '01 '    #  9: coverage=1
    '2B11 '  # 10: nPairs=11025
    'C000 '  # 12: searchRange=49152
    '000D '  # 14: entrySelector=13
    '4266 '  # 16: rangeShift=16998
) + deHexStr(' '.join(
    '%04X %04X %04X' % (a, b, 0)
    for (a, b) in itertools.product(range(105), repeat=2)
))


@pytest.fixture
def font():
    return FakeFont(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                         "abcdefghijklmnopqrstuvwxyz"))

@pytest.fixture
def overflowing_font():
    return FakeFont(["glyph%i" % i for i in range(105)])


class KernTableTest(object):

    @pytest.mark.parametrize(
        "data, version",
        [
            (KERN_VER_0_FMT_0_DATA, 0),
            (KERN_VER_1_FMT_0_DATA, 1.0),
        ],
        ids=["version_0", "version_1"]
    )
    def test_decompile_single_format_0(self, data, font, version):
        kern = newTable("kern")
        kern.decompile(data, font)

        assert kern.version == version
        assert len(kern.kernTables) == 1

        st = kern.kernTables[0]
        assert st.apple is (version == 1.0)
        assert st.format == 0
        # horizontal kerning in OT kern is coverage 0x01, while in
        # AAT kern it's the default (0)
        assert st.coverage == (0 if st.apple else 1)
        assert st.tupleIndex == (0 if st.apple else None)
        assert len(st.kernTable) == 3
        assert st.kernTable == {
            ('E', 'M'): -40,
            ('E', 'c'): 40,
            ('F', 'o'): -50
        }

    @pytest.mark.parametrize(
        "version, expected",
        [
            (0, KERN_VER_0_FMT_0_DATA),
            (1.0, KERN_VER_1_FMT_0_DATA),
        ],
        ids=["version_0", "version_1"]
    )
    def test_compile_single_format_0(self, font, version, expected):
        kern = newTable("kern")
        kern.version = version
        apple = version == 1.0
        st = KernTable_format_0(apple)
        kern.kernTables = [st]
        st.coverage = (0 if apple else 1)
        st.tupleIndex = 0 if apple else None
        st.kernTable = {
            ('E', 'M'): -40,
            ('E', 'c'): 40,
            ('F', 'o'): -50
        }
        data = kern.compile(font)
        assert data == expected

    @pytest.mark.parametrize(
        "xml, version",
        [
            (KERN_VER_0_FMT_0_XML, 0),
            (KERN_VER_1_FMT_0_XML, 1.0),
        ],
        ids=["version_0", "version_1"]
    )
    def test_fromXML_single_format_0(self, xml, font, version):
        kern = newTable("kern")
        for name, attrs, content in parseXML(xml):
            kern.fromXML(name, attrs, content, ttFont=font)

        assert kern.version == version
        assert len(kern.kernTables) == 1

        st = kern.kernTables[0]
        assert st.apple is (version == 1.0)
        assert st.format == 0
        assert st.coverage == (0 if st.apple else 1)
        assert st.tupleIndex == (0 if st.apple else None)
        assert len(st.kernTable) == 3
        assert st.kernTable == {
            ('E', 'M'): -40,
            ('E', 'c'): 40,
            ('F', 'o'): -50
        }

    @pytest.mark.parametrize(
        "version, expected",
        [
            (0, KERN_VER_0_FMT_0_XML),
            (1.0, KERN_VER_1_FMT_0_XML),
        ],
        ids=["version_0", "version_1"]
    )
    def test_toXML_single_format_0(self, font, version, expected):
        kern = newTable("kern")
        kern.version = version
        apple = version == 1.0
        st = KernTable_format_0(apple)
        kern.kernTables = [st]
        st.coverage = 0 if apple else 1
        st.tupleIndex = 0 if apple else None
        st.kernTable = {
            ('E', 'M'): -40,
            ('E', 'c'): 40,
            ('F', 'o'): -50
        }
        xml = getXML(kern.toXML, font)
        assert xml == expected

    @pytest.mark.parametrize(
        "data, version, header_length, st_length",
        [
            (KERN_VER_0_FMT_UNKNOWN_DATA, 0, 4, 10),
            (KERN_VER_1_FMT_UNKNOWN_DATA, 1.0, 8, 12),
        ],
        ids=["version_0", "version_1"]
    )
    def test_decompile_format_unknown(
            self, data, font, version, header_length, st_length):
        kern = newTable("kern")
        kern.decompile(data, font)

        assert kern.version == version
        assert len(kern.kernTables) == 2

        st_data = data[header_length:]
        st0 = kern.kernTables[0]
        assert st0.format == 4
        assert st0.data == st_data[:st_length]
        st_data = st_data[st_length:]

        st1 = kern.kernTables[1]
        assert st1.format == 5
        assert st1.data == st_data[:st_length]

    @pytest.mark.parametrize(
        "version, st_length, expected",
        [
            (0, 10, KERN_VER_0_FMT_UNKNOWN_DATA),
            (1.0, 12, KERN_VER_1_FMT_UNKNOWN_DATA),
        ],
        ids=["version_0", "version_1"]
    )
    def test_compile_format_unknown(self, version, st_length, expected):
        kern = newTable("kern")
        kern.version = version
        kern.kernTables = []

        for unknown_fmt, kern_data in zip((4, 5), ("1234 5678", "9ABC DEF0")):
            if version > 0:
                coverage = 0
                header_fmt = deHexStr(
                    "%08X %02X %02X %04X" % (
                        st_length, coverage, unknown_fmt, 0))
            else:
                coverage = 1
                header_fmt = deHexStr(
                    "%04X %04X %02X %02X" % (
                        0, st_length, unknown_fmt, coverage))
            st = KernTable_format_unkown(unknown_fmt)
            st.data = header_fmt + deHexStr(kern_data)
            kern.kernTables.append(st)

        data = kern.compile(font)
        assert data == expected

    @pytest.mark.parametrize(
        "xml, version, st_length",
        [
            (KERN_VER_0_FMT_UNKNOWN_XML, 0, 10),
            (KERN_VER_1_FMT_UNKNOWN_XML, 1.0, 12),
        ],
        ids=["version_0", "version_1"]
    )
    def test_fromXML_format_unknown(self, xml, font, version, st_length):
        kern = newTable("kern")
        for name, attrs, content in parseXML(xml):
            kern.fromXML(name, attrs, content, ttFont=font)

        assert kern.version == version
        assert len(kern.kernTables) == 2

        st0 = kern.kernTables[0]
        assert st0.format == 4
        assert len(st0.data) == st_length

        st1 = kern.kernTables[1]
        assert st1.format == 5
        assert len(st1.data) == st_length

    @pytest.mark.parametrize(
        "version", [0, 1.0], ids=["version_0", "version_1"])
    def test_toXML_format_unknown(self, font, version):
        kern = newTable("kern")
        kern.version = version
        st = KernTable_format_unkown(4)
        st.data = b"ABCD"
        kern.kernTables = [st]

        xml = getXML(kern.toXML, font)

        assert xml == [
            '<version value="%s"/>' % version,
            '<kernsubtable format="4">',
            '  <!-- unknown \'kern\' subtable format -->',
            '  41424344   ',
            '</kernsubtable>',
        ]

    def test_getkern(self):
        table = newTable("kern")
        table.version = 0
        table.kernTables = []

        assert table.getkern(0) is None

        st0 = KernTable_format_0()
        table.kernTables.append(st0)

        assert table.getkern(0) is st0
        assert table.getkern(4) is None

        st1 = KernTable_format_unkown(4)
        table.kernTables.append(st1)


class KernTable_format_0_Test(object):

    def test_decompileBadGlyphId(self, font):
        subtable = KernTable_format_0()
        subtable.decompile(
            b'\x00' + b'\x00' + b'\x00' + b'\x1a' + b'\x00' + b'\x00' +
            b'\x00' + b'\x02' + b'\x00' * 6 +
            b'\x00' + b'\x01' + b'\x00' + b'\x03' + b'\x00' + b'\x01' +
            b'\x00' + b'\x01' + b'\xFF' + b'\xFF' + b'\x00' + b'\x02',
            font)
        assert subtable[("B", "D")] == 1
        assert subtable[("B", "glyph65535")] == 2

    def test_compileOverflowingSubtable(self, overflowing_font):
        font = overflowing_font
        kern = newTable("kern")
        kern.version = 0
        st = KernTable_format_0(0)
        kern.kernTables = [st]
        st.coverage = 1
        st.tupleIndex = None
        st.kernTable = {
            (a, b): 0
            for (a, b) in itertools.product(
                font.getGlyphOrder(), repeat=2)
        }
        assert len(st.kernTable) == 11025
        data = kern.compile(font)
        assert data == KERN_VER_0_FMT_0_OVERFLOWING_DATA

    def test_decompileOverflowingSubtable(self, overflowing_font):
        font = overflowing_font
        data = KERN_VER_0_FMT_0_OVERFLOWING_DATA
        kern = newTable("kern")
        kern.decompile(data, font)

        st = kern.kernTables[0]
        assert st.kernTable == {
            (a, b): 0
            for (a, b) in itertools.product(
                font.getGlyphOrder(), repeat=2)
        }


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(sys.argv))
