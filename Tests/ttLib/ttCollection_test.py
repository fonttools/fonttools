import os
from io import BytesIO
from itertools import count
from pathlib import Path

import pytest
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import TTCollection
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


def test_save_ttc_v2_dsig(lazy):
    # save() should write a V2 TTC if there's a TTCollection.dsig
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    ttc = TTCollection(ttc_path, lazy=lazy)
    ttc.dsig = table_D_S_I_G_("DSIG")

    # Make a minimal valid DSIG with no signature records
    ttc.dsig.ulVersion = 1
    ttc.dsig.usNumSigs = 0
    ttc.dsig.usFlag = 0
    ttc.dsig.signatureRecords = []

    buf = BytesIO()
    ttc.save(buf)
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


def test_save_ttc_v2_dsig_none(lazy):
    # save() should write a V2 TTC if there's a TTCollection.dsig == None
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    ttc = TTCollection(ttc_path, lazy=lazy)
    ttc.dsig = None

    buf = BytesIO()
    ttc.save(buf)
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
        assert hasattr(collection, "dsig")
        assert collection.dsig is None


def test_save_ttc_v2_dsig_invalid(lazy):
    # save() should raise if there's a TTCollection.dsig that can't be compiled
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    ttc = TTCollection(ttc_path, lazy=lazy)
    ttc.dsig = table_D_S_I_G_("DSIG")

    # The required fields in the DSIG are not set, so compilation will fail
    with pytest.raises(KeyError):
        buf = BytesIO()
        ttc.save(buf)


def test_roundtrip_ttc_dsig(lazy):
    # The DSIG should persist when not explicitly decompiling it
    ttc_path = TTX_DATA_DIR / "TestTTCv2.ttc"
    with TTCollection(ttc_path, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
        assert hasattr(collection, "dsig")
        buf = BytesIO()
        collection.save(buf)
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

    # Last 8 bytes of the file should contain the DSIG table
    buf.seek(-8, 2)
    data = buf.read(8)
    assert data == deHexStr(
        "00 00 00 01"  # DSIG table version
        "00 00 00 00"  # numSignatures, flags
    )


def test_save_ttc_deterministic_across_clock_tick(monkeypatch):
    # With recalcTimestamp on (the default), each font restamps its 'head' from
    # timestampNow(); save() must pin a single timestamp across the collection so
    # the 'head' tables stay byte-identical and shared. Otherwise a wall-clock
    # tick between the two fonts' head.compile() calls gives them different
    # 'modified' values, defeating table sharing and adding a whole head table
    # (a non-deterministic, flaky file size). See
    # https://github.com/fonttools/fonttools/issues/4110
    import fontTools.ttLib.tables._h_e_a_d as head_mod

    ttc_path = TTX_DATA_DIR / "TestTTCv2.ttc"

    def save_bytes(clock):
        monkeypatch.setattr(head_mod, "timestampNow", clock)
        ttc = TTCollection(ttc_path, lazy=False)
        buf = BytesIO()
        ttc.save(buf)
        ttc.close()
        return buf.getvalue()

    steady = save_bytes(lambda: 1000)  # clock never advances
    ticks = count(1)
    ticking = save_bytes(lambda: next(ticks) * 86400)  # advances on every call

    # A clock tick must not change the output: the shared 'head' is written once.
    assert len(ticking) == len(steady)
    with TTCollection(BytesIO(ticking), lazy=False) as ttc:
        assert ttc[0]["head"].modified == ttc[1]["head"].modified


def test_roundtrip_ttc_dsig_decompile(lazy):
    # The DSIG should persist when decompiling it
    ttc_path = TTX_DATA_DIR / "TestTTCv2.ttc"
    with TTCollection(ttc_path, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
        assert hasattr(collection, "dsig")
        collection.dsig.decompile(collection.dsig.data, None)
        buf = BytesIO()
        collection.save(buf)
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

    # Last 8 bytes of the file should contain the DSIG table
    buf.seek(-8, 2)
    data = buf.read(8)
    assert data == deHexStr(
        "00 00 00 01"  # DSIG table version
        "00 00 00 00"  # numSignatures, flags
    )
