import zipfile

import pytest

from fontTools.misc.filesystem._zipfs import WriteZipFS


@pytest.mark.parametrize("suffix", [".zip", ".ufoz"])
def test_writezipfs_repeated_close(tmp_path, suffix):
    path = tmp_path / f"archive{suffix}"
    fs = WriteZipFS(path)
    fs.writebytes("hello.txt", b"hello")
    fs.close()
    archive = path.read_bytes()

    fs.close()

    assert fs.isclosed()
    assert path.read_bytes() == archive
    with zipfile.ZipFile(path) as zf:
        assert zf.read("hello.txt") == b"hello"


@pytest.mark.parametrize("suffix", [".zip", ".ufoz"])
def test_writezipfs_explicit_close_in_context_manager(tmp_path, suffix):
    path = tmp_path / f"archive{suffix}"
    with WriteZipFS(path) as fs:
        fs.writebytes("hello.txt", b"hello")
        fs.close()

    assert fs.isclosed()
    with zipfile.ZipFile(path) as zf:
        assert zf.read("hello.txt") == b"hello"


@pytest.mark.parametrize("suffix", [".ufoz", ".ZIP", ""])
def test_writezipfs_preserves_sibling_archive(tmp_path, suffix):
    path = tmp_path / f"archive{suffix}"
    sibling = tmp_path / "archive.zip"
    with zipfile.ZipFile(sibling, "w") as zf:
        zf.writestr("original.txt", b"keep this archive")
    original = sibling.read_bytes()
    if path.exists():
        pytest.skip("Output and sibling names alias on this filesystem")

    with WriteZipFS(path) as fs:
        fs.writebytes("hello.txt", b"hello")

    assert sibling.exists()
    assert sibling.read_bytes() == original
    with zipfile.ZipFile(path) as zf:
        assert zf.namelist() == ["hello.txt"]
        assert zf.read("hello.txt") == b"hello"


@pytest.mark.parametrize("suffix", [".zip", ".ufoz", ".ZIP", ""])
def test_writezipfs_creates_output_parent(tmp_path, suffix):
    path = tmp_path / "new" / f"archive{suffix}"
    with WriteZipFS(path) as fs:
        fs.writebytes("hello.txt", b"hello")
    with zipfile.ZipFile(path) as zf:
        assert zf.read("hello.txt") == b"hello"
