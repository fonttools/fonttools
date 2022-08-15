from fontTools.misc.visitor import TTVisitor
import fontTools.ttLib as ttLib
import fontTools.ttLib.tables.otBase as otBase
import fontTools.ttLib.tables.otTables as otTables


class ScalerVisitor(TTVisitor):
    def scale(self, v):
        return v // 2


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


from fontTools.ttLib import TTFont
import sys

font = TTFont(sys.argv[1])

visitor = ScalerVisitor()
visitor.visit(font)
