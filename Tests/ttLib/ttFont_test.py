import io
import os
import tempfile
from fontTools.ttLib import (
    TTFont,
    newTable,
    registerCustomTableClass,
    unregisterCustomTableClass,
)
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import pytest


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


@pytest.fixture
def ttf_path():
    font = TTFont()
    ttx = os.path.join(os.path.dirname(__file__), "data", "TestTTF-Regular.ttx")
    font.importXML(ttx)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        font.save(tmp)
    yield tmp.name
    os.remove(tmp.name)


@pytest.mark.parametrize("lazy", [True, False, None])
def test_overwrite_input_file(ttf_path, lazy):
    font2 = TTFont(ttf_path, lazy=lazy)
    font2.save(ttf_path)
