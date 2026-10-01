from fontTools import ttLib
from fontTools.otlLib import builder
from fontTools.otlLib.error import OpenTypeLibError
from fontTools.ttLib.tables import otTables
from types import SimpleNamespace
import pytest


def make_builder():
    font = ttLib.TTFont()
    glyphs = [".notdef"] + [f"g{i}" for i in range(1, 44000)]
    font.setGlyphOrder(glyphs + ["before", "after"])
    lookup_builder = builder.ChainContextSubstBuilder(font, None)
    even = glyphs[2::2]
    odd = glyphs[1::2]
    # Overlapping classes rule out format 2; each coverage is about 44KB, so
    # format 3 overflows the lookup offsets when all four rules are sized
    # together, but each consecutive pair fits.
    classes = [even, ["g1"] + even, odd, ["g2"] + odd]
    return lookup_builder, classes


def test_overflow_splits_rules_in_order():
    lookup_builder, classes = make_builder()
    for index, glyphs in enumerate(classes):
        # Only the last rule has context. Splitting must keep the lookup
        # chaining for the earlier rules, which have neither prefix nor suffix.
        context = index == 3
        lookup_builder.rules.append(
            builder.ChainContextualRule(
                [["before"]] if context else [],
                [glyphs],
                [["after"]] if context else [],
                [None if index == 0 else SimpleNamespace(lookup_index=index)],
            )
        )

    lookup = lookup_builder.build()

    assert len(lookup.SubTable) == 4
    for index, (subtable, glyphs) in enumerate(zip(lookup.SubTable, classes)):
        assert isinstance(subtable, otTables.ChainContextSubst)
        assert subtable.Format == 3
        assert [set(c.glyphs) for c in subtable.InputCoverage] == [set(glyphs)]
        assert [c.glyphs for c in subtable.BacktrackCoverage] == (
            [["before"]] if index == 3 else []
        )
        assert [c.glyphs for c in subtable.LookAheadCoverage] == (
            [["after"]] if index == 3 else []
        )
        assert [
            (r.SequenceIndex, r.LookupListIndex) for r in subtable.SubstLookupRecord
        ] == ([] if index == 0 else [(0, index)])


def test_single_rule_overflow_still_raises():
    lookup_builder, classes = make_builder()
    # An offset overflow inside a single format-3 subtable cannot be split.
    lookup_builder.rules.append(
        builder.ChainContextualRule([], classes[:3], [], [None, None, None])
    )
    with pytest.raises(OpenTypeLibError, match="^All candidates overflowed$"):
        lookup_builder.build()
