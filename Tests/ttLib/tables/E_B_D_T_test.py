import pytest

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
