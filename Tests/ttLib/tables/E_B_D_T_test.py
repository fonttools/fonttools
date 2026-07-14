from fontTools.ttLib.tables.E_B_D_T_ import _writeExtFileImageData


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


def test_extfile_export_contains_crafted_glyph_name(tmp_path):
    # A font can name a glyph with path separators (e.g. via a crafted 'post'
    # table); the "extfile" bitmap export must keep the file inside the folder.
    out = tmp_path / "out"
    out.mkdir()
    writer = _Writer(str(out / "font.ttx"))

    _writeExtFileImageData(0, "../../../pwned", _Bitmap(), writer, None)

    assert not (tmp_path / "pwned.bin").exists()
    written = out / "bitmaps" / "strike0" / "pwned.bin"
    assert written.exists()
    assert written.read_bytes() == b"\xde\xad\xbe\xef"
