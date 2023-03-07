from fontTools import unicodedata

import pytest


def test_script():
    assert unicodedata.script("a") == "Latn"
    assert unicodedata.script(chr(0)) == "Zyyy"
    assert unicodedata.script(chr(0x0378)) == "Zzzz"
    assert unicodedata.script(chr(0x10FFFF)) == "Zzzz"

    # these were randomly sampled, one character per script
    assert unicodedata.script(chr(0x1E918)) == "Adlm"
    assert unicodedata.script(chr(0x1170D)) == "Ahom"
    assert unicodedata.script(chr(0x145A0)) == "Hluw"
    assert unicodedata.script(chr(0x0607)) == "Arab"
    assert unicodedata.script(chr(0x056C)) == "Armn"
    assert unicodedata.script(chr(0x10B27)) == "Avst"
    assert unicodedata.script(chr(0x1B41)) == "Bali"
    assert unicodedata.script(chr(0x168AD)) == "Bamu"
    assert unicodedata.script(chr(0x16ADD)) == "Bass"
    assert unicodedata.script(chr(0x1BE5)) == "Batk"
    assert unicodedata.script(chr(0x09F3)) == "Beng"
    assert unicodedata.script(chr(0x11C5B)) == "Bhks"
    assert unicodedata.script(chr(0x3126)) == "Bopo"
    assert unicodedata.script(chr(0x1103B)) == "Brah"
    assert unicodedata.script(chr(0x2849)) == "Brai"
    assert unicodedata.script(chr(0x1A0A)) == "Bugi"
    assert unicodedata.script(chr(0x174E)) == "Buhd"
    assert unicodedata.script(chr(0x18EE)) == "Cans"
    assert unicodedata.script(chr(0x102B7)) == "Cari"
    assert unicodedata.script(chr(0x1053D)) == "Aghb"
    assert unicodedata.script(chr(0x11123)) == "Cakm"
    assert unicodedata.script(chr(0xAA1F)) == "Cham"
    assert unicodedata.script(chr(0xAB95)) == "Cher"
    assert unicodedata.script(chr(0x1F0C7)) == "Zyyy"
    assert unicodedata.script(chr(0x2C85)) == "Copt"
    assert unicodedata.script(chr(0x12014)) == "Xsux"
    assert unicodedata.script(chr(0x1082E)) == "Cprt"
    assert unicodedata.script(chr(0xA686)) == "Cyrl"
    assert unicodedata.script(chr(0x10417)) == "Dsrt"
    assert unicodedata.script(chr(0x093E)) == "Deva"
    assert unicodedata.script(chr(0x1BC4B)) == "Dupl"
    assert unicodedata.script(chr(0x1310C)) == "Egyp"
    assert unicodedata.script(chr(0x1051C)) == "Elba"
    assert unicodedata.script(chr(0x2DA6)) == "Ethi"
    assert unicodedata.script(chr(0x10AD)) == "Geor"
    assert unicodedata.script(chr(0x2C52)) == "Glag"
    assert unicodedata.script(chr(0x10343)) == "Goth"
    assert unicodedata.script(chr(0x11371)) == "Gran"
    assert unicodedata.script(chr(0x03D0)) == "Grek"
    assert unicodedata.script(chr(0x0AAA)) == "Gujr"
    assert unicodedata.script(chr(0x0A4C)) == "Guru"
    assert unicodedata.script(chr(0x23C9F)) == "Hani"
    assert unicodedata.script(chr(0xC259)) == "Hang"
    assert unicodedata.script(chr(0x1722)) == "Hano"
    assert unicodedata.script(chr(0x108F5)) == "Hatr"
    assert unicodedata.script(chr(0x05C2)) == "Hebr"
    assert unicodedata.script(chr(0x1B072)) == "Hira"
    assert unicodedata.script(chr(0x10847)) == "Armi"
    assert unicodedata.script(chr(0x033A)) == "Zinh"
    assert unicodedata.script(chr(0x10B66)) == "Phli"
    assert unicodedata.script(chr(0x10B4B)) == "Prti"
    assert unicodedata.script(chr(0xA98A)) == "Java"
    assert unicodedata.script(chr(0x110B2)) == "Kthi"
    assert unicodedata.script(chr(0x0CC6)) == "Knda"
    assert unicodedata.script(chr(0x3337)) == "Kana"
    assert unicodedata.script(chr(0xA915)) == "Kali"
    assert unicodedata.script(chr(0x10A2E)) == "Khar"
    assert unicodedata.script(chr(0x17AA)) == "Khmr"
    assert unicodedata.script(chr(0x11225)) == "Khoj"
    assert unicodedata.script(chr(0x112B6)) == "Sind"
    assert unicodedata.script(chr(0x0ED7)) == "Laoo"
    assert unicodedata.script(chr(0xAB3C)) == "Latn"
    assert unicodedata.script(chr(0x1C48)) == "Lepc"
    assert unicodedata.script(chr(0x1923)) == "Limb"
    assert unicodedata.script(chr(0x1071D)) == "Lina"
    assert unicodedata.script(chr(0x100EC)) == "Linb"
    assert unicodedata.script(chr(0xA4E9)) == "Lisu"
    assert unicodedata.script(chr(0x10284)) == "Lyci"
    assert unicodedata.script(chr(0x10926)) == "Lydi"
    assert unicodedata.script(chr(0x11161)) == "Mahj"
    assert unicodedata.script(chr(0x0D56)) == "Mlym"
    assert unicodedata.script(chr(0x0856)) == "Mand"
    assert unicodedata.script(chr(0x10AF0)) == "Mani"
    assert unicodedata.script(chr(0x11CB0)) == "Marc"
    assert unicodedata.script(chr(0x11D28)) == "Gonm"
    assert unicodedata.script(chr(0xABDD)) == "Mtei"
    assert unicodedata.script(chr(0x1E897)) == "Mend"
    assert unicodedata.script(chr(0x109B0)) == "Merc"
    assert unicodedata.script(chr(0x10993)) == "Mero"
    assert unicodedata.script(chr(0x16F5D)) == "Plrd"
    assert unicodedata.script(chr(0x1160B)) == "Modi"
    assert unicodedata.script(chr(0x18A8)) == "Mong"
    assert unicodedata.script(chr(0x16A48)) == "Mroo"
    assert unicodedata.script(chr(0x1128C)) == "Mult"
    assert unicodedata.script(chr(0x105B)) == "Mymr"
    assert unicodedata.script(chr(0x108AF)) == "Nbat"
    assert unicodedata.script(chr(0x19B3)) == "Talu"
    assert unicodedata.script(chr(0x1143D)) == "Newa"
    assert unicodedata.script(chr(0x07F4)) == "Nkoo"
    assert unicodedata.script(chr(0x1B192)) == "Nshu"
    assert unicodedata.script(chr(0x169C)) == "Ogam"
    assert unicodedata.script(chr(0x1C56)) == "Olck"
    assert unicodedata.script(chr(0x10CE9)) == "Hung"
    assert unicodedata.script(chr(0x10316)) == "Ital"
    assert unicodedata.script(chr(0x10A93)) == "Narb"
    assert unicodedata.script(chr(0x1035A)) == "Perm"
    assert unicodedata.script(chr(0x103D5)) == "Xpeo"
    assert unicodedata.script(chr(0x10A65)) == "Sarb"
    assert unicodedata.script(chr(0x10C09)) == "Orkh"
    assert unicodedata.script(chr(0x0B60)) == "Orya"
    assert unicodedata.script(chr(0x104CF)) == "Osge"
    assert unicodedata.script(chr(0x104A8)) == "Osma"
    assert unicodedata.script(chr(0x16B12)) == "Hmng"
    assert unicodedata.script(chr(0x10879)) == "Palm"
    assert unicodedata.script(chr(0x11AF1)) == "Pauc"
    assert unicodedata.script(chr(0xA869)) == "Phag"
    assert unicodedata.script(chr(0x10909)) == "Phnx"
    assert unicodedata.script(chr(0x10B81)) == "Phlp"
    assert unicodedata.script(chr(0xA941)) == "Rjng"
    assert unicodedata.script(chr(0x16C3)) == "Runr"
    assert unicodedata.script(chr(0x0814)) == "Samr"
    assert unicodedata.script(chr(0xA88C)) == "Saur"
    assert unicodedata.script(chr(0x111C8)) == "Shrd"
    assert unicodedata.script(chr(0x1045F)) == "Shaw"
    assert unicodedata.script(chr(0x115AD)) == "Sidd"
    assert unicodedata.script(chr(0x1D8C0)) == "Sgnw"
    assert unicodedata.script(chr(0x0DB9)) == "Sinh"
    assert unicodedata.script(chr(0x110F9)) == "Sora"
    assert unicodedata.script(chr(0x11A60)) == "Soyo"
    assert unicodedata.script(chr(0x1B94)) == "Sund"
    assert unicodedata.script(chr(0xA81F)) == "Sylo"
    assert unicodedata.script(chr(0x0740)) == "Syrc"
    assert unicodedata.script(chr(0x1714)) == "Tglg"
    assert unicodedata.script(chr(0x1761)) == "Tagb"
    assert unicodedata.script(chr(0x1965)) == "Tale"
    assert unicodedata.script(chr(0x1A32)) == "Lana"
    assert unicodedata.script(chr(0xAA86)) == "Tavt"
    assert unicodedata.script(chr(0x116A5)) == "Takr"
    assert unicodedata.script(chr(0x0B8E)) == "Taml"
    assert unicodedata.script(chr(0x1754D)) == "Tang"
    assert unicodedata.script(chr(0x0C40)) == "Telu"
    assert unicodedata.script(chr(0x07A4)) == "Thaa"
    assert unicodedata.script(chr(0x0E42)) == "Thai"
    assert unicodedata.script(chr(0x0F09)) == "Tibt"
    assert unicodedata.script(chr(0x2D3A)) == "Tfng"
    assert unicodedata.script(chr(0x114B0)) == "Tirh"
    assert unicodedata.script(chr(0x1038B)) == "Ugar"
    assert unicodedata.script(chr(0xA585)) == "Vaii"
    assert unicodedata.script(chr(0x118CF)) == "Wara"
    assert unicodedata.script(chr(0xA066)) == "Yiii"
    assert unicodedata.script(chr(0x11A31)) == "Zanb"
    assert unicodedata.script(chr(0x11F00)) == "Kawi"


def test_script_extension():
    assert unicodedata.script_extension("a") == {"Latn"}
    assert unicodedata.script_extension(chr(0)) == {"Zyyy"}
    assert unicodedata.script_extension(chr(0x0378)) == {"Zzzz"}
    assert unicodedata.script_extension(chr(0x10FFFF)) == {"Zzzz"}

    assert unicodedata.script_extension("\u0660") == {"Arab", "Thaa", "Yezi"}
    assert unicodedata.script_extension("\u0964") == {
        "Beng",
        "Deva",
        "Dogr",
        "Gong",
        "Gonm",
        "Gran",
        "Gujr",
        "Guru",
        "Knda",
        "Mahj",
        "Mlym",
        "Nand",
        "Orya",
        "Sind",
        "Sinh",
        "Sylo",
        "Takr",
        "Taml",
        "Telu",
        "Tirh",
    }


def test_script_name():
    assert unicodedata.script_name("Latn") == "Latin"
    assert unicodedata.script_name("Zyyy") == "Common"
    assert unicodedata.script_name("Zzzz") == "Unknown"
    # underscores in long names are replaced by spaces
    assert unicodedata.script_name("Egyp") == "Egyptian Hieroglyphs"

    with pytest.raises(KeyError):
        unicodedata.script_name("QQQQ")
    assert unicodedata.script_name("QQQQ", default="Unknown")


def test_script_code():
    assert unicodedata.script_code("Latin") == "Latn"
    assert unicodedata.script_code("Common") == "Zyyy"
    assert unicodedata.script_code("Unknown") == "Zzzz"
    # case, whitespace, underscores and hyphens are ignored
    assert unicodedata.script_code("Egyptian Hieroglyphs") == "Egyp"
    assert unicodedata.script_code("Egyptian_Hieroglyphs") == "Egyp"
    assert unicodedata.script_code("egyptianhieroglyphs") == "Egyp"
    assert unicodedata.script_code("Egyptian-Hieroglyphs") == "Egyp"

    with pytest.raises(KeyError):
        unicodedata.script_code("Does not exist")
    assert unicodedata.script_code("Does not exist", default="Zzzz") == "Zzzz"


def test_block():
    assert unicodedata.block("\x00") == "Basic Latin"
    assert unicodedata.block("\x7F") == "Basic Latin"
    assert unicodedata.block("\x80") == "Latin-1 Supplement"
    assert unicodedata.block("\u1c90") == "Georgian Extended"
    assert unicodedata.block("\u0870") == "Arabic Extended-B"
    assert unicodedata.block("\U00011B00") == "Devanagari Extended-A"


def test_ot_tags_from_script():
    # simple
    assert unicodedata.ot_tags_from_script("Latn") == ["latn"]
    # script mapped to multiple new and old script tags
    assert unicodedata.ot_tags_from_script("Deva") == ["dev2", "deva"]
    # exceptions
    assert unicodedata.ot_tags_from_script("Hira") == ["kana"]
    assert unicodedata.ot_tags_from_script("Zmth") == ["math"]
    # special script codes map to DFLT
    assert unicodedata.ot_tags_from_script("Zinh") == ["DFLT"]
    assert unicodedata.ot_tags_from_script("Zyyy") == ["DFLT"]
    assert unicodedata.ot_tags_from_script("Zzzz") == ["DFLT"]
    # this is invalid or unknown
    assert unicodedata.ot_tags_from_script("Aaaa") == ["DFLT"]


def test_ot_tag_to_script():
    assert unicodedata.ot_tag_to_script("latn") == "Latn"
    assert unicodedata.ot_tag_to_script("kana") == "Kana"
    assert unicodedata.ot_tag_to_script("DFLT") == None
    assert unicodedata.ot_tag_to_script("aaaa") == None
    assert unicodedata.ot_tag_to_script("beng") == "Beng"
    assert unicodedata.ot_tag_to_script("bng2") == "Beng"
    assert unicodedata.ot_tag_to_script("dev2") == "Deva"
    assert unicodedata.ot_tag_to_script("gjr2") == "Gujr"
    assert unicodedata.ot_tag_to_script("yi  ") == "Yiii"
    assert unicodedata.ot_tag_to_script("nko ") == "Nkoo"
    assert unicodedata.ot_tag_to_script("vai ") == "Vaii"
    assert unicodedata.ot_tag_to_script("lao ") == "Laoo"
    assert unicodedata.ot_tag_to_script("yi") == "Yiii"
    assert unicodedata.ot_tag_to_script("math") == "Zmth"
    # both 'hang' and 'jamo' tags map to the Hangul script
    assert unicodedata.ot_tag_to_script("hang") == "Hang"
    assert unicodedata.ot_tag_to_script("jamo") == "Hang"

    for invalid_value in ("", " ", "z zz", "zzzzz"):
        with pytest.raises(ValueError, match="invalid OpenType tag"):
            unicodedata.ot_tag_to_script(invalid_value)


def test_script_horizontal_direction():
    assert unicodedata.script_horizontal_direction("Latn") == "LTR"
    assert unicodedata.script_horizontal_direction("Arab") == "RTL"
    assert unicodedata.script_horizontal_direction("Thaa") == "RTL"
    assert unicodedata.script_horizontal_direction("Ougr") == "RTL"

    with pytest.raises(KeyError):
        unicodedata.script_horizontal_direction("Azzz")
    assert unicodedata.script_horizontal_direction("Azzz", default="LTR") == "LTR"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
