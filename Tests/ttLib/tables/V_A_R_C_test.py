from fontTools.ttLib import TTFont
from io import StringIO, BytesIO
import pytest
import os
import unittest

CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, "data")


class VarCompositeTest(unittest.TestCase):
    def test_basic(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        varc = font["VARC"]

        assert varc.table.Coverage.glyphs == [
            "uniAC00",
            "uniAC01",
            "glyph00003",
            "glyph00005",
            "glyph00007",
            "glyph00008",
            "glyph00009",
        ]

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        varc = font["VARC"]

        assert varc.table.Coverage.glyphs == [
            "uni6868",
            "glyph00002",
            "glyph00005",
            "glyph00007",
        ]

    def test_roundtrip(self):
        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-ac00-ac01.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()

        font_path = os.path.join(DATA_DIR, "..", "..", "data", "varc-6868.ttf")
        font = TTFont(font_path)
        tables = [
            table_tag
            for table_tag in font.keys()
            if table_tag not in {"head", "maxp", "hhea", "name", "fvar"}
        ]
        xml = StringIO()
        font.saveXML(xml)
        xml1 = StringIO()
        font.saveXML(xml1, tables=tables)
        xml.seek(0)
        font = TTFont()
        font.importXML(xml)
        ttf = BytesIO()
        font.save(ttf)
        ttf.seek(0)
        font = TTFont(ttf)
        xml2 = StringIO()
        font.saveXML(xml2, tables=tables)
        assert xml1.getvalue() == xml2.getvalue()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
