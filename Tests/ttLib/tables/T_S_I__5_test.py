from types import SimpleNamespace

import pytest
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib.tables.T_S_I__5 import table_T_S_I__5

# (type, length, offset) for 'extra' programs
TSI5_GLYPHGROUPS = {
    ".notdef": 1,
    "I": 1,
    "space": 1,
}

# compiled TSI5 table from data above
TSI5_DATA = deHexStr("0001 0001 0001")


class Font:
    def __init__(self, numGlyphs: int) -> None:
        self._numGlyphs = numGlyphs
        self._glyphs = {0: ".notdef", 1: "I", 2: "space"}
        self._tables = {"maxp": SimpleNamespace(numGlyphs=numGlyphs)}

    def __getitem__(self, key: str):
        return self._tables[key]

    def getGlyphName(self, glyphID: int):
        return self._glyphs.get(glyphID, f"glyph{glyphID:5d}")

    def getGlyphOrder(self):
        return list(self._glyphs.values())


@pytest.fixture
def table():
    return table_T_S_I__5()


@pytest.mark.parametrize(
    "numGlyphs, data, expected_glyphgroups",
    [
        (3, TSI5_DATA, TSI5_GLYPHGROUPS),
        (4, TSI5_DATA, TSI5_GLYPHGROUPS),
        (2, TSI5_DATA, TSI5_GLYPHGROUPS),
    ],
    ids=["simple", "fewer entries", "fewer glyphs"],
)
def test_decompile(table, numGlyphs, data, expected_glyphgroups):
    font = Font(numGlyphs)

    table.decompile(data, font)

    assert len(table.glyphGrouping) == 3
    assert table.glyphGrouping == expected_glyphgroups


@pytest.mark.parametrize(
    "numGlyphs, glyphgroups, expected_data",
    [
        (3, TSI5_GLYPHGROUPS, TSI5_DATA),
        (4, TSI5_GLYPHGROUPS, TSI5_DATA),
        (2, TSI5_GLYPHGROUPS, TSI5_DATA),
    ],
    ids=["simple", "fewer entries", "fewer glyphs"],
)
def test_compile(table, numGlyphs, glyphgroups, expected_data):
    # assert table.compile(ttFont=Font(numGlyphs)) == b""

    table.glyphGrouping = TSI5_GLYPHGROUPS
    data = table.compile(ttFont=Font(numGlyphs))
    assert data == expected_data


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
