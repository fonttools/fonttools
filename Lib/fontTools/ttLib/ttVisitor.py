"""Specialization of fontTools.misc.visitor to work with TTFont."""

from fontTools.misc.visitor import Visitor
from fontTools.ttLib import TTFont


class TTVisitor(Visitor):
    def visitAttr(self, obj, attr, value, *args, **kwargs):
        if isinstance(value, TTFont):
            return False
        super().visitAttr(obj, attr, value, *args, **kwargs)

    def visit(self, obj, *args, **kwargs):
        if hasattr(obj, "ensureDecompiled"):
            obj.ensureDecompiled(recurse=False)
        super().visit(obj, *args, **kwargs)


@TTVisitor.register(TTFont)
def visit(visitor, font, *args, **kwargs):
    if hasattr(visitor, "font"):
        return False
    visitor.font = font
    for tag in font.keys():
        visitor.visit(font[tag], *args, **kwargs)
    del visitor.font
    return False
