#! /usr/bin/env python3

# Example script to remove overlaps in TTF using skia-pathops.
# Overlapping components will be decomposed.


import sys
from typing import Iterable, Optional, Mapping
from fontTools.ttLib import ttFont
from fontTools.ttLib.tables import _g_l_y_f
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

try:
    import pathops
except ImportError:
    sys.exit(
        "This script requires the skia-pathops module. "
        "`pip install skia-pathops` and then retry."
    )

_TTGlyphMapping = Mapping[str, ttFont._TTGlyph]


def skpath_from_simple_glyph(glyphName: str, glyphSet: _TTGlyphMapping) -> pathops.Path:
    path = pathops.Path()
    pathPen = path.getPen()
    glyphSet[glyphName].draw(pathPen)
    return path


def skpath_from_composite_glyph(
    glyphName: str, glyphSet: _TTGlyphMapping
) -> pathops.Path:
    # record TTGlyph outlines without components
    dcPen = DecomposingRecordingPen(glyphSet)
    glyphSet[glyphName].draw(dcPen)
    # replay recording onto a skia-pathops Path
    path = pathops.Path()
    pathPen = path.getPen()
    dcPen.replay(pathPen)
    return path


def simple_glyph_from_skpath(path: pathops.Path) -> _g_l_y_f.Glyph:
    # Skia paths have no 'components', no need for glyphSet
    ttPen = TTGlyphPen(glyphSet=None)
    path.draw(ttPen)
    glyph = ttPen.glyph()
    assert not glyph.isComposite()
    # compute glyph.xMin (glyfTable parameter unused for non composites)
    glyph.recalcBounds(glyfTable=None)
    return glyph


def remove_overlaps(
    font: ttFont.TTFont, glyphNames: Optional[Iterable[str]] = None
) -> None:
    if glyphNames is None:
        glyphNames = font.getGlyphOrder()

    glyfTable = font["glyf"]
    hmtxTable = font["hmtx"]
    glyphSet = font.getGlyphSet()

    for glyphName in glyphNames:
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
            glyfTable[glyphName] = glyph = simple_glyph_from_skpath(path2)
            # also ensure hmtx LSB == glyph.xMin so glyph origin is at x=0
            width, lsb = hmtxTable[glyphName]
            if lsb != glyph.xMin:
                hmtxTable[glyphName] = (width, glyph.xMin)


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: remove-overlaps.py fontfile.ttf outfile.ttf [GLYPHNAMES ...]")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]
    glyphNames = sys.argv[3:] or None

    with ttFont.TTFont(src) as f:
        remove_overlaps(f, glyphNames)
        f.save(dst)


if __name__ == "__main__":
    main()
