import os
import sys

import pytest

from fontTools.misc import filesystem as fs
from fontTools.misc.textTools import tostr
from fontTools.ufoLib import UFOFileStructure, UFOReader, UFOWriter, haveFS

TESTDATA = fs.osfs.OSFS(os.path.join(os.path.dirname(__file__), "testdata"))
TEST_UFO3 = "TestFont1 (UFO3).ufo"
TEST_UFOZ = "TestFont1 (UFO3).ufoz"


@pytest.fixture(params=[TEST_UFO3, TEST_UFOZ])
def testufo(request):
    name = request.param
    with fs.tempfs.TempFS() as tmp:
        if TESTDATA.isdir(name):
            fs.copy.copy_dir(TESTDATA, name, tmp, name)
        else:
            fs.copy.copy_file(TESTDATA, name, tmp, name)
        yield tmp.getsyspath(name)


@pytest.fixture
def testufoz():
    with fs.tempfs.TempFS() as tmp:
        fs.copy.copy_file(TESTDATA, TEST_UFOZ, tmp, TEST_UFOZ)
        yield tmp.getsyspath(TEST_UFOZ)


class TestUFOZ:
    def test_read(self, testufoz):
        with UFOReader(testufoz) as reader:
            assert reader.fileStructure == UFOFileStructure.ZIP
            assert reader.formatVersion == 3
            gs = reader.getGlyphSet()
            a = gs.getGLIF("a").decode("utf-8")
            assert a.splitlines() == [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<glyph name="a" format="2">',
                '  <advance height="750" width="388"/>',
                '  <unicode hex="0061"/>',
                "  <outline>",
                "    <contour>",
                '      <point x="66" y="0" type="line"/>',
                '      <point x="322" y="0" type="line"/>',
                '      <point x="194" y="510" type="line"/>',
                "    </contour>",
                "  </outline>",
                "</glyph>",
            ]

    def test_getFileModificationTime(self, testufoz):
        with UFOReader(testufoz) as reader:
            modified = reader.getFileModificationTime("metainfo.plist")
            assert isinstance(modified, float)

    def test_write(self, testufoz):
        with UFOWriter(testufoz, structure="zip") as writer:
            writer.writeLib({"hello world": 123})
        with UFOReader(testufoz) as reader:
            assert reader.readLib() == {"hello world": 123}


def test_pathlike(testufo):
    class PathLike:
        def __init__(self, s):
            self._path = s

        def __fspath__(self):
            return tostr(self._path, sys.getfilesystemencoding())

    path = PathLike(testufo)

    with UFOReader(path) as reader:
        assert reader._path == path.__fspath__()

    with UFOWriter(path) as writer:
        assert writer._path == path.__fspath__()


def test_path_attribute_deprecated(testufo):
    with UFOWriter(testufo) as writer:
        with pytest.warns(DeprecationWarning, match="The 'path' attribute"):
            writer.path


@pytest.fixture
def memufo():
    fs = pytest.importorskip("fs")
    m = fs.memoryfs.MemoryFS()
    fs.copy.copy_dir(TESTDATA, TEST_UFO3, m, "/")
    return m


@pytest.mark.skipif(not haveFS, reason="requires fs")
class TestMemoryFS:
    def test_init_reader(self, memufo):
        with UFOReader(memufo) as reader:
            assert reader.formatVersion == 3
            assert reader.fileStructure == UFOFileStructure.PACKAGE
        assert not memufo.isclosed()

    def test_init_writer(self):
        fs = pytest.importorskip("fs")
        m = fs.memoryfs.MemoryFS()
        with UFOWriter(m) as writer:
            assert m.exists("metainfo.plist")
            assert writer._path == "<memfs>"
        assert not m.isclosed()
