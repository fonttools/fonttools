from fontTools.ttLib.ttVisitor import TTVisitor
import fontTools.ttLib as ttLib
import fontTools.ttLib.tables.otBase as otBase
import fontTools.ttLib.tables.otTables as otTables
from fontTools.misc.fixedTools import otRound


class ScalerVisitor(TTVisitor):
    def __init__(self, scaleFactor):
        self.scaleFactor = scaleFactor

    def scale(self, v):
        return otRound(v * self.scaleFactor)


@ScalerVisitor.register_attrs(
    (
        (ttLib.getTableClass("head"), ("unitsPerEm", "xMin", "yMin", "xMax", "yMax")),
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
    )
)
def visit(visitor, obj, attr, value):
    setattr(obj, attr, visitor.scale(value))


@ScalerVisitor.register_attr(ttLib.getTableClass("hmtx"), "metrics")
def visit(visitor, obj, attr, metrics):
    for g in metrics:
        advance, lsb = metrics[g]
        metrics[g] = visitor.scale(advance), visitor.scale(lsb)


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


# GPOS


@ScalerVisitor.register(otTables.ValueRecord)
def visit(visitor, obj):
    attrs = ["XAdvance", "YAdvance", "XPlacement", "YPlacement"]
    for attr in attrs:
        v = getattr(obj, attr, None)
        if v is not None:
            v = visitor.scale(v)
            setattr(obj, attr, v)


@ScalerVisitor.register(otTables.Anchor)
def visit(visitor, obj):
    attrs = ["XCoordinate", "YCoordinate"]
    for attr in attrs:
        v = getattr(obj, attr)
        v = visitor.scale(v)
        setattr(obj, attr, v)


if __name__ == "__main__":

    from fontTools.ttLib import TTFont
    import sys

    if len(sys.argv) != 3:
        print("usage: scale-upem.py font new-upem")
        sys.exit()

    font = TTFont(sys.argv[1])
    new_upem = int(sys.argv[2])

    upem = font["head"].unitsPerEm

    visitor = ScalerVisitor(new_upem / upem)
    visitor.visit(font)

    font.save("out.ttf")
