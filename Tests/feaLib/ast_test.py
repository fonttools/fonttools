from fontTools.feaLib import ast
from fontTools.feaLib.parser import Parser
from io import StringIO
import unittest


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

    def test_name_statements_escape_quote_and_backslash(self):
        string = 'a"b\\c'
        win = r'name "a\0022b\005cc";'
        mac = r'name 1 "a\22b\5cc";'
        for statement, expected in [
            (ast.FeatureNameStatement("ss01", 3, 1, 0x409, string), win),
            (ast.FeatureNameStatement("ss01", 1, 0, 0, string), mac),
            (ast.FeatureNameStatement("size", 3, 1, 0x409, string), "sizemenu" + win),
            (ast.STATNameStatement("stat", 3, 1, 0x409, string), win),
            (ast.STATNameStatement("stat", 1, 0, 0, string), mac),
            (
                ast.CVParametersNameStatement(
                    "cv01", 3, 1, 0x409, string, "FeatUILabelNameID"
                ),
                win,
            ),
        ]:
            with self.subTest(statement=type(statement).__name__):
                self.assertEqual(statement.asFea(), expected)

    def test_name_statements_keep_non_ascii(self):
        statement = ast.FeatureNameStatement("ss01", 3, 1, 0x411, "ローマン")
        self.assertEqual(statement.asFea(), 'name 3 1 1041 "ローマン";')

    def test_feature_names_roundtrip_quote_and_backslash(self):
        fea = (
            "feature ss01 {\n"
            "    featureNames {\n"
            '        name "a\\0022b\\005cc";\n'
            '        name 1 "a\\22b\\5cc";\n'
            "    };\n"
            "} ss01;\n"
        )
        doc = Parser(StringIO(fea), glyphNames=()).parse()
        reparsed = Parser(StringIO(doc.asFea()), glyphNames=()).parse()
        names = reparsed.statements[0].statements[0].statements
        self.assertEqual([n.string for n in names], ['a"b\\c', 'a"b\\c'])


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
