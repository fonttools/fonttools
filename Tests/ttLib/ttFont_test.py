import io
from pathlib import Path
from fontTools.ttLib import TTFont, newTable, registerCustomTableClass, unregisterCustomTableClass
from fontTools.ttLib.tables.DefaultTable import DefaultTable


class CustomTableClass(DefaultTable):

    def decompile(self, data, ttFont):
        self.numbers = list(data)

    def compile(self, ttFont):
        return bytes(self.numbers)

    # not testing XML read/write


table_C_U_S_T_ = CustomTableClass  # alias for testing


TABLETAG = "CUST"


def test_registerCustomTableClass():
    font = TTFont()
    font[TABLETAG] = newTable(TABLETAG)
    font[TABLETAG].data = b"\x00\x01\xff"
    f = io.BytesIO()
    font.save(f)
    f.seek(0)
    assert font[TABLETAG].data == b"\x00\x01\xff"
    registerCustomTableClass(TABLETAG, "ttFont_test", "CustomTableClass")
    try:
        font = TTFont(f)
        assert font[TABLETAG].numbers == [0, 1, 255]
        assert font[TABLETAG].compile(font) == b"\x00\x01\xff"
    finally:
        unregisterCustomTableClass(TABLETAG)


def test_registerCustomTableClassStandardName():
    registerCustomTableClass(TABLETAG, "ttFont_test")
    try:
        font = TTFont()
        font[TABLETAG] = newTable(TABLETAG)
        font[TABLETAG].numbers = [4, 5, 6]
        assert font[TABLETAG].compile(font) == b"\x04\x05\x06"
    finally:
        unregisterCustomTableClass(TABLETAG)


def test_gettabletags_method(tmp_path):
    tt_tables = ["head", "hhea", "maxp", "OS/2", "hmtx", "cmap", "fpgm", "prep", "cvt ", "loca", "glyf", "name", "post", "gasp", "DSIG"]
    cff_tables = ["head", "hhea", "maxp", "OS/2", "name", "cmap", "post", "CFF ", "hmtx", "DSIG"]

    # TT tests
      # xml import
    tt_font = TTFont()
    tt_font.importXML(Path("Tests/ttLib/data/TestTTF-Regular.ttx"))

    res_tt = tt_font.getTableTags()
    assert len(res_tt) == 15
    for table in tt_tables:
        assert table in tt_font
        assert table in res_tt

      # font binary file path read
    tt_path = tmp_path / "tt_test.ttf"
    tt_font.save(tt_path)
    tt_2_font = TTFont(tt_path)

    res_tt_2 = tt_2_font.getTableTags()
    assert len(res_tt_2) == 15
    for table in tt_tables:
        assert table in tt_2_font
        assert table in res_tt_2

    # CFF tests
      # xml import
    cff_font = TTFont()
    cff_font.importXML(Path("Tests/ttLib/data/TestOTF-Regular.otx"))

    res_cff = cff_font.getTableTags()
    assert len(res_cff) == 10
    for table in cff_tables:
        assert table in cff_font
        assert table in res_cff

      # font binary file path read
    cff_path = tmp_path / "cff_test.otf"
    cff_font.save(cff_path)
    cff_2_font = TTFont(cff_path)

    res_cff_2 = cff_2_font.getTableTags()
    assert len(res_cff_2) == 10
    for table in cff_tables:
        assert table in cff_2_font
        assert table in res_cff_2


