"""Specialization of fontTools.misc.visitor to work with TTFont."""

from fontTools.misc.visitor import Visitor
from fontTools.ttLib import TTFont


class TTVisitor(Visitor):
    def visit(self, obj, *args, **kwargs):
        if hasattr(obj, "ensureDecompiled"):
            obj.ensureDecompiled(recurse=False)
        super().visit(obj, *args, **kwargs)


@TTVisitor.register(TTFont)
def visit(visitor, font):
    if hasattr(visitor, "font"):
        return False
    visitor.font = font
    for tag in font.keys():
        visitor.visit(font[tag])
    del visitor.font
    return False
