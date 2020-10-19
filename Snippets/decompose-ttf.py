#! /usr/bin/env python3

# Example script to decompose the composite glyphs in a TTF into
# non-composite outlines.


import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

try:
    import pathops
except ImportError:
    sys.exit(
        "This script requires the skia-pathops module. "
        "`pip install skia-pathops` and then retry."
    )


if len(sys.argv) != 3:
    print("usage: decompose-ttf.py fontfile.ttf outfile.ttf")
    sys.exit(1)

src = sys.argv[1]
dst = sys.argv[2]

with TTFont(src) as f:
    glyfTable = f["glyf"]
    glyphSet = f.getGlyphSet()

    for glyphName in glyphSet.keys():
        if not glyfTable[glyphName].isComposite():
            continue

        # record TTGlyph outlines without components
        dcPen = DecomposingRecordingPen(glyphSet)
        glyphSet[glyphName].draw(dcPen)

        # replay recording onto a skia-pathops Path
        path = pathops.Path()
        pathPen = path.getPen()
        dcPen.replay(pathPen)

        # remove overlaps
        path.simplify()

        # create new TTGlyph from Path
        ttPen = TTGlyphPen(None)
        path.draw(ttPen)
        glyfTable[glyphName] = ttPen.glyph()

    f.save(dst)
