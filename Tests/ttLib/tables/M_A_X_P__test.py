from fontTools.ttLib import TTFont, newTable


def test_compile_decompile():
    font = TTFont(recalcBBoxes=False)
    font.setGlyphOrder([".notdef", "a", "b"])
    table = font["MAXP"] = newTable("MAXP")
    table.tableVersion = 0x00005000

    data = table.compile(font)
    assert data == b"\x00\x00\x50\x00\x00\x00\x03"

    decompiled = newTable("MAXP")
    decompiled.decompile(data, font)
    assert decompiled.tableVersion == 0x00005000
    assert decompiled.numGlyphs == 3
