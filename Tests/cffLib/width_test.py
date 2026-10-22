from fontTools.cffLib.width import _get_hmtx
from fontTools.ttLib import TTFont, newTable


def test_get_hmtx_prefers_uppercase_companion():
    font = TTFont()
    font["hmtx"] = newTable("hmtx")
    font["HMTX"] = newTable("HMTX")

    assert _get_hmtx(font) is font["HMTX"]


def test_get_hmtx_uses_lowercase_without_companion():
    font = TTFont()
    font["hmtx"] = newTable("hmtx")

    assert _get_hmtx(font) is font["hmtx"]
