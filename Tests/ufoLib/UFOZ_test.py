from fontTools.ufoLib import UFOReader, UFOWriter, UFOFileStructure
from fontTools.ufoLib.errors import UFOLibError, GlifLibError
from fontTools.misc import plistlib
from fontTools.misc.textTools import tostr
import sys
import os
import fs.osfs
import fs.tempfs
import fs.memoryfs
import fs.copy
import pytest
import warnings


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
    m = fs.memoryfs.MemoryFS()
    fs.copy.copy_dir(TESTDATA, TEST_UFO3, m, "/")
    return m


class TestMemoryFS:
    def test_init_reader(self, memufo):
        with UFOReader(memufo) as reader:
            assert reader.formatVersion == 3
            assert reader.fileStructure == UFOFileStructure.PACKAGE

    def test_init_writer(self):
        m = fs.memoryfs.MemoryFS()
        with UFOWriter(m) as writer:
            assert m.exists("metainfo.plist")
            assert writer._path == "<memfs>"
