import struct

import pytest

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import C_B_D_T_, E_B_D_T_
from fontTools.ttLib.tables.E_B_D_T_ import _extFileName, _writeExtFileImageData


class _Writer:
    def __init__(self, name):
        self.file = type("_File", (), {"name": name})()

    def simpletag(self, tag, **kwargs):
        pass

    def newline(self):
        pass


class _Bitmap:
    fileExtension = ".bin"
    imageData = b"\xde\xad\xbe\xef"


def _export(tmp_path, glyphName, data=b"\xde\xad\xbe\xef"):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    writer = _Writer(str(out / "font.ttx"))
    bitmap = _Bitmap()
    bitmap.imageData = data
    _writeExtFileImageData(0, glyphName, bitmap, writer, None)
    return out / "bitmaps" / "strike0"


def test_extfile_export_contains_crafted_glyph_name(tmp_path):
    # A font can name a glyph with path separators (e.g. via a crafted 'post'
    # table); the "extfile" bitmap export must keep the file inside the folder.
    strike = _export(tmp_path, "../../../pwned")

    assert not (tmp_path / "pwned.bin").exists()
    (written,) = list(strike.iterdir())
    assert written.read_bytes() == b"\xde\xad\xbe\xef"


def test_extfile_export_plain_names_are_unchanged(tmp_path):
    # ordinary glyph names must keep their filename, or existing exports change
    strike = _export(tmp_path, "uni0041")

    assert (strike / "uni0041.bin").exists()


@pytest.mark.parametrize(
    "first, second",
    [
        ("a/b", "b"),  # a name that collides once its directory part is dropped
        ("../b", "b"),
        ("x/", "y/"),  # names whose final component is empty
        (".", ".."),
        # a plain name spelled like the escaped form of another name: the
        # escaping has to be injective, not merely separator-free
        ("a/b", _extFileName("a/b")),
        ("%2Fb", "/b"),
        ("%", ""),
    ],
)
def test_extfile_export_distinct_names_dont_collide(tmp_path, first, second):
    # dropping the directory part alone would map both onto the same file, so
    # the second export would silently overwrite the first
    _export(tmp_path, first, b"FIRST")
    strike = _export(tmp_path, second, b"SECOND")

    written = sorted(p.read_bytes() for p in strike.iterdir())
    assert written == [b"FIRST", b"SECOND"]


def test_extfile_name_mapping_is_injective():
    # every distinct glyph name must get a distinct filename, or one export
    # silently overwrites another
    names = [
        "a",
        "b",
        "uni0041",
        "a.alt",
        "%",
        "%25",
        "%2Fb",
        "/b",
        "a/b",
        "../b",
        "..",
        ".",
        "",
        "x/",
        "y/",
        "a\\b",
        "\u00e9",
        _extFileName("a/b"),
        _extFileName(""),
        _extFileName(".."),
    ]
    mapped = [_extFileName(n) for n in names]

    assert len(set(mapped)) == len(set(names))
    assert all("/" not in m and "\\" not in m for m in mapped)
    assert all(m not in ("", ".", "..") for m in mapped)


@pytest.fixture(params=[1, 2, 6, 7, 8, 9, 17, 18])
def bitmap_glyph(request):
    image_format = request.param
    if image_format in (1, 2, 8, 17):
        header = struct.pack(">BBbbB", 1, 8, -1, 1, 9)
        metrics = dict(height=1, width=8, BearingX=-1, BearingY=1, Advance=9)
    else:
        header = struct.pack(">BBbbBbbB", 1, 8, -1, 1, 9, -4, 2, 10)
        metrics = dict(
            height=1,
            width=8,
            horiBearingX=-1,
            horiBearingY=1,
            horiAdvance=9,
            vertBearingX=-4,
            vertBearingY=2,
            vertAdvance=10,
        )
    font = TTFont()
    font.setGlyphOrder([".notdef", "A"])
    if image_format in (8, 9):
        payload = struct.pack(">HHbb", 1, 1, -2, 3)
        if image_format == 8:
            payload = b"\0" + payload
    elif image_format in (17, 18):
        # CBDT stores the image as opaque bytes with a length prefix.
        payload = struct.pack(">L", 1) + b"\x81"
    else:
        payload = b"\x81"
    classes = (
        C_B_D_T_.cbdt_bitmap_classes
        if image_format >= 17
        else E_B_D_T_.ebdt_bitmap_classes
    )
    data = header + payload
    return classes[image_format](data, font), font, data, metrics


@pytest.mark.parametrize("decompile_first", [False, True])
def test_missing_attribute_preserves_bitmap_metrics(bitmap_glyph, decompile_first):
    glyph, font, data, metrics = bitmap_glyph
    if decompile_first:
        assert vars(glyph.metrics) == metrics

    # Attribute probing (for example, by an interactive display) must not
    # restart decompilation and replace the metrics with an empty object.
    for _ in range(2):
        assert not hasattr(glyph, "_repr_mimebundle_")
        assert vars(glyph.metrics) == metrics
        assert glyph.compile(font) == data


def test_lazy_bitmap_metrics_and_edited_metrics_are_preserved(bitmap_glyph):
    glyph, font, data, metrics = bitmap_glyph
    assert vars(glyph.metrics) == metrics
    assert glyph.compile(font) == data
    glyph.metrics.width = 7
    glyph.ensureDecompiled()
    assert not hasattr(glyph, "missing_attribute")
    assert glyph.metrics.width == 7
    assert glyph.compile(font) == data[:1] + b"\x07" + data[2:]
