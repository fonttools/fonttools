from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
from fontTools.misc.textTools import deHexStr
from fontTools.varLib.builder import buildSparseVarRegionList
from io import StringIO, BytesIO
import pytest
import os
import unittest

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, "data")


@pytest.mark.parametrize("lazy", [False, True, None])
def test_sparse_region_axis_offsets(lazy):
    # Two differently sized region headers share one axis record. Axis offsets
    # are relative to their own region, not the enclosing region list.
    data = deHexStr("""
        00000002 0000000C 00000012
        0001 00000010
        0002 0000000A 00000012
        0000 0000 4000 4000
        0001 C000 C000 0000
        """)
    font = TTFont(lazy=lazy)
    regions = otTables.SparseVarRegionList()
    regions.decompile(OTTableReader(data), font)
    assert regions.RegionCount == 2
    assert regions.Region[0].SparseVarRegionAxis[0].PeakCoord == 1
    assert regions.Region[1].SparseVarRegionAxis[0].PeakCoord == 1
    assert regions.Region[1].SparseVarRegionAxis[1].AxisIndex == 1
    assert regions.Region[1].SparseVarRegionAxis[1].PeakCoord == -1

    writer = OTTableWriter()
    regions.compile(writer, font)
    reloaded = otTables.SparseVarRegionList()
    reloaded.decompile(OTTableReader(writer.getAllData()), font)
    assert reloaded.Region[1].SparseVarRegionAxis[1].PeakCoord == -1
    assert reloaded.Region[0].SparseVarRegionAxis[0].PeakCoord == 1


def test_sparse_region_count_uint32():
    font = TTFont(lazy=True)
    regions = buildSparseVarRegionList([{}], [])
    regions.Region *= 0x10000
    writer = OTTableWriter()
    regions.compile(writer, font)
    data = writer.getAllData()
    assert data[:4] == b"\0\1\0\0"
    reloaded = otTables.SparseVarRegionList()
    reloaded.decompile(OTTableReader(data), font)
    assert reloaded.RegionCount == 0x10000
    assert reloaded.Region[0xFFFF].SparseRegionCount == 0


@pytest.mark.parametrize("lazy", [False, True, None])
def test_delta_set_index_offset(lazy):
    # The INDEX is separated from the MultiVarData header by unrelated bytes.
    data = deHexStr(
        "010002 0000 0001 00000013 DEADBEEF DEADBEEF "
        "00000002 01 01 05 05 01 01 FE 80"
    )
    font = TTFont(lazy=lazy)
    table = otTables.MultiVarData()
    table.decompile(OTTableReader(data), font)
    assert table.Item == [[1, -2, 0], []]
    table.Item *= 6  # Exercise lazy INDEX decoding as well as eager decoding.
    writer = OTTableWriter()
    table.compile(writer, font)
    reloaded = otTables.MultiVarData()
    reloaded.decompile(OTTableReader(writer.getAllData()), font)
    assert list(reloaded.Item) == [[1, -2, 0], []] * 6


def test_empty_delta_set_index_offset():
    font = TTFont()
    table = otTables.MultiVarData()
    table.Format, table.VarRegionIndex, table.Item = 1, [], []
    writer = OTTableWriter()
    table.compile(writer, font)
    data = writer.getAllData()
    assert data == deHexStr("01 0000 00000007 00000000")
    reloaded = otTables.MultiVarData()
    reloaded.decompile(OTTableReader(data), font)
    assert reloaded.Item == []


class VarCompositeTest(unittest.TestCase):
    def test_basic(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        varc = font["VARC"]

        assert varc.table.Coverage.glyphs == [
            "uniAC00",
            "uniAC01",
            "glyph00003",
            "glyph00005",
            "glyph00007",
            "glyph00008",
            "glyph00009",
        ]

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        varc = font["VARC"]

        assert varc.table.Coverage.glyphs == [
            "uni6868",
            "glyph00002",
            "glyph00005",
            "glyph00007",
        ]

    def test_roundtrip(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea", "name", "fvar"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
