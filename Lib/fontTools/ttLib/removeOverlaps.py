""" Simplify TrueType glyphs by merging overlapping contours/components.

Requires https://github.com/fonttools/skia-pathops
"""

from typing import Iterable, Optional, Mapping

from fontTools.ttLib import ttFont
from fontTools.ttLib.tables import _g_l_y_f
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

import pathops


_TTGlyphMapping = Mapping[str, ttFont._TTGlyph]


def skPathFromSimpleGlyph(glyphName: str, glyphSet: _TTGlyphMapping) -> pathops.Path:
    path = pathops.Path()
    pathPen = path.getPen()
    glyphSet[glyphName].draw(pathPen)
    return path


def skPathFromCompositeGlyph(glyphName: str, glyphSet: _TTGlyphMapping) -> pathops.Path:
    # record TTGlyph outlines without components
    dcPen = DecomposingRecordingPen(glyphSet)
    glyphSet[glyphName].draw(dcPen)
    # replay recording onto a skia-pathops Path
    path = pathops.Path()
    pathPen = path.getPen()
    dcPen.replay(pathPen)
    return path


def ttfGlyphFromSkPath(path: pathops.Path) -> _g_l_y_f.Glyph:
    # Skia paths have no 'components', no need for glyphSet
    ttPen = TTGlyphPen(glyphSet=None)
    path.draw(ttPen)
    glyph = ttPen.glyph()
    assert not glyph.isComposite()
    # compute glyph.xMin (glyfTable parameter unused for non composites)
    glyph.recalcBounds(glyfTable=None)
    return glyph


def removeOverlaps(
    font: ttFont.TTFont, glyphNames: Optional[Iterable[str]] = None
) -> None:
    """ Simplify glyphs in TTFont by merging overlapping contours.

    Overlapping components are first decomposed to simple contours, then merged.

    Currently this only works with TrueType fonts with 'glyf' table.
    Raises NotImplementedError if 'glyf' table is absent.

    Args:
        font: input TTFont object, modified in place.
        glyphNames: optional iterable of glyph names (str) to remove overlaps from.
            By default, all glyphs in the font are processed.
    """
    try:
        glyfTable = font["glyf"]
    except KeyError:
        raise NotImplementedError("removeOverlaps currently only works with TTFs")

    hmtxTable = font["hmtx"]
    glyphSet = font.getGlyphSet()

    if glyphNames is None:
        glyphNames = font.getGlyphOrder()

    for glyphName in glyphNames:
        if glyfTable[glyphName].isComposite():
            path = skPathFromCompositeGlyph(glyphName, glyphSet)
        else:
            path = skPathFromSimpleGlyph(glyphName, glyphSet)

        # duplicate path
        path2 = pathops.Path(path)

        # remove overlaps
        path2.simplify()

        # replace TTGlyph if simplified copy is different
        if path2 != path:
            glyfTable[glyphName] = glyph = ttfGlyphFromSkPath(path2)
            # also ensure hmtx LSB == glyph.xMin so glyph origin is at x=0
            width, lsb = hmtxTable[glyphName]
            if lsb != glyph.xMin:
                hmtxTable[glyphName] = (width, glyph.xMin)


def main(args=None):
    import sys

    if args is None:
        args = sys.argv[1:]

    if len(args) < 2:
        print(
            f"usage: fonttools ttLib.removeOverlaps INPUT.ttf OUTPUT.ttf [GLYPHS ...]"
        )
        sys.exit(1)

    src = args[0]
    dst = args[1]
    glyphNames = args[2:] or None

    with ttFont.TTFont(src) as f:
        removeOverlaps(f, glyphNames)
        f.save(dst)


if __name__ == "__main__":
    main()
