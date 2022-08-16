from fontTools.ttLib import TTFont
from fontTools.ttLib.ttVisitor import TTVisitor
import os
import pytest


class TTVisitorTest(object):

    @staticmethod
    def getpath(testfile):
        path = os.path.dirname(__file__)
        return os.path.join(path, "data", testfile)

    def test_ttvisitor(self):

        font = TTFont(self.getpath("TestVGID-Regular.otf"))
        visitor = TTVisitor()
        visitor.visit(font, 1, 2, arg=3)
