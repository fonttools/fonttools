from io import StringIO
from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    SourceDescriptor,
)
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.varLib import build
from fontTools.varLib.builder import buildVarData
import pytest


@pytest.mark.parametrize(
    "region_indices, items, expected_num_shorts",
    [
        ([], [], 0),
        ([0], [[1]], 0),
        ([0], [[128]], 1),
        ([0, 1, 2], [[128, 1, 2], [3, -129, 5], [6, 7, 8]], 2),
        ([0, 1, 2], [[0, 128, 2], [3, 4, 5], [6, 7, -129]], 3),
        ([0], [[32768]], 0x8001),
        ([0, 1, 2], [[32768, 1, 2], [3, -129, 5], [6, 7, 8]], 0x8001),
        ([0, 1, 2], [[32768, 1, 2], [3, -32769, 5], [6, 7, 8]], 0x8002),
        ([0, 1, 2], [[0, 32768, 2], [3, 4, 5], [6, 7, -32769]], 0x8003),
    ],
    ids=[
        "0_regions_0_deltas",
        "1_region_1_uint8",
        "1_region_1_short",
        "3_regions_2_shorts_ordered",
        "3_regions_2_shorts_unordered",
        "1_region_1_long",
        "3_regions_1_long_ordered",
        "3_regions_2_longs_ordered",
        "3_regions_2_longs_unordered",
    ],
)
def test_buildVarData_no_optimize(region_indices, items, expected_num_shorts):
    data = buildVarData(region_indices, items, optimize=False)

    assert data.ItemCount == len(items)
    assert data.NumShorts == expected_num_shorts
    assert data.VarRegionCount == len(region_indices)
    assert data.VarRegionIndex == region_indices
    assert data.Item == items


@pytest.mark.parametrize(
    [
        "region_indices",
        "items",
        "expected_num_shorts",
        "expected_regions",
        "expected_items",
    ],
    [
        (
            [0, 1, 2],
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
            0,
            [0, 1, 2],
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 128, 2], [3, 4, 5], [6, 7, 8]],
            1,
            [1, 0, 2],
            [[128, 0, 2], [4, 3, 5], [7, 6, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 1, 128], [3, 4, 5], [6, -129, 8]],
            2,
            [1, 2, 0],
            [[1, 128, 0], [4, 5, 3], [-129, 8, 6]],
        ),
        (
            [0, 1, 2],
            [[128, 1, -129], [3, 4, 5], [6, 7, 8]],
            2,
            [0, 2, 1],
            [[128, -129, 1], [3, 5, 4], [6, 8, 7]],
        ),
        (
            [0, 1, 2],
            [[0, 1, 128], [3, -129, 5], [256, 7, 8]],
            3,
            [0, 1, 2],
            [[0, 1, 128], [3, -129, 5], [256, 7, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 128, 2], [0, 4, 5], [0, 7, 8]],
            1,
            [1, 2],
            [[128, 2], [4, 5], [7, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 32768, 2], [3, 4, 5], [6, 7, 8]],
            0x8001,
            [1, 0, 2],
            [[32768, 0, 2], [4, 3, 5], [7, 6, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 1, 32768], [3, 4, 5], [6, -32769, 8]],
            0x8002,
            [1, 2, 0],
            [[1, 32768, 0], [4, 5, 3], [-32769, 8, 6]],
        ),
        (
            [0, 1, 2],
            [[32768, 1, -32769], [3, 4, 5], [6, 7, 8]],
            0x8002,
            [0, 2, 1],
            [[32768, -32769, 1], [3, 5, 4], [6, 8, 7]],
        ),
        (
            [0, 1, 2],
            [[0, 1, 32768], [3, -32769, 5], [65536, 7, 8]],
            0x8003,
            [0, 1, 2],
            [[0, 1, 32768], [3, -32769, 5], [65536, 7, 8]],
        ),
        (
            [0, 1, 2],
            [[0, 32768, 2], [0, 4, 5], [0, 7, 8]],
            0x8001,
            [1, 2],
            [[32768, 2], [4, 5], [7, 8]],
        ),
    ],
    ids=[
        "0/3_shorts_no_reorder",
        "1/3_shorts_reorder",
        "2/3_shorts_reorder",
        "2/3_shorts_same_row_reorder",
        "3/3_shorts_no_reorder",
        "1/3_shorts_1/3_zeroes",
        "1/3_longs_reorder",
        "2/3_longs_reorder",
        "2/3_longs_same_row_reorder",
        "3/3_longs_no_reorder",
        "1/3_longs_1/3_zeroes",
    ],
)
def test_buildVarData_optimize(
    region_indices, items, expected_num_shorts, expected_regions, expected_items
):
    data = buildVarData(region_indices, items, optimize=True)

    assert data.ItemCount == len(items)
    assert data.NumShorts == expected_num_shorts
    assert data.VarRegionCount == len(expected_regions)
    assert data.VarRegionIndex == expected_regions
    assert data.Item == expected_items


def test_empty_vhvar_size():
    """HVAR/VHVAR should be present but empty when there are no glyph metrics
    variations, and should use a direct mapping for optimal encoding."""

    # Make a designspace that varies the outlines of 'A' but not its advance.
    doc = DesignSpaceDocument()

    doc.addAxis(
        AxisDescriptor(tag="wght", name="Weight", minimum=400, default=400, maximum=700)
    )

    for wght in (400, 700):
        # Outlines depend on weight.
        pen = TTGlyphPen(None)
        pen.lineTo((0, wght))
        pen.lineTo((wght, wght))
        pen.lineTo((wght, 0))
        pen.closePath()
        glyphs = {"A": pen.glyph()}

        fb = FontBuilder(unitsPerEm=1000)
        fb.setupGlyphOrder(list(glyphs.keys()))
        fb.setupGlyf(glyphs)

        # Horizontal advance does not vary.
        fb.setupHorizontalMetrics(
            {name: (500, fb.font["glyf"][name].xMin) for name in glyphs}  # type: ignore
        )
        fb.setupHorizontalHeader(ascent=1000, descent=0)

        # Vertical advance does not vary.
        fb.setupVerticalMetrics(
            {name: (500, 1000 - fb.font["glyf"][name].yMax) for name in glyphs}  # type: ignore
        )
        fb.setupVerticalHeader(ascent=1000, descent=0)

        fb.setupNameTable({"familyName": "TestEmptyVhvar", "styleName": "Regular"})
        fb.setupPost()
        doc.addSource(SourceDescriptor(font=fb.font, location={"Weight": wght}))

    # Compile.
    vf, *_ = build(doc)

    # Test both tables' encodings:
    for table in ("HVAR", "VVAR"):
        # Variable glyph metrics table should be built even when there are no
        # glyph metrics variations.
        assert table in vf

        # The table should be empty, and use a direct mapping for optimal size.
        expected = """
<?xml version="1.0" encoding="UTF-8"?>
<Version value="0x00010000"/>
<VarStore Format="1">
  <Format value="1"/>
  <VarRegionList>
    <!-- RegionAxisCount=1 -->
    <!-- RegionCount=0 -->
  </VarRegionList>
  <!-- VarDataCount=1 -->
  <VarData index="0">
    <!-- ItemCount=1 -->
    <NumShorts value="0"/>
    <!-- VarRegionCount=0 -->
    <Item index="0" value="[]"/>
  </VarData>
</VarStore>
""".lstrip()

        with StringIO() as buffer:
            writer = XMLWriter(buffer)
            vf[table].toXML(writer, vf)
            actual = buffer.getvalue()
        assert actual == expected

        # The table should be encodable in at least this size.
        # (VVAR has an extra Offset32 to point to a vertical origin mapping)
        optimal_size = {"HVAR": 42, "VVAR": 46}[table]
        assert len(vf[table].compile(vf)) <= optimal_size


def test_vhvar_beyond_64k():
    """varLib can build HVAR/VVAR for fonts with more than 0xFFFF glyphs.

    The advance store uses the indirect mapping (the direct/no-map store can't
    index more than 0xFFFF glyphs, since VarData.ItemCount is uint16), and the
    advance index map escalates to DeltaSetIndexMap Format 1 (uint32 MappingCount)
    when a glyph beyond gid 0xFFFF varies.
    """
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    from fontTools.ttLib.tables.otBase import OTTableWriter

    n = 0x10001  # 65537 glyphs -> highest gid is 0x10000
    glyph_order = [".notdef"] + ["g%05d" % i for i in range(1, n)]
    high = glyph_order[-1]

    doc = DesignSpaceDocument()
    doc.addAxis(
        AxisDescriptor(tag="wght", name="Weight", minimum=0, default=0, maximum=1000)
    )
    # the two advances just need to differ so the high glyph actually varies
    for wght, adv in ((0, 480), (1000, 520)):
        fb = FontBuilder(unitsPerEm=1000)
        fb.setupGlyphOrder(glyph_order)
        fb.setupGlyf({g: Glyph() for g in glyph_order})
        # Only the highest glyph's advances vary, so the map cannot be trimmed
        # below 65536 entries and must use Format 1.
        hmetrics = {g: (500, 0) for g in glyph_order}
        vmetrics = {g: (500, 0) for g in glyph_order}
        hmetrics[high] = vmetrics[high] = (adv, 0)
        fb.setupHorizontalMetrics(hmetrics)
        fb.setupHorizontalHeader(ascent=1000, descent=0)
        fb.setupVerticalMetrics(vmetrics)
        fb.setupVerticalHeader(ascent=1000, descent=0)
        fb.setupNameTable({"familyName": "TestBeyond64k", "styleName": "Regular"})
        fb.setupPost(keepGlyphNames=False)
        doc.addSource(SourceDescriptor(font=fb.font, location={"Weight": wght}))

    vf, *_ = build(doc)

    for tableTag, mapName in (("HVAR", "AdvWidthMap"), ("VVAR", "AdvHeightMap")):
        assert tableTag in vf
        advMap = getattr(vf[tableTag].table, mapName)
        assert advMap is not None
        writer = OTTableWriter()
        advMap.compile(writer, vf)
        assert (
            writer.getAllData()[0] == 1
        ), f"{tableTag}.{mapName} should use DeltaSetIndexMap Format 1"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
