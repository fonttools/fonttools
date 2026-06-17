import os
from io import BytesIO
from pathlib import Path
from fontTools.ttLib import TTCollection
import pytest
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib.tables.D_S_I_G_ import table_D_S_I_G_

TTX_DATA_DIR = Path(__file__).parent.parent / "ttx" / "data"


@pytest.fixture(params=[None, True, False])
def lazy(request):
    return request.param


def test_lazy_open_path(lazy):
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    with TTCollection(ttc_path, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6


def test_lazy_open_file(lazy):
    with (TTX_DATA_DIR / "TestTTC.ttc").open("rb") as file:
        collection = TTCollection(file, lazy=lazy)
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6


def test_save_ttc_v2_empty_dsig(lazy):
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    ttc = TTCollection(ttc_path, lazy=lazy)
    # An empty dsig will only result in three 0 fields added to the TTC header after the
    # font offsets
    ttc.dsig = table_D_S_I_G_("DSIG")
    buf = BytesIO()
    ttc.save(buf, version=0x00020000)
    ttc.close()
    buf.seek(0)
    data = buf.read(32)
    assert data == deHexStr(
        "74 74 63 66"  # ttfc
        "00 02 00 00"  # ttc version 2
        "00 00 00 02"  # number of fonts
        "00 00 00 20"  # font 0 offset
        "00 00 09 40"  # font 1 offset
        "00 00 00 00"  # ulDsigTag
        "00 00 00 00"  # ulDsigLength
        "00 00 00 00"  # ulDsigOffset
    )

    # Last 8 bytes of the file should be identical to the original
    buf.seek(-8, 2)
    data = buf.read(8)
    assert data == deHexStr("00 00 04 88 00 00 00 01")

    # Read the collection again and check for DSIG
    buf.seek(0)
    with TTCollection(buf, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
        # The DSIG fields were empty, the attribute should not exist
        assert not hasattr(collection, "dsig")


def test_save_ttc_v2_dsig(lazy):
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    ttc = TTCollection(ttc_path, lazy=lazy)
    ttc.dsig = table_D_S_I_G_("DSIG")

    # Make a minimal valid DSIG with no signature records
    ttc.dsig.ulVersion = 1
    ttc.dsig.usNumSigs = 0
    ttc.dsig.usFlag = 0
    ttc.dsig.signatureRecords = []

    buf = BytesIO()
    ttc.save(buf, version=0x00020000)
    ttc.close()
    buf.seek(0)
    data = buf.read(32)
    assert data == deHexStr(
        "74 74 63 66"  # ttfc
        "00 02 00 00"  # ttc version 2
        "00 00 00 02"  # number of fonts
        "00 00 00 20"  # font 0 offset
        "00 00 09 40"  # font 1 offset
        "44 53 49 47"  # ulDsigTag
        "00 00 00 08"  # ulDsigLength
        "00 00 0A 3C"  # ulDsigOffset
    )

    # Last 8 bytes of the file should contain the DSIG table
    buf.seek(-8, 2)
    data = buf.read(8)
    assert data == deHexStr(
        "00 00 00 01"  # DSIG table version
        "00 00 00 00"  # numSignatures, flags
    )

    # Read the collection again and check for DSIG
    buf.seek(0)
    with TTCollection(buf, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
        assert isinstance(collection.dsig, table_D_S_I_G_)
        collection.dsig.decompile(collection.dsig.data, None)
        assert collection.dsig.ulVersion == 1
        assert collection.dsig.usNumSigs == 0
        assert collection.dsig.usFlag == 0


def test_roundtrip_ttc_v2_dsig(lazy):
    # Check if the DSIG persists when not explicitly decompiling it
    ttc_path = TTX_DATA_DIR / "TestTTCv2.ttc"
    with TTCollection(ttc_path, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
        assert hasattr(collection, "dsig")
        buf = BytesIO()
        collection.save(buf, version=0x00020000)
    buf.seek(0)
    data = buf.read(32)
    assert data == deHexStr(
        "74 74 63 66"  # ttfc
        "00 02 00 00"  # ttc version 2
        "00 00 00 02"  # number of fonts
        "00 00 00 20"  # font 0 offset
        "00 00 09 3C"  # font 1 offset
        "44 53 49 47"  # ulDsigTag
        "00 00 00 08"  # ulDsigLength
        "00 00 0A 38"  # ulDsigOffset
    )
