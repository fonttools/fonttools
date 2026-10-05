import pytest

from io import BytesIO
from pathlib import Path
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont
from fontTools.ttLib.reorderGlyphs import reorderGlyphs

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize("lazy", [True, False, None])
@pytest.mark.parametrize("pairpos", [False, True])
def test_reorder_lazy_arrays(lazy, pairpos):
    from fontTools.misc.lazyTools import LazyList

    fb = FontBuilder(1000)
    order = [".notdef"] + [f"g{i}" for i in range(10)]
    fb.setupGlyphOrder(order)
    fb.setupPost()
    if pairpos:
        statements = [f"pos g0 g{i} {i + 1};" for i in range(10)]
    else:
        statements = [f"pos g{i} {i + 1};" for i in range(10)]
    addOpenTypeFeaturesFromString(
        fb.font, "feature kern { " + " ".join(statements) + " } kern;"
    )
    data = BytesIO()
    fb.font.save(data)
    font = TTFont(BytesIO(data.getvalue()), lazy=lazy)
    subtable = font["GPOS"].table.LookupList.Lookup[0].SubTable[0]
    records = subtable.PairSet[0].PairValueRecord if pairpos else subtable.Value
    assert isinstance(records, LazyList) == bool(lazy)
    reorderGlyphs(font, order[:1] + list(reversed(order[1:])))
    output = BytesIO()
    font.save(output)
    font = TTFont(BytesIO(output.getvalue()))
    subtable = font["GPOS"].table.LookupList.Lookup[0].SubTable[0]
    if pairpos:
        assert subtable.Coverage.glyphs == ["g0"]
        pairs = subtable.PairSet[0].PairValueRecord
        assert [record.SecondGlyph for record in pairs] == list(reversed(order[1:]))
        assert {
            (first, record.SecondGlyph): record.Value1.XAdvance
            for first, pair_set in zip(subtable.Coverage.glyphs, subtable.PairSet)
            for record in pair_set.PairValueRecord
        } == {("g0", f"g{i}"): i + 1 for i in range(10)}
    else:
        assert subtable.Coverage.glyphs == list(reversed(order[1:]))
        assert [v.XAdvance for v in subtable.Value] == list(reversed(range(1, 11)))


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
