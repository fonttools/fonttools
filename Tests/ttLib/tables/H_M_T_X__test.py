from fontTools.misc import sstruct
from fontTools.ttLib import TTFont, newTable


def makeHeader(tag, countName, count):
    table = newTable(tag)
    _, names, _ = sstruct.getformat(table.tableFormat)
    for name in names:
        setattr(table, name, 0)
    table.tableVersion = 0x00010000
    setattr(table, countName, count)
    return table


def test_extended_header_metric_count():
    font = TTFont(recalcBBoxes=False)
    for tag, countName in (("HHEA", "numberOfHMetrics"), ("VHEA", "numberOfVMetrics")):
        table = makeHeader(tag, countName, 0x10000)
        data = table.compile(font)
        assert len(data) == 38
        assert data[-4:] == b"\x00\x01\x00\x00"

        decompiled = newTable(tag)
        decompiled.decompile(data, font)
        assert getattr(decompiled, countName) == 0x10000


def test_HMTX_uses_locked_uppercase_tables():
    font = TTFont(recalcBBoxes=False)
    font.setGlyphOrder([".notdef", "a", "b"])
    font["MAXP"] = newTable("MAXP")
    font["MAXP"].numGlyphs = 3
    font["HHEA"] = makeHeader("HHEA", "numberOfHMetrics", 2)
    font["HMTX"] = newTable("HMTX")

    font["HMTX"].decompile(
        b"\x01\xf4\x00\x0a\x02\x58\x00\x14\x00\x1e",
        font,
    )
    assert font["HMTX"].metrics == {
        ".notdef": (500, 10),
        "a": (600, 20),
        "b": (600, 30),
    }

    font["HMTX"].compile(font)
    assert font["HHEA"].numberOfHMetrics == 2


def test_VMTX_uses_locked_uppercase_tables():
    table = newTable("VMTX")
    assert table.headerTag == "VHEA"
    assert table.maxpTag == "MAXP"
