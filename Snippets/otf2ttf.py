#!/usr/bin/env python
from __future__ import print_function, division, absolute_import
import sys
from fontTools.ttLib import TTFont, newTable
from cu2qu.pens import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttx import makeOutputFileName
import argparse


# default approximation error, measured in UPEM
MAX_ERR = 1.0

# default 'post' table format
POST_FORMAT = 2.0

# assuming the input contours' direction is correctly set (counter-clockwise),
# we just flip it to clockwise
REVERSE_DIRECTION = True


def glyphs_to_quadratic(
        glyphs, max_err=MAX_ERR, reverse_direction=REVERSE_DIRECTION):
    quadGlyphs = {}
    for gname in glyphs.keys():
        glyph = glyphs[gname]
        ttPen = TTGlyphPen(glyphs)
        cu2quPen = Cu2QuPen(ttPen, max_err,
                            reverse_direction=reverse_direction)
        glyph.draw(cu2quPen)
        quadGlyphs[gname] = ttPen.glyph()
    return quadGlyphs


def otf_to_ttf(ttFont, post_format=POST_FORMAT, **kwargs):
    assert ttFont.sfntVersion == "OTTO"
    assert "CFF " in ttFont

    glyphOrder = ttFont.getGlyphOrder()

    ttFont["loca"] = newTable("loca")
    ttFont["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = glyphOrder
    glyf.glyphs = glyphs_to_quadratic(ttFont.getGlyphSet(), **kwargs)
    del ttFont["CFF "]

    ttFont["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        len(g.components if hasattr(g, 'components') else [])
        for g in glyf.glyphs.values())

    post = ttFont["post"]
    post.formatType = post_format
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyphOrder

    ttFont.sfntVersion = "\000\001\000\000"


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", metavar="INPUT")
    parser.add_argument("-o", "--output")
    parser.add_argument("-e", "--max-error", type=float, default=MAX_ERR)
    parser.add_argument("--post-format", type=float, default=POST_FORMAT)
    parser.add_argument(
        "--keep-direction", dest='reverse_direction', action='store_false')
    options = parser.parse_args(args)

    output = options.output or makeOutputFileName(options.input,
                                                  outputDir=None,
                                                  extension='.ttf')
    font = TTFont(options.input)
    otf_to_ttf(font,
               post_format=options.post_format,
               max_err=options.max_error,
               reverse_direction=options.reverse_direction)
    font.save(output)


if __name__ == "__main__":
    sys.exit(main())
