#! /usr/bin/env python3

# Example script to remove overlaps in TTF using skia-pathops


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


def skpath_from_simple_glyph(glyphName, glyphSet):
    path = pathops.Path()
    pathPen = path.getPen()
    glyphSet[glyphName].draw(pathPen)
    return path


def skpath_from_composite_glyph(glyphName, glyphSet):
    # record TTGlyph outlines without components
    dcPen = DecomposingRecordingPen(glyphSet)
    glyphSet[glyphName].draw(dcPen)
    # replay recording onto a skia-pathops Path
    path = pathops.Path()
    pathPen = path.getPen()
    dcPen.replay(pathPen)
    return path


def tt_glyph_from_skpath(path):
    ttPen = TTGlyphPen(None)
    path.draw(ttPen)
    return ttPen.glyph()


def main():
    if len(sys.argv) != 3:
        print("usage: remove-overlaps.py fontfile.ttf outfile.ttf")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]

    with TTFont(src) as f:
        glyfTable = f["glyf"]
        glyphSet = f.getGlyphSet()

        for glyphName in glyphSet.keys():
            if glyfTable[glyphName].isComposite():
                path = skpath_from_composite_glyph(glyphName, glyphSet)
            else:
                path = skpath_from_simple_glyph(glyphName, glyphSet)

            # duplicate path
            path2 = pathops.Path(path)

            # remove overlaps
            path2.simplify()

            # replace TTGlyph if simplified copy is different
            if path2 != path:
                glyfTable[glyphName] = tt_glyph_from_skpath(path2)

        f.save(dst)


if __name__ == "__main__":
    main()
