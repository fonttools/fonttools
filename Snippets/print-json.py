import fontTools.ttLib as ttLib
from fontTools.ttLib.ttVisitor import TTVisitor
from fontTools.misc.textTools import Tag


class JsonVisitor(TTVisitor):

    def _open(self, s):
        print(s, file=self.file)
        self._indent += self.indent

    def _close(self, s):
        self._indent = self._indent[:-len(self.indent)]
        print("%s%s," % (self._indent, s), file=self.file)

    def __init__(self, file, indent="  "):
        self.file = file
        self.indent = indent
        self._indent = ""

    def visitObject(self, obj):
        self._open("{")
        super().visitObject(obj)
        print('%s"type": "%s"' % (self._indent, obj.__class__.__name__), file=self.file)
        self._close("}")

    def visitAttr(self, obj, attr, value):
        print('%s"%s": ' % (self._indent, attr), end="", file=self.file)
        self.visit(value)

    def visitList(self, obj, *args, **kwargs):
        self._open("[")
        for value in obj:
            print(self._indent, end="", file=self.file)
            self.visit(value, *args, **kwargs)
        self._close("]")

    def visitDict(self, obj, *args, **kwargs):
        self._open("{")
        for key, value in obj.items():
            print('%s"%s": ' % (self._indent, key), end="", file=self.file)
            self.visit(value, *args, **kwargs)
        self._close("}")

    def visitLeaf(self, obj):
        if isinstance(obj, tuple):
            obj = list(obj)

        if isinstance(obj, bytes):
            s = repr(obj)
            s = s[1:]
        else:
            s = repr(obj)

        if s[0] == "'":
            s = '"' + s[1:-1] + '"'

        print("%s," % s, file=self.file)


@JsonVisitor.register(ttLib.TTFont)
def visit(self, font):
    if hasattr(visitor, "font"):
        return False
    visitor.font = font

    self._open("{")
    for tag in font.keys():
        print('%s"%s": ' % (self._indent, tag), end="", file=self.file)
        visitor.visit(font[tag])
    self._close("}")

    del visitor.font
    return False


@JsonVisitor.register_attr(ttLib.getTableClass("glyf"), "glyphOrder")
def visit(visitor, obj, attr, value):
    return False


@JsonVisitor.register(ttLib.getTableModule("glyf").GlyphCoordinates)
def visit(self, obj):
    self.visitList(obj)
    return False


@JsonVisitor.register(Tag)
def visit(self, obj):
    print('"%s",' % str(obj), file=self.file)
    return False


if __name__ == "__main__":

    from fontTools.ttLib import TTFont
    import sys

    if len(sys.argv) != 2:
        print("usage: print-json.py font")
        sys.exit()

    font = TTFont(sys.argv[1])

    visitor = JsonVisitor(sys.stdout)
    visitor.visit(font)
