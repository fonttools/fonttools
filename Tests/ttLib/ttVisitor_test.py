from fontTools.ttLib import TTFont
from fontTools.ttLib.ttVisitor import TTVisitor
import os
import pytest


class TestVisitor(TTVisitor):
    def __init__(self):
        self.value = []
        self.depth = 0

    def _add(self, s):
        self.value.append(s)

    def visit(self, obj, target_depth):
        if self.depth == target_depth:
            self._add(obj)
        self.depth += 1
        super().visit(obj, target_depth)
        self.depth -= 1


class TTVisitorTest(object):
    @staticmethod
    def getpath(testfile):
        path = os.path.dirname(__file__)
        return os.path.join(path, "data", testfile)

    def test_ttvisitor(self):
        font = TTFont(self.getpath("TestVGID-Regular.otf"))
        visitor = TestVisitor()

        # Count number of objects at depth 1:
        # That is, number of font tables, including GlyphOrder.
        visitor.visit(font, 1)

        assert len(visitor.value) == 14
