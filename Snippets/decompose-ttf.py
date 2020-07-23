#! /usr/bin/env python3

# Example script to decompose the composite glyphs in a TTF into
# non-composite outlines.


import sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


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
        dcPen = DecomposingRecordingPen(glyphSet)
        glyphSet[glyphName].draw(dcPen)
        ttPen = TTGlyphPen(None)
        dcPen.replay(ttPen)
        glyfTable[glyphName] = ttPen.glyph()

    f.save(dst)
