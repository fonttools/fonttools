import io
import os
import re
import random
import tempfile
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import (
    TTFont,
    TTLibError,
    newTable,
    registerCustomTableClass,
    unregisterCustomTableClass,
)
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
import pytest


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")


class CustomTableClass(DefaultTable):
    def decompile(self, data, ttFont):
        self.numbers = list(data)

    def compile(self, ttFont):
        return bytes(self.numbers)

    # not testing XML read/write


table_C_U_S_T_ = CustomTableClass  # alias for testing


TABLETAG = "CUST"


def normalize_TTX(string):
    string = re.sub(' ttLibVersion=".*"', "", string)
    string = re.sub('checkSumAdjustment value=".*"', "", string)
    string = re.sub('modified value=".*"', "", string)
    return string


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


ttxTTF = r"""<?xml version="1.0" encoding="UTF-8"?>
<ttFont sfntVersion="\x00\x01\x00\x00" ttLibVersion="4.9.0">
  <hmtx>
    <mtx name=".notdef" width="300" lsb="0"/>
  </hmtx>
</ttFont>
"""


ttxOTF = """<?xml version="1.0" encoding="UTF-8"?>
<ttFont sfntVersion="OTTO" ttLibVersion="4.9.0">
  <hmtx>
    <mtx name=".notdef" width="300" lsb="0"/>
  </hmtx>
</ttFont>
"""


def test_sfntVersionFromTTX():
    # https://github.com/fonttools/fonttools/issues/2370
    font = TTFont()
    assert font.sfntVersion == "\x00\x01\x00\x00"
    ttx = io.StringIO(ttxOTF)
    # Font is "empty", TTX file will determine sfntVersion
    font.importXML(ttx)
    assert font.sfntVersion == "OTTO"
    ttx = io.StringIO(ttxTTF)
    # Font is not "empty", sfntVersion in TTX file will be ignored
    font.importXML(ttx)
    assert font.sfntVersion == "OTTO"


def test_virtualGlyphId():
    otfpath = os.path.join(DATA_DIR, "TestVGID-Regular.otf")
    ttxpath = os.path.join(DATA_DIR, "TestVGID-Regular.ttx")

    otf = TTFont(otfpath)

    ttx = TTFont()
    ttx.importXML(ttxpath)

    with open(ttxpath, encoding="utf-8") as fp:
        xml = normalize_TTX(fp.read()).splitlines()

    for font in (otf, ttx):
        GSUB = font["GSUB"].table
        assert GSUB.LookupList.LookupCount == 37
        lookup = GSUB.LookupList.Lookup[32]
        assert lookup.LookupType == 8
        subtable = lookup.SubTable[0]
        assert subtable.LookAheadGlyphCount == 1
        lookahead = subtable.LookAheadCoverage[0]
        assert len(lookahead.glyphs) == 46
        assert "glyph00453" in lookahead.glyphs

        out = io.StringIO()
        font.saveXML(out)
        outxml = normalize_TTX(out.getvalue()).splitlines()
        assert xml == outxml


def test_setGlyphOrder_also_updates_glyf_glyphOrder():
    # https://github.com/fonttools/fonttools/issues/2060#issuecomment-1063932428
    font = TTFont()
    font.importXML(os.path.join(DATA_DIR, "TestTTF-Regular.ttx"))
    current_order = font.getGlyphOrder()

    assert current_order == font["glyf"].glyphOrder

    new_order = list(current_order)
    while new_order == current_order:
        random.shuffle(new_order)

    font.setGlyphOrder(new_order)

    assert font.getGlyphOrder() == new_order
    assert font["glyf"].glyphOrder == new_order


def test_getGlyphOrder_not_true_post_format_1(caplog):
    # https://github.com/fonttools/fonttools/issues/2736
    caplog.set_level("WARNING")
    font = TTFont(os.path.join(DATA_DIR, "bogus_post_format_1.ttf"))
    hmtx = font["hmtx"]
    assert len(hmtx.metrics) > len(standardGlyphOrder)
    log_rec = caplog.records[-1]
    assert log_rec.levelname == "WARNING"
    assert "Not enough names found in the 'post' table" in log_rec.message


@pytest.mark.parametrize("lazy", [None, True, False])
def test_ensureDecompiled(lazy):
    # test that no matter the lazy value, ensureDecompiled decompiles all tables
    font = TTFont()
    font.importXML(os.path.join(DATA_DIR, "TestTTF-Regular.ttx"))
    # test font has no OTL so we add some, as an example of otData-driven tables
    addOpenTypeFeaturesFromString(
        font,
        """
        feature calt {
            sub period' period' period' space by ellipsis;
        } calt;

        feature dist {
            pos period period -30;
        } dist;
        """,
    )
    # also add an additional cmap subtable that will be lazily-loaded
    cm = CmapSubtable.newSubtable(14)
    cm.platformID = 0
    cm.platEncID = 5
    cm.language = 0
    cm.cmap = {}
    cm.uvsDict = {0xFE00: [(0x002E, None)]}
    font["cmap"].tables.append(cm)

    # save and reload, potentially lazily
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    font = TTFont(buf, lazy=lazy)

    # check no table is loaded until/unless requested, no matter the laziness
    for tag in font.keys():
        assert not font.isLoaded(tag)

    if lazy is not False:
        # additional cmap doesn't get decompiled automatically unless lazy=False;
        # can't use hasattr or else cmap's maginc __getattr__ kicks in...
        cm = next(st for st in font["cmap"].tables if st.__dict__["format"] == 14)
        assert cm.data is not None
        assert "uvsDict" not in cm.__dict__
        # glyf glyphs are not expanded unless lazy=False
        assert font["glyf"].glyphs["period"].data is not None
        assert not hasattr(font["glyf"].glyphs["period"], "coordinates")

    if lazy is True:
        # OTL tables hold a 'reader' to lazily load when lazy=True
        assert "reader" in font["GSUB"].table.LookupList.__dict__
        assert "reader" in font["GPOS"].table.LookupList.__dict__

    font.ensureDecompiled()

    # all tables are decompiled now
    for tag in font.keys():
        assert font.isLoaded(tag)
    # including the additional cmap
    cm = next(st for st in font["cmap"].tables if st.__dict__["format"] == 14)
    assert cm.data is None
    assert "uvsDict" in cm.__dict__
    # expanded glyf glyphs lost the 'data' attribute
    assert not hasattr(font["glyf"].glyphs["period"], "data")
    assert hasattr(font["glyf"].glyphs["period"], "coordinates")
    # and OTL tables have read their 'reader'
    assert "reader" not in font["GSUB"].table.LookupList.__dict__
    assert "Lookup" in font["GSUB"].table.LookupList.__dict__
    assert "reader" not in font["GPOS"].table.LookupList.__dict__
    assert "Lookup" in font["GPOS"].table.LookupList.__dict__


@pytest.fixture
def testFont_fvar_avar():
    ttxpath = os.path.join(DATA_DIR, "TestTTF_normalizeLocation.ttx")
    ttf = TTFont()
    ttf.importXML(ttxpath)
    return ttf


@pytest.mark.parametrize(
    "userLocation, expectedNormalizedLocation",
    [
        ({}, {"wght": 0.0}),
        ({"wght": 100}, {"wght": -1.0}),
        ({"wght": 250}, {"wght": -0.75}),
        ({"wght": 400}, {"wght": 0.0}),
        ({"wght": 550}, {"wght": 0.75}),
        ({"wght": 625}, {"wght": 0.875}),
        ({"wght": 700}, {"wght": 1.0}),
    ],
)
def test_font_normalizeLocation(
    testFont_fvar_avar, userLocation, expectedNormalizedLocation
):
    normalizedLocation = testFont_fvar_avar.normalizeLocation(userLocation)
    assert expectedNormalizedLocation == normalizedLocation


def test_font_normalizeLocation_no_VF():
    ttf = TTFont()
    with pytest.raises(TTLibError, match="Not a variable font"):
        ttf.normalizeLocation({})


def test_getGlyphID():
    font = TTFont()
    font.importXML(os.path.join(DATA_DIR, "TestTTF-Regular.ttx"))

    assert font.getGlyphID("space") == 3
    assert font.getGlyphID("glyph12345") == 12345  # virtual glyph
    with pytest.raises(KeyError):
        font.getGlyphID("non_existent")
    with pytest.raises(KeyError):
        font.getGlyphID("glyph_prefix_but_invalid_id")


def test_spooled_tempfile_may_not_have_attribute_seekable():
    # SpooledTemporaryFile only got a seekable attribute on Python 3.11
    # https://github.com/fonttools/fonttools/issues/3052
    font = TTFont()
    font.importXML(os.path.join(DATA_DIR, "TestTTF-Regular.ttx"))
    tmp = tempfile.SpooledTemporaryFile()
    font.save(tmp)
    # this should not fail
    _ = TTFont(tmp)


def test_unseekable_file_lazy_loading_fails():
    class NonSeekableFile:
        def __init__(self):
            self.file = io.BytesIO()

        def read(self, size):
            return self.file.read(size)

        def seekable(self):
            return False

    f = NonSeekableFile()
    with pytest.raises(TTLibError, match="Input file must be seekable when lazy=True"):
        TTFont(f, lazy=True)


def test_unsupported_seek_operation_lazy_loading_fails():
    class UnsupportedSeekFile:
        def __init__(self):
            self.file = io.BytesIO()

        def read(self, size):
            return self.file.read(size)

        def seek(self, offset):
            raise io.UnsupportedOperation("Unsupported seek operation")

    f = UnsupportedSeekFile()
    with pytest.raises(TTLibError, match="Input file must be seekable when lazy=True"):
        TTFont(f, lazy=True)
