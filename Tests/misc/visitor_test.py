
class TestVisitor(OTVisitor):
    pass

import fontTools.ttLib.tables.otTables as otTables

@TestVisitor.register(otTables.Lookup)
def visit(visitor, obj):
    print(obj)
    return False

from fontTools.ttLib import TTFont
import sys

font = TTFont(sys.argv[1])
gsub = font['GSUB']

visitor = TestVisitor()
visitor.visit(gsub)
