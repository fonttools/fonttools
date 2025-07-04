import unittest

from fontTools.feaLib import ast


class AstTest(unittest.TestCase):
    def test_glyphname_escape(self):
        statement = ast.GlyphClass()
        for name in ("BASE", "NULL", "foo", "a"):
            statement.append(ast.GlyphName(name))
        self.assertEqual(statement.asFea(), r"[\BASE \NULL foo a]")

    def test_valuerecord_none(self):
        statement = ast.ValueRecord(xPlacement=10, xAdvance=20)
        self.assertEqual(statement.asFea(), "<10 0 20 0>")

    def test_valuerecord_empty(self):
        statement = ast.ValueRecord()
        self.assertEqual(statement.asFea(), "<NULL>")

    def test_non_object_location(self):
        el = ast.Element(location=("file.fea", 1, 2))
        self.assertEqual(el.location.file, "file.fea")
        self.assertEqual(el.location.line, 1)
        self.assertEqual(el.location.column, 2)

    def test_single_pos_statement_empty_valuerecord(self):
        statement = ast.SinglePosStatement(
            pos=[(ast.GlyphName("a"), ast.ValueRecord())],
            prefix=[],
            suffix=[],
            forceChain=False,
        )
        self.assertEqual(statement.asFea(), "pos a <NULL>;")

    def test_single_pos_statement_empty_valuerecord_chain(self):
        statement = ast.SinglePosStatement(
            pos=[(ast.GlyphName("a"), ast.ValueRecord())],
            prefix=[],
            suffix=[],
            forceChain=True,
        )
        self.assertEqual(statement.asFea(), "pos a' <NULL>;")


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
