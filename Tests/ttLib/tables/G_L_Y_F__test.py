from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import (
    ARGS_ARE_XY_VALUES,
    GID_IS_24_BIT,
    Glyph,
    GlyphComponent,
)


def test_component_24bit_glyph_id():
    glyf = newTable("GLYF")
    glyf.getGlyphID = lambda name: 0x10000
    glyf.getGlyphName = lambda glyphID: "component"

    component = GlyphComponent()
    component.glyphName = "component"
    component.flags = 0
    component.x = component.y = 0

    data = component.compile(False, False, glyf)
    flags = int.from_bytes(data[:2], "big")
    assert flags == ARGS_ARE_XY_VALUES | GID_IS_24_BIT
    assert data[2:5] == b"\x01\x00\x00"

    decompiled = GlyphComponent()
    more, haveInstructions, remainder = decompiled.decompile(data, glyf)
    assert not more
    assert not haveInstructions
    assert not remainder
    assert decompiled.glyphName == "component"


def test_compile_updates_locked_uppercase_tables():
    font = TTFont(recalcBBoxes=False)
    font.setGlyphOrder([".notdef", "a"])
    font["GLYF"] = newTable("GLYF")
    font["GLYF"].glyphs = {name: Glyph() for name in font.getGlyphOrder()}
    font["GLYF"].glyphOrder = font.getGlyphOrder()
    font["LOCA"] = newTable("LOCA")
    font["MAXP"] = newTable("MAXP")
    font["MAXP"].tableVersion = 0x00005000

    font["GLYF"].compile(font)
    assert len(font["LOCA"].locations) == 3
    assert font["MAXP"].numGlyphs == 2
