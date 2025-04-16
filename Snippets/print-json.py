import fontTools.ttLib as ttLib
from fontTools.ttLib.ttVisitor import TTVisitor
from fontTools.misc.textTools import Tag
from array import array


class JsonVisitor(TTVisitor):
    def _open(self, s):
        print(s, file=self.file)
        self._indent += self.indent
        self.comma = False

    def _close(self, s):
        self._indent = self._indent[: -len(self.indent)]
        print("\n%s%s" % (self._indent, s), end="", file=self.file)
        self.comma = True

    def __init__(self, file, indent="  "):
        self.file = file
        self.indent = indent
        self._indent = ""

    def visitObject(self, obj):
        self._open("{")
        super().visitObject(obj)
        if self.comma:
            print(",", end="", file=self.file)
        print(
            '\n%s"type": "%s"' % (self._indent, obj.__class__.__name__),
            end="",
            file=self.file,
        )
        self._close("}")

    def visitAttr(self, obj, attr, value):
        if self.comma:
            print(",", file=self.file)
        print('%s"%s": ' % (self._indent, attr), end="", file=self.file)
        self.visit(value)
        self.comma = True

    def visitList(self, obj, *args, **kwargs):
        self._open("[")
        comma = False
        for value in obj:
            if comma:
                print(",", end="", file=self.file)
                print(file=self.file)
            print(self._indent, end="", file=self.file)
            self.visit(value, *args, **kwargs)
            comma = True
        self._close("]")

    def visitDict(self, obj, *args, **kwargs):
        self._open("{")
        comma = False
        for key, value in obj.items():
            if comma:
                print(",", end="", file=self.file)
                print(file=self.file)
            print('%s"%s": ' % (self._indent, key), end="", file=self.file)
            self.visit(value, *args, **kwargs)
            comma = True
        self._close("}")

    def visitLeaf(self, obj):
        if isinstance(obj, tuple):
            obj = list(obj)
        elif isinstance(obj, bytes):
            obj = list(obj)

        if obj is None:
            s = "null"
        elif obj is True:
            s = "true"
        elif obj is False:
            s = "false"
        else:
            s = repr(obj)

        if s[0] == "'":
            s = '"' + s[1:-1] + '"'

        print("%s" % s, end="", file=self.file)


@JsonVisitor.register(ttLib.TTFont)
def visit(self, font):
    if hasattr(visitor, "font"):
        print("{}", end="", file=self.file)
        return False
    visitor.font = font

    self._open("{")
    for tag in font.keys():
        if self.comma:
            print(",", file=self.file)
        print('\n%s"%s": ' % (self._indent, tag), end="", file=self.file)
        visitor.visit(font[tag])
    self._close("}")

    del visitor.font
    return False


@JsonVisitor.register(ttLib.GlyphOrder)
def visit(self, obj):
    self.visitList(self.font.getGlyphOrder())
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
    print('"%s"' % str(obj), end="", file=self.file)
    return False


@JsonVisitor.register(array)
def visit(self, obj):
    self.visitList(obj)
    return False


@JsonVisitor.register(bytearray)
def visit(self, obj):
    self.visitList(obj)
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
