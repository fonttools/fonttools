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


def test_osfs_rejects_symlink_out_of_root(tmp_path):
    # resolve() expands symlinks, so a link inside the root that points outside
    # it is rejected as well; this is stricter than pyfilesystem2 and intended.
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "secret.txt").write_bytes(b"secret")
    root = tmp_path / "root"
    root.mkdir()
    try:
        (root / "link").symlink_to(tmp_path / "outside", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported")
    ofs = OSFS(root)
    with pytest.raises(IllegalBackReference):
        ofs.readbytes("link/secret.txt")


def _evil_zip(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("font.ufo/metainfo.plist", b"x")
        z.writestr("../escaped.txt", b"pwned")
        z.writestr("font.ufo/lib.plist", b"y")
    return ReadZipFS(str(path))


def test_readzipfs_member_cannot_escape_root(tmp_path):
    zfs = _evil_zip(tmp_path / "evil.zip")
    # building the directory mirror must not create files outside its root
    with pytest.raises(IllegalBackReference) as excinfo:
        zfs.exists("font.ufo/metainfo.plist")
    # the offending zip entry is named, not the path the caller asked for
    assert "../escaped.txt" in str(excinfo.value)
    assert not (tmp_path / "escaped.txt").exists()


def test_readzipfs_failed_mirror_is_not_cached(tmp_path):
    # the mirror can also fail to build for reasons the member-name pre-scan
    # cannot see -- here a member named both as a file and as a directory, which
    # makes makedirs raise -- and the half-built mirror must not be published
    zip_path = tmp_path / "conflict.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("node", b"file")
        z.writestr("node/child.txt", b"x")
        z.writestr("after.txt", b"y")
    zfs = ReadZipFS(str(zip_path))
    for _ in range(2):
        with pytest.raises(OSError):
            zfs.exists("after.txt")
    assert zfs._directory_fs is None


def test_readzipfs_rejection_is_repeatable(tmp_path):
    # the mirror is built lazily and cached; rejecting an archive must not leave
    # a half-built one behind, or a second call would answer from a silently
    # truncated view of the zip instead of failing again
    zfs = _evil_zip(tmp_path / "evil.zip")
    for _ in range(2):
        with pytest.raises(IllegalBackReference):
            zfs.exists("font.ufo/metainfo.plist")
    # a member listed after the offending one must not read as missing
    with pytest.raises(IllegalBackReference):
        zfs.exists("font.ufo/lib.plist")
