"""Change the units-per-EM of a font.

Currently does not support CFF fonts. AAT, Graphite tables are not supported
either."""


from fontTools.ttLib.ttVisitor import TTVisitor
import fontTools.ttLib as ttLib
import fontTools.ttLib.tables.otBase as otBase
import fontTools.ttLib.tables.otTables as otTables
from fontTools.misc.fixedTools import otRound


__all__ = ["scale_upem", "ScalerVisitor"]


class ScalerVisitor(TTVisitor):
    def __init__(self, scaleFactor):
        self.scaleFactor = scaleFactor

    def scale(self, v):
        return otRound(v * self.scaleFactor)


@ScalerVisitor.register_attrs(
    (
        (ttLib.getTableClass("head"), ("unitsPerEm", "xMin", "yMin", "xMax", "yMax")),
        (ttLib.getTableClass("post"), ("underlinePosition", "underlineThickness")),
        (ttLib.getTableClass("VORG"), ("defaultVertOriginY")),
        (
            ttLib.getTableClass("hhea"),
            (
                "ascent",
                "descent",
                "lineGap",
                "advanceWidthMax",
                "minLeftSideBearing",
                "minRightSideBearing",
                "xMaxExtent",
                "caretOffset",
            ),
        ),
        (
            ttLib.getTableClass("vhea"),
            (
                "ascent",
                "descent",
                "lineGap",
                "advanceHeightMax",
                "minTopSideBearing",
                "minBottomSideBearing",
                "yMaxExtent",
                "caretOffset",
            ),
        ),
        (
            ttLib.getTableClass("OS/2"),
            (
                "xAvgCharWidth",
                "ySubscriptXSize",
                "ySubscriptYSize",
                "ySubscriptXOffset",
                "ySubscriptYOffset",
                "ySuperscriptXSize",
                "ySuperscriptYSize",
                "ySuperscriptXOffset",
                "ySuperscriptYOffset",
                "yStrikeoutSize",
                "yStrikeoutPosition",
                "sTypoAscender",
                "sTypoDescender",
                "sTypoLineGap",
                "usWinAscent",
                "usWinDescent",
                "sxHeight",
                "sCapHeight",
            ),
        ),
        (otTables.ValueRecord, ("XAdvance", "YAdvance", "XPlacement", "YPlacement")),
        (otTables.Anchor, ("XCoordinate", "YCoordinate")),
        (otTables.CaretValue, ("Coordinate")),
        (otTables.BaseCoord, ("Coordinate")),
        (otTables.ClipBox, ("xMin", "yMin", "xMax", "yMax")),
    )
)
def visit(visitor, obj, attr, value):
    setattr(obj, attr, visitor.scale(value))


@ScalerVisitor.register_attr(
    (ttLib.getTableClass("hmtx"), ttLib.getTableClass("vmtx")), "metrics"
)
def visit(visitor, obj, attr, metrics):
    for g in metrics:
        advance, lsb = metrics[g]
        metrics[g] = visitor.scale(advance), visitor.scale(lsb)


@ScalerVisitor.register_attr(ttLib.getTableClass("VMTX"), "VOriginRecords")
def visit(visitor, obj, attr, VOriginRecords):
    for g in VOriginRecords:
        VOriginRecords[g] = visitor.scale(VOriginRecords[g])


@ScalerVisitor.register_attr(ttLib.getTableClass("glyf"), "glyphs")
def visit(visitor, obj, attr, glyphs):
    for g in glyphs.values():
        if g.isComposite():
            for component in g.components:
                component.x = visitor.scale(component.x)
                component.y = visitor.scale(component.y)
        else:
            for attr in ("xMin", "xMax", "yMin", "yMax"):
                v = getattr(g, attr, None)
                if v is not None:
                    setattr(g, attr, visitor.scale(v))

        glyf = visitor.font["glyf"]
        coordinates = g.getCoordinates(glyf)[0]
        for i, (x, y) in enumerate(coordinates):
            coordinates[i] = visitor.scale(x), visitor.scale(y)


@ScalerVisitor.register_attr(ttLib.getTableClass("gvar"), "variations")
def visit(visitor, obj, attr, variations):
    for varlist in variations.values():
        for var in varlist:
            coordinates = var.coordinates
            for i, xy in enumerate(coordinates):
                if xy is None:
                    continue
                coordinates[i] = visitor.scale(xy[0]), visitor.scale(xy[1])


@ScalerVisitor.register_attr(ttLib.getTableClass("kern"), "kernTables")
def visit(visitor, obj, attr, kernTables):
    for table in kernTables:
        kernTable = table.kernTable
        for k in kernTable.keys():
            kernTable[k] = visitor.scale(kernTable[k])


# ItemVariationStore


@ScalerVisitor.register(otTables.VarData)
def visit(visitor, varData):
    for item in varData.Item:
        for i, v in enumerate(item):
            item[i] = visitor.scale(v)


# COLRv1


def _setup_scale_paint(paint, scale):
    if -2 <= scale <= 2 - (1 >> 14):
        paint.Format = 20  # PaintScaleUniform
        paint.scale = scale
        return

    transform = otTables.Affine2x3()
    transform.populateDefaults()
    transform.xy = transform.yx = transform.dx = transform.dy = 0
    transform.xx = transform.yy = scale

    paint.Format = 12  # PaintTransform
    paint.Transform = transform


@ScalerVisitor.register(otTables.BaseGlyphPaintRecord)
def visit(visitor, record):
    oldPaint = record.Paint

    scale = otTables.Paint()
    _setup_scale_paint(scale, visitor.scaleFactor)
    scale.Paint = oldPaint

    record.Paint = scale

    return True


@ScalerVisitor.register(otTables.Paint)
def visit(visitor, paint):
    if paint.Format != 10:  # PaintGlyph
        return True

    newPaint = otTables.Paint()
    newPaint.Format = paint.Format
    newPaint.Paint = paint.Paint
    newPaint.Glyph = paint.Glyph
    del paint.Paint
    del paint.Glyph

    _setup_scale_paint(paint, 1 / visitor.scaleFactor)
    paint.Paint = newPaint

    visitor.visit(newPaint.Paint)

    return False


def scale_upem(font, new_upem):
    """Change the units-per-EM of font to the new value."""
    upem = font["head"].unitsPerEm
    visitor = ScalerVisitor(new_upem / upem)
    visitor.visit(font)


if __name__ == "__main__":

    from fontTools.ttLib import TTFont
    import sys

    if len(sys.argv) != 3:
        print("usage: fonttools ttLib.scaleUpem font new-upem")
        sys.exit()

    font = TTFont(sys.argv[1])
    new_upem = int(sys.argv[2])

    if "CFF " in font or "CFF2" in font:
        print(
            "fonttools ttLib.scaleUpem: CFF/CFF2 fonts are not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    scale_upem(font, new_upem)

    print("Writing out.ttf")
    font.save("out.ttf")
