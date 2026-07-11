import zipfile

import pytest

from fontTools.misc.filesystem._errors import IllegalBackReference
from fontTools.misc.filesystem._osfs import OSFS
from fontTools.misc.filesystem._zipfs import ReadZipFS


def test_osfs_reads_within_root(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_bytes(b"hello")
    ofs = OSFS(tmp_path)
    assert ofs.readbytes("sub/a.txt") == b"hello"
    # a back-reference that stays within the root is still resolved
    assert ofs.readbytes("sub/../sub/a.txt") == b"hello"


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "../../etc/hosts",
        "sub/../../outside.txt",
        "nonexistent/../../outside.txt",
    ],
)
def test_osfs_rejects_traversal(tmp_path, path):
    (tmp_path.parent / "outside.txt").write_bytes(b"secret")
    ofs = OSFS(tmp_path)
    with pytest.raises(IllegalBackReference):
        ofs.readbytes(path)


def test_subfs_rejects_traversal_out_of_root(tmp_path):
    # mirrors how ufoLib opens a glyph set: an OSFS rooted at the UFO, a SubFS
    # into "glyphs", and a file name coming from the untrusted contents.plist
    ufo = tmp_path / "font.ufo"
    (ufo / "glyphs").mkdir(parents=True)
    (tmp_path / "outside.txt").write_bytes(b"secret")
    sub = OSFS(ufo).opendir("glyphs")
    with pytest.raises(IllegalBackReference):
        sub.readbytes("../../outside.txt")


def test_readzipfs_member_cannot_escape_root(tmp_path):
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("font.ufo/metainfo.plist", b"x")
        z.writestr("../escaped.txt", b"pwned")
    zfs = ReadZipFS(str(zip_path))
    # building the directory mirror must not create files outside its root
    with pytest.raises(IllegalBackReference):
        zfs.exists("font.ufo/metainfo.plist")
