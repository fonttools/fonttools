import pytest

from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.reorderGlyphs import reorderGlyphs

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize("lazy", [True, False, None])
def test_reorder_glyphs(lazy):
    font_path = DATA_DIR / "Test-Regular.ttf"
    font = TTFont(str(font_path), lazy=lazy)
    old_coverage1 = list(
        font["GSUB"].table.LookupList.Lookup[0].SubTable[0].Coverage[0].glyphs
    )
    old_coverage2 = list(
        font["GPOS"].table.LookupList.Lookup[0].SubTable[0].Coverage.glyphs
    )

    ga = font.getGlyphOrder()
    ga = [ga[0]] + list(reversed(ga[1:]))
    reorderGlyphs(font, ga)

    new_coverage1 = list(
        font["GSUB"].table.LookupList.Lookup[0].SubTable[0].Coverage[0].glyphs
    )
    new_coverage2 = list(
        font["GPOS"].table.LookupList.Lookup[0].SubTable[0].Coverage.glyphs
    )

    assert list(reversed(old_coverage1)) == new_coverage1
    assert list(reversed(old_coverage2)) == new_coverage2


def test_ttfont_reorder_glyphs():
    font_path = DATA_DIR / "Test-Regular.ttf"
    font = TTFont(str(font_path))
    ga = font.getGlyphOrder()
    ga = [ga[0]] + list(reversed(ga[1:]))

    old_coverage1 = list(
        font["GSUB"].table.LookupList.Lookup[0].SubTable[0].Coverage[0].glyphs
    )
    old_coverage2 = list(
        font["GPOS"].table.LookupList.Lookup[0].SubTable[0].Coverage.glyphs
    )

    font.reorderGlyphs(ga)

    new_coverage1 = list(
        font["GSUB"].table.LookupList.Lookup[0].SubTable[0].Coverage[0].glyphs
    )
    new_coverage2 = list(
        font["GPOS"].table.LookupList.Lookup[0].SubTable[0].Coverage.glyphs
    )

    assert list(reversed(old_coverage1)) == new_coverage1
    assert list(reversed(old_coverage2)) == new_coverage2


def test_reorder_glyphs_cff():
    font_path = DATA_DIR / "TestVGID-Regular.otf"
    font = TTFont(str(font_path))
    ga = font.getGlyphOrder()
    ga = list(reversed(ga))
    reorderGlyphs(font, ga)

    assert list(font["CFF "].cff.topDictIndex[0].CharStrings.charStrings.keys()) == ga
    assert font["CFF "].cff.topDictIndex[0].charset == ga


def test_reorder_glyphs_bad_length(caplog):
    font_path = DATA_DIR / "Test-Regular.ttf"
    font = TTFont(str(font_path))
    with pytest.raises(ValueError) as ex:
        reorderGlyphs(font, ["A"])
    assert "New glyph order contains 1 glyphs" in str(ex.value)


def test_reorder_glyphs_bad_set(caplog):
    font_path = DATA_DIR / "Test-Regular.ttf"
    font = TTFont(str(font_path))
    ga = list(font.getGlyphOrder()) + ["AA"]
    ga.pop(1)
    with pytest.raises(ValueError) as ex:
        reorderGlyphs(font, ga)
    assert "New glyph order does not contain the same set of glyphs" in str(ex.value)
