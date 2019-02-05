from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib import ast
import unittest


class AstTest(unittest.TestCase):
    def test_glyphname_escape(self):
        statement = ast.GlyphClass()
        for name in ("BASE", "NULL", "foo", "a"):
            statement.append(ast.GlyphName(name))
        self.assertEqual(statement.asFea(), r"[\BASE \NULL foo a]")


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
