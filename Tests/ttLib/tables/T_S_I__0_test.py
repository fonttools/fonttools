from fontTools.misc.py23 import SimpleNamespace
from fontTools.misc.textTools import deHexStr
from fontTools.misc.testTools import getXML
from fontTools.ttLib.tables.T_S_I__0 import table_T_S_I__0
import pytest


# (gid, length, offset) for glyph programs
TSI0_INDICES = [
    (0, 1, 0),
    (1, 5, 1),
    (2, 0, 1),
    (3, 0, 1),
    (4, 8, 6)]

# (type, length, offset) for 'extra' programs
TSI0_EXTRA_INDICES = [
    (0xFFFA, 2, 14),          # ppgm
    (0xFFFB, 4, 16),          # cvt
    (0xFFFC, 6, 20),          # reserved
    (0xFFFD, 10, 26)]         # fpgm

# compiled TSI0 table from data above
TSI0_DATA = deHexStr(
    "0000 0001 00000000"
    "0001 0005 00000001"
    "0002 0000 00000001"
    "0003 0000 00000001"
    "0004 0008 00000006"
    "FFFE 0000 ABFC1F34"      # 'magic' separates glyph from extra programs
    "FFFA 0002 0000000E"
    "FFFB 0004 00000010"
    "FFFC 0006 00000014"
    "FFFD 000A 0000001A")

# empty font has no glyph programs but 4 extra programs are always present
EMPTY_TSI0_EXTRA_INDICES = [
    (0xFFFA, 0, 0),
    (0xFFFB, 0, 0),
    (0xFFFC, 0, 0),
    (0xFFFD, 0, 0)]

EMPTY_TSI0_DATA = deHexStr(
    "FFFE 0000 ABFC1F34"
    "FFFA 0000 00000000"
    "FFFB 0000 00000000"
    "FFFC 0000 00000000"
    "FFFD 0000 00000000")


@pytest.fixture
def table():
    return table_T_S_I__0()


@pytest.mark.parametrize(
    "numGlyphs, data, expected_indices, expected_extra_indices",
    [
        (5, TSI0_DATA, TSI0_INDICES, TSI0_EXTRA_INDICES),
        (0, EMPTY_TSI0_DATA, [], EMPTY_TSI0_EXTRA_INDICES)
    ],
    ids=["simple", "empty"]
)
def test_decompile(table, numGlyphs, data, expected_indices,
                   expected_extra_indices):
    font = {'maxp': SimpleNamespace(numGlyphs=numGlyphs)}

    table.decompile(data, font)

    assert len(table.indices) == numGlyphs
    assert table.indices == expected_indices
    assert len(table.extra_indices) == 4
    assert table.extra_indices == expected_extra_indices


@pytest.mark.parametrize(
    "numGlyphs, indices, extra_indices, expected_data",
    [
        (5, TSI0_INDICES, TSI0_EXTRA_INDICES, TSI0_DATA),
        (0, [], EMPTY_TSI0_EXTRA_INDICES, EMPTY_TSI0_DATA)
    ],
    ids=["simple", "empty"]
)
def test_compile(table, numGlyphs, indices, extra_indices, expected_data):
    assert table.compile(ttFont=None) == b""

    table.set(indices, extra_indices)
    data = table.compile(ttFont=None)
    assert data == expected_data


def test_set(table):
    table.set(TSI0_INDICES, TSI0_EXTRA_INDICES)
    assert table.indices == TSI0_INDICES
    assert table.extra_indices == TSI0_EXTRA_INDICES


def test_toXML(table):
    assert getXML(table.toXML, ttFont=None) == [
        '<!-- This table will be calculated by the compiler -->']


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(sys.argv))
