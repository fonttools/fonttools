from fontTools.misc import xmlWriter
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import (
    ARGS_ARE_XY_VALUES,
    GID_IS_24_BIT,
    Glyph,
    GlyphCoordinates,
    GlyphComponent,
    flagCubic,
)
from fontTools.ttLib.tables import ttProgram


def cubic_glyph():
    glyph = Glyph()
    glyph.numberOfContours = 1
    glyph.coordinates = GlyphCoordinates([(0, 0), (1, 0), (1, 1), (0, 1)])
    glyph.endPtsOfContours = [3]
    glyph.flags = bytearray([flagCubic] * 4)
    glyph.program = ttProgram.Program()
    return glyph


def test_cubic_flag_is_uppercase_only():
    data = cubic_glyph().compile(newTable("GLYF"))

    upper_glyph = Glyph(data)
    upper_glyph.expand(newTable("GLYF"))
    assert all(flag & flagCubic for flag in upper_glyph.flags)

    lower_glyph = Glyph(data)
    lower_glyph.expand(newTable("glyf"))
    assert not any(flag & flagCubic for flag in lower_glyph.flags)

    data = cubic_glyph().compile(newTable("glyf"))
    recompiled_glyph = Glyph(data)
    recompiled_glyph.expand(newTable("GLYF"))
    assert not any(flag & flagCubic for flag in recompiled_glyph.flags)


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


def test_split_glyphs_use_uppercase_table_tag(tmp_path):
    class OutlineGlyph:
        numberOfContours = 1
        xMin = yMin = xMax = yMax = 0

        def expand(self, glyfTable):
            pass

        def toXML(self, writer, ttFont):
            pass

    font = TTFont()
    font.setGlyphOrder(["a"])
    glyf = font["GLYF"] = newTable("GLYF")
    glyf.glyphs = {"a": OutlineGlyph()}
    glyf.glyphOrder = font.getGlyphOrder()
    path = tmp_path / "GLYF.ttx"

    writer = xmlWriter.XMLWriter(path)
    glyf.toXML(writer, font, splitGlyphs=True)
    writer.close()

    glyphPath = next(p for p in tmp_path.iterdir() if p != path)
    assert "<GLYF>" in glyphPath.read_text()
