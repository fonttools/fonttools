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
