from fontTools.misc.visitor import TTVisitor
import fontTools.ttLib.tables.otBase as otBase
import fontTools.ttLib.tables.otTables as otTables


class ScalerVisitor(TTVisitor):

    def scale(self, v):
        return v // 2

@ScalerVisitor.register(otTables.ValueRecord)
def visit(visitor, obj):
    attrs = ['XAdvance', 'YAdvance', 'XPlacement', 'YPlacement']
    for attr in attrs:
        v = getattr(obj, attr, None)
        if v is not None:
            v = visitor.scale(v)
            setattr(obj, attr, v)
    return False

@ScalerVisitor.register(otTables.Anchor)
def visit(visitor, obj):
    attrs = ['XCoordinate', 'YCoordinate']
    for attr in attrs:
        v = getattr(obj, attr)
        v = visitor.scale(v)
        setattr(obj, attr, v)
    return False


from fontTools.ttLib import TTFont
import sys

font = TTFont(sys.argv[1])

visitor = ScalerVisitor()
visitor.visit(font)
