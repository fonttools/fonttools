from fontTools.ttLib import TTFont, newTable
from fontTools.varLib.mvar import getMVARTableTag


def test_getMVARTableTag_prefers_uppercase_companions():
    font = TTFont()
    font["hhea"] = newTable("hhea")
    font["HHEA"] = newTable("HHEA")
    font["vhea"] = newTable("vhea")
    font["VHEA"] = newTable("VHEA")

    assert getMVARTableTag(font, "hhea") == "HHEA"
    assert getMVARTableTag(font, "vhea") == "VHEA"
    assert getMVARTableTag(font, "OS/2") == "OS/2"


def test_getMVARTableTag_keeps_lowercase_without_companions():
    font = TTFont()
    font["hhea"] = newTable("hhea")
    font["vhea"] = newTable("vhea")

    assert getMVARTableTag(font, "hhea") == "hhea"
    assert getMVARTableTag(font, "vhea") == "vhea"
