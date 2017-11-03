from __future__ import print_function, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._k_e_r_n import KernTable_format_0
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.testTools import FakeFont, getXML, parseXML
import pytest


KERN_VER_0_FMT_0_DATA = deHexStr(
    '0000 '            #  0: version=0
    '0001 '            #  2: nTables=1
    '0000 '            #  4: version=0 (bogus field, unused)
    '0020 '            #  6: length=32
    '0000 '            #  8: coverage=0
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
    '<kernsubtable coverage="0" format="0">',
    '  <pair l="E" r="M" v="-40"/>',
    '  <pair l="E" r="c" v="40"/>',
    '  <pair l="F" r="o" v="-50"/>',
    '</kernsubtable>',
]

KERN_VER_1_FMT_0_DATA = deHexStr(
    '0001 0000 '       #  0: version=1
    '0000 0001 '       #  4: nTables=1
    '0000 0022 '       #  8: length=34
    '0000 '            # 12: coverage=0
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


@pytest.fixture
def font():
    return FakeFont(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                         "abcdefghijklmnopqrstuvwxyz"))


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
        assert st.coverage == 0
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
        st.coverage = 0
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
        assert st.coverage == 0
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
        st.coverage = 0
        st.tupleIndex = 0 if apple else None
        st.kernTable = {
            ('E', 'M'): -40,
            ('E', 'c'): 40,
            ('F', 'o'): -50
        }
        xml = getXML(kern.toXML, font)
        assert xml == expected


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


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(sys.argv))
