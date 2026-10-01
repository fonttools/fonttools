import io
import copy
import pickle
import tempfile
import zlib
from types import SimpleNamespace
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib.sfnt import (
    calcChecksum,
    SFNTDirectoryEntry,
    SFNTReader,
    sfntDirectorySize,
    WOFFDirectoryEntry,
    WOFFFlavorData,
)
from pathlib import Path
import pytest

TEST_DATA = Path(__file__).parent / "data"


@pytest.fixture
def ttfont_path():
    font = TTFont()
    font.importXML(TEST_DATA / "TestTTF-Regular.ttx")
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as fp:
        font_path = Path(fp.name)
        font.save(font_path)
    yield font_path
    font_path.unlink()


def test_calcChecksum():
    assert calcChecksum(b"abcd") == 1633837924
    assert calcChecksum(b"abcdxyz") == 3655064932


EMPTY_SFNT = b"\x00\x01\x00\x00" + b"\x00" * 8


def pickle_unpickle(obj):
    return pickle.loads(pickle.dumps(obj))


class SFNTReaderTest:
    @pytest.mark.parametrize("deepcopy", [copy.deepcopy, pickle_unpickle])
    def test_pickle_protocol_FileIO(self, deepcopy, tmp_path):
        fontfile = tmp_path / "test.ttf"
        fontfile.write_bytes(EMPTY_SFNT)
        reader = SFNTReader(fontfile.open("rb"))

        reader2 = deepcopy(reader)

        assert reader2 is not reader
        assert reader2.file is not reader.file

        assert isinstance(reader2.file, io.BufferedReader)
        assert isinstance(reader2.file.raw, io.FileIO)
        assert reader2.file.name == reader.file.name
        assert reader2.file.tell() == reader.file.tell()

        for k, v in reader.__dict__.items():
            if k == "file":
                continue
            assert getattr(reader2, k) == v

    @pytest.mark.parametrize("deepcopy", [copy.deepcopy, pickle_unpickle])
    def test_pickle_protocol_BytesIO(self, deepcopy, tmp_path):
        buf = io.BytesIO(EMPTY_SFNT)
        reader = SFNTReader(buf)

        reader2 = deepcopy(reader)

        assert reader2 is not reader
        assert reader2.file is not reader.file

        assert isinstance(reader2.file, io.BytesIO)
        assert reader2.file.tell() == reader.file.tell()
        assert reader2.file.getvalue() == reader.file.getvalue()

        for k, v in reader.__dict__.items():
            if k == "file":
                continue
            assert getattr(reader2, k) == v


def test_loadData_truncated_raises_TTLibError():
    # A corrupt table directory entry whose length runs past the end of the
    # file must raise TTLibError, not a bare AssertionError (which is also
    # silently skipped under `python -O`).
    entry = SFNTDirectoryEntry()
    entry.tag = "test"
    entry.offset = 0
    entry.length = 1000  # more than the stream holds
    with pytest.raises(TTLibError, match="unexpected end of 'test' table data"):
        entry.loadData(io.BytesIO(b"short"))


def test_load_truncated_font_raises_TTLibError(ttfont_path):
    # End-to-end: a font file cut short past its last table directory entry
    # must fail with TTLibError when that table is loaded. Chop 4 bytes so we
    # land inside the last table regardless of its 4-byte padding.
    data = ttfont_path.read_bytes()[:-4]
    font = TTFont(io.BytesIO(data), lazy=True)
    with pytest.raises(TTLibError, match=r"unexpected end of '\w{4}' table data"):
        for tag in font.keys():
            font[tag]


def test_truncated_table_directory_raises_TTLibError(ttfont_path):
    # Keep the complete sfnt header but only half of its first table-directory
    # entry. The short entry must raise TTLibError rather than struct.error.
    data = ttfont_path.read_bytes()[
        : sfntDirectorySize + SFNTDirectoryEntry.formatSize // 2
    ]
    with pytest.raises(TTLibError, match="unexpected end of table directory"):
        TTFont(io.BytesIO(data))


def test_bogus_numTables_raises_TTLibError(ttfont_path):
    # Corrupting numTables makes the directory run past the end of the file.
    data = bytearray(ttfont_path.read_bytes())
    data[5] ^= 0xFF
    with pytest.raises(TTLibError, match="unexpected end of table directory"):
        TTFont(io.BytesIO(bytes(data)))


# The WOFF decode path validated its (untrusted) sizes with bare assertions,
# which raise the wrong exception and, under `python -O`, are dropped entirely,
# so a corrupt WOFF was accepted with wrong-sized data. These mirror the
# truncated-table-directory tests above for the WOFF-specific sites.


def test_woff_table_bad_compressed_length_raises_TTLibError():
    entry = WOFFDirectoryEntry()
    entry.tag = "test"
    # A compressed table must be smaller than its original size.
    entry.length = 20
    entry.origLength = 10
    with pytest.raises(TTLibError, match="corrupt WOFF table 'test'"):
        entry.decodeData(zlib.compress(b"A" * 10))


def test_woff_table_decompressed_size_mismatch_raises_TTLibError():
    payload = b"A" * 100
    rawData = zlib.compress(payload)
    entry = WOFFDirectoryEntry()
    entry.tag = "test"
    entry.length = len(rawData)
    entry.origLength = len(payload) + 5  # lie about the original size
    assert entry.length < entry.origLength
    with pytest.raises(
        TTLibError, match="unexpected size for decompressed WOFF table 'test'"
    ):
        entry.decodeData(rawData)


def _woff_flavor_reader(**kwargs):
    attrs = dict(
        majorVersion=1,
        minorVersion=0,
        metaOffset=0,
        metaLength=0,
        metaOrigLength=0,
        privOffset=0,
        privLength=0,
        file=io.BytesIO(b""),
    )
    attrs.update(kwargs)
    return SimpleNamespace(**attrs)


def test_woff_metadata_truncated_raises_TTLibError():
    reader = _woff_flavor_reader(metaLength=100, file=io.BytesIO(b"short"))
    with pytest.raises(TTLibError, match="unexpected end of WOFF metadata"):
        WOFFFlavorData(reader)


def test_woff_metadata_size_mismatch_raises_TTLibError():
    meta = b"<metadata/>"
    compressed = zlib.compress(meta)
    reader = _woff_flavor_reader(
        metaLength=len(compressed),
        metaOrigLength=len(meta) + 3,  # lie about the uncompressed size
        file=io.BytesIO(compressed),
    )
    with pytest.raises(
        TTLibError, match="unexpected size for decompressed WOFF metadata"
    ):
        WOFFFlavorData(reader)


def test_woff_privData_truncated_raises_TTLibError():
    reader = _woff_flavor_reader(privLength=100, file=io.BytesIO(b"short"))
    with pytest.raises(TTLibError, match="unexpected end of WOFF private data"):
        WOFFFlavorData(reader)


def test_ttLib_sfnt_write_privData(tmp_path, ttfont_path):
    output_path = tmp_path / "TestTTF-Regular.woff"
    font = TTFont(ttfont_path)

    privData = "Private Eyes".encode()

    data = WOFFFlavorData()
    head = font["head"]
    data.majorVersion, data.minorVersion = map(
        int, format(head.fontRevision, ".3f").split(".")
    )

    data.privData = privData
    font.flavor = "woff"
    font.flavorData = data
    font.save(output_path)

    assert output_path.exists()
    assert TTFont(output_path).flavorData.privData == privData
