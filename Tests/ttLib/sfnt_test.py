from contextlib import contextmanager
import io
import copy
import pickle
import struct
import tempfile
import zlib

try:
    import tracemalloc
except ImportError:
    tracemalloc = None
from types import SimpleNamespace
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib import sfnt
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


def _zlib_zeros(size):
    co = zlib.compressobj(9)
    chunk = b"\x00" * (1024 * 1024)
    parts = []
    remaining = size
    while remaining > 0:
        n = min(len(chunk), remaining)
        parts.append(co.compress(chunk[:n]))
        remaining -= n
    parts.append(co.flush())
    return b"".join(parts)


def _make_woff1(entries, body, meta_offset=0, meta_length=0, meta_orig_length=0):
    header_size = 44
    dir_size = 20 * len(entries)
    total_len = header_size + dir_size + len(body)
    total_sfnt = min(12 + 16 * len(entries) + sum(e[3] for e in entries), 0xFFFFFFFF)
    header = struct.pack(
        ">4s4sIHHIHHIIIII",
        b"wOFF",
        b"\x00\x01\x00\x00",
        total_len,
        len(entries),
        0,
        total_sfnt,
        1,
        0,
        meta_offset,
        meta_length,
        meta_orig_length,
        0,
        0,
    )
    directory = b"".join(struct.pack(">4sIIII", *e) for e in entries)
    return header + directory + body


@contextmanager
def _assert_peak_memory_below(limit):
    if tracemalloc is None:
        yield
        return
    tracemalloc.start()
    try:
        yield
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < limit


def test_woff_table_decompression_bomb_lying_header():
    # A 20 MiB zlib stream whose directory entry claims origLength=100 KiB
    # (length < origLength < actual) must abort via bounded decompression
    # rather than materialising the 20 MiB stream.
    bomb = _zlib_zeros(20 * 1024 * 1024)
    entry = WOFFDirectoryEntry()
    entry.tag = "glyf"
    entry.length = len(bomb)
    entry.origLength = 100_000
    assert entry.length < entry.origLength

    with _assert_peak_memory_below(2 * 1024 * 1024):
        with pytest.raises(
            TTLibError,
            match="unexpected size for decompressed WOFF table 'glyf': exceeds expected",
        ):
            entry.decodeData(bomb)


def test_woff_table_decompression_bomb_declared_limits():
    # Excess compression ratio (20 KiB -> 20 MiB = ~1000x > 100x) rejected
    # before zlib runs, both on direct decodeData and at SFNTReader open.
    bomb = _zlib_zeros(20 * 1024 * 1024)
    entry = WOFFDirectoryEntry()
    entry.tag = "glyf"
    entry.length = len(bomb)
    entry.origLength = 20 * 1024 * 1024
    with pytest.raises(TTLibError, match="exceeds maximum compression ratio"):
        entry.decodeData(bomb)

    woff_ratio = _make_woff1([(b"glyf", 64, len(bomb), 20 * 1024 * 1024, 0)], bomb)
    with pytest.raises(TTLibError, match="exceeds maximum compression ratio"):
        SFNTReader(io.BytesIO(woff_ratio))

    # Excess absolute size (> WOFF_MAX_DECOMPRESSED_SIZE) rejected even if
    # compression ratio would otherwise be plausible.
    huge = sfnt.WOFF_MAX_DECOMPRESSED_SIZE + 1
    entry.origLength = huge
    with pytest.raises(TTLibError, match="exceeds maximum allowed size"):
        entry.decodeData(bomb)

    # Overlapping table offsets: 50 tables pointing to the same ~40 KiB blob,
    # each with a modest 50x per-table ratio, totaling 100 MiB (> 100x file size).
    payload = bytes(range(256)) * 150 + b"\x00" * (2 * 1024 * 1024 - 256 * 150)
    chunk = zlib.compress(payload, 9)
    n_tables = 50
    data_off = 44 + 20 * n_tables
    entries = [
        (f"t{i:03d}".encode(), data_off, len(chunk), 2 * 1024 * 1024, 0)
        for i in range(n_tables)
    ]
    woff_overlap = _make_woff1(entries, chunk)
    with pytest.raises(TTLibError, match="exceeds maximum compression ratio"):
        SFNTReader(io.BytesIO(woff_overlap))


@pytest.mark.parametrize("declared_orig", [0, 100])
def test_woff_metadata_decompression_bomb_lying_header(declared_orig):
    # Specifically guards against zlib's max_length=0 meaning unbounded as well
    # as small declared metaOrigLength values.
    bomb = _zlib_zeros(20 * 1024 * 1024)
    reader = _woff_flavor_reader(
        metaOffset=0,
        metaLength=len(bomb),
        metaOrigLength=declared_orig,
        file=io.BytesIO(bomb),
    )
    with _assert_peak_memory_below(2 * 1024 * 1024):
        with pytest.raises(
            TTLibError,
            match="unexpected size for decompressed WOFF metadata: exceeds expected",
        ):
            WOFFFlavorData(reader)


def test_woff_metadata_decompression_bomb_declared_limits():
    bomb = _zlib_zeros(20 * 1024 * 1024)
    reader = _woff_flavor_reader(
        metaOffset=0,
        metaLength=len(bomb),
        metaOrigLength=20 * 1024 * 1024,
        file=io.BytesIO(bomb),
    )
    with pytest.raises(TTLibError, match="exceeds maximum allowed size"):
        WOFFFlavorData(reader)

    # Under WOFF_MAX_METADATA_SIZE (e.g. 5 MiB) but > 100x compression ratio
    bomb_5m = _zlib_zeros(5 * 1024 * 1024)
    reader_ratio = _woff_flavor_reader(
        metaOffset=0,
        metaLength=len(bomb_5m),
        metaOrigLength=5 * 1024 * 1024,
        file=io.BytesIO(bomb_5m),
    )
    with pytest.raises(TTLibError, match="exceeds maximum compression ratio"):
        WOFFFlavorData(reader_ratio)


def test_woff_truncated_zlib_stream_raises_TTLibError():
    payload = b"A" * 100
    truncated = zlib.compress(payload)[:-2]  # drop Adler-32 tail
    entry = WOFFDirectoryEntry()
    entry.tag = "test"
    entry.length = len(truncated)
    entry.origLength = len(payload)
    with pytest.raises(TTLibError, match="unexpected end of compressed WOFF table"):
        entry.decodeData(truncated)


def test_loadData_huge_length_on_real_file_does_not_preallocate(tmp_path):
    # CPython BufferedReader.read(0xFFFFFFFF) pre-allocates 4 GiB even on a
    # 5-byte file; bounded chunked reads cap allocation to _READ_CHUNK_SIZE.
    small = tmp_path / "small.bin"
    small.write_bytes(b"short")
    entry = SFNTDirectoryEntry()
    entry.tag = "test"
    entry.offset = 0
    entry.length = 0xFFFFFFFF

    with _assert_peak_memory_below(2 * 1024 * 1024):
        with small.open("rb") as f:
            with pytest.raises(TTLibError, match="unexpected end of 'test' table data"):
                entry.loadData(f)
            reader = _woff_flavor_reader(
                metaLength=0xFFFFFFFF, metaOrigLength=10, file=f
            )
            with pytest.raises(TTLibError, match="unexpected end of WOFF metadata"):
                WOFFFlavorData(reader)
            reader_priv = _woff_flavor_reader(privLength=0xFFFFFFFF, file=f)
            with pytest.raises(TTLibError, match="unexpected end of WOFF private data"):
                WOFFFlavorData(reader_priv)


def test_woff_metadata_limit_none_disables_cap(monkeypatch):
    # Setting WOFF_MAX_METADATA_SIZE = None must disable the metadata size cap
    # rather than silently falling back to WOFF_MAX_DECOMPRESSED_SIZE.
    monkeypatch.setattr(sfnt, "WOFF_MAX_METADATA_SIZE", None)
    monkeypatch.setattr(sfnt, "WOFF_MAX_DECOMPRESSED_SIZE", 10)
    monkeypatch.setattr(sfnt, "WOFF_MAX_COMPRESSION_RATIO", None)
    meta = b"<metadata>0123456789abcdef</metadata>"
    compressed = zlib.compress(meta)
    reader = _woff_flavor_reader(
        metaOffset=0,
        metaLength=len(compressed),
        metaOrigLength=len(meta),
        file=io.BytesIO(compressed),
    )
    assert WOFFFlavorData(reader).metaData == meta


def test_load_lazy_without_seek_end(ttfont_path, monkeypatch):
    # Custom seekable streams that only support SEEK_SET (raising
    # UnsupportedOperation on SEEK_END) must work for lazy SFNT loads, read
    # multi-chunk tables accurately, and never receive huge single read() calls.
    raw = ttfont_path.read_bytes()

    class SeekSetOnlyFile:
        def __init__(self, data):
            self._buf = io.BytesIO(data)
            self.max_read = 0

        def read(self, n=-1):
            self.max_read = max(self.max_read, n)
            return self._buf.read(n)

        def tell(self):
            return self._buf.tell()

        def seekable(self):
            return True

        def seek(self, offset, whence=0):
            if whence != 0:
                raise io.UnsupportedOperation("SEEK_END not supported")
            return self._buf.seek(offset, 0)

    monkeypatch.setattr(sfnt, "_READ_CHUNK_SIZE", 64)
    stream = SeekSetOnlyFile(raw)
    font = TTFont(stream, lazy=True)
    assert font["head"].magicNumber == 0x5F0F3CF5
    assert font["glyf"] is not None
    assert stream.max_read <= 64

    trunc = SeekSetOnlyFile(b"short")
    entry = SFNTDirectoryEntry()
    entry.tag = "test"
    entry.offset = 0
    entry.length = 0xFFFFFFFF
    with pytest.raises(TTLibError, match="unexpected end of 'test' table data"):
        entry.loadData(trunc)
    assert trunc.max_read <= 64
