#! /usr/bin/env python3

# Illustrates how a fonttools script can construct variable fonts.
#
# This script reads Roboto-Thin.ttf, Roboto-Regular.ttf, and
# Roboto-Black.ttf from /tmp/Roboto, and writes a Multiple Master GX
# font named "Roboto.ttf" into the current working directory.
# This output font supports interpolation along the Weight axis,
# and it contains named instances for "Thin", "Light", "Regular",
# "Bold", and "Black".
#
# All input fonts must contain the same set of glyphs, and these glyphs
# need to have the same control points in the same order. Note that this
# is *not* the case for the normal Roboto fonts that can be downloaded
# from Google. This demo script prints a warning for any problematic
# glyphs; in the resulting font, these glyphs will not be interpolated
# and get rendered in the "Regular" weight.
#
# Usage:
# $ mkdir /tmp/Roboto && cp Roboto-*.ttf /tmp/Roboto
# $ ./interpolate.py && open Roboto.ttf


from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r, Axis, NamedInstance
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r, TupleVariation
import logging


def AddFontVariations(font):
    assert "fvar" not in font
    fvar = font["fvar"] = table__f_v_a_r()

    weight = Axis()
    weight.axisTag = "wght"
    weight.nameID = AddName(font, "Weight").nameID
    weight.minValue, weight.defaultValue, weight.maxValue = (100, 400, 900)
    fvar.axes.append(weight)

    # https://www.microsoft.com/typography/otspec/os2.htm#wtc
    for name, wght in (
            ("Thin", 100),
            ("Light", 300),
            ("Regular", 400),
            ("Bold", 700),
            ("Black", 900)):
        inst = NamedInstance()
        inst.nameID = AddName(font, name).nameID
        inst.coordinates = {"wght": wght}
        fvar.instances.append(inst)


def AddName(font, name):
    """(font, "Bold") --> NameRecord"""
    nameTable = font.get("name")
    namerec = NameRecord()
    namerec.nameID = 1 + max([n.nameID for n in nameTable.names] + [256])
    namerec.string = name.encode("mac_roman")
    namerec.platformID, namerec.platEncID, namerec.langID = (1, 0, 0)
    nameTable.names.append(namerec)
    return namerec


def AddGlyphVariations(font, thin, regular, black):
    assert "gvar" not in font
    gvar = font["gvar"] = table__g_v_a_r()
    gvar.version = 1
    gvar.reserved = 0
    gvar.variations = {}
    for glyphName in regular.getGlyphOrder():
        regularCoord = GetCoordinates(regular, glyphName)
        thinCoord = GetCoordinates(thin, glyphName)
        blackCoord = GetCoordinates(black, glyphName)
        if not regularCoord or not blackCoord or not thinCoord:            
            logging.warning("glyph %s not present in all input fonts",
                            glyphName)
            continue
        if (len(regularCoord) != len(blackCoord) or
            len(regularCoord) != len(thinCoord)):
            logging.warning("glyph %s has not the same number of "
                            "control points in all input fonts", glyphName)
            continue
        thinDelta = []
        blackDelta = []
        for ((regX, regY), (blackX, blackY), (thinX, thinY)) in \
                zip(regularCoord, blackCoord, thinCoord):
            thinDelta.append(((thinX - regX, thinY - regY)))
            blackDelta.append((blackX - regX, blackY - regY))
        thinVar = TupleVariation({"wght": (-1.0, -1.0, 0.0)}, thinDelta)
        blackVar = TupleVariation({"wght": (0.0, 1.0, 1.0)}, blackDelta)
        gvar.variations[glyphName] = [thinVar, blackVar]


def GetCoordinates(font, glyphName):
    """font, glyphName --> glyph coordinates as expected by "gvar" table

    The result includes four "phantom points" for the glyph metrics,
    as mandated by the "gvar" spec.
    """
    glyphTable = font["glyf"]
    glyph = glyphTable.glyphs.get(glyphName)
    if glyph is None:
        return None
    glyph.expand(glyphTable)
    glyph.recalcBounds(glyphTable)
    if glyph.isComposite():
        coord = [c.getComponentInfo()[1][-2:] for c in glyph.components]
    else:
        coord = [c for c in glyph.getCoordinates(glyphTable)[0]]
    # Add phantom points for (left, right, top, bottom) positions.
    horizontalAdvanceWidth, leftSideBearing = font["hmtx"].metrics[glyphName]


    leftSideX = glyph.xMin - leftSideBearing
    rightSideX = leftSideX + horizontalAdvanceWidth

    # XXX these are incorrect.  Load vmtx and fix.
    topSideY = glyph.yMax
    bottomSideY = -glyph.yMin

    coord.extend([(leftSideX, 0),
                  (rightSideX, 0),
                  (0, topSideY),
                  (0, bottomSideY)])
    return coord


def main():
    logging.basicConfig(format="%(levelname)s: %(message)s")
    thin = TTFont("/tmp/Roboto/Roboto-Thin.ttf")
    regular = TTFont("/tmp/Roboto/Roboto-Regular.ttf")
    black = TTFont("/tmp/Roboto/Roboto-Black.ttf")
    out = regular
    AddFontVariations(out)
    AddGlyphVariations(out, thin, regular, black)
    out.save("./Roboto.ttf")


if __name__ == "__main__":
    import sys
    sys.exit(main())
