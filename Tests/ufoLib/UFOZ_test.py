from fontTools.ufoLib import UFOReader, UFOWriter, UFOFileStructure
from fontTools.ufoLib.errors import UFOLibError, GlifLibError
from fontTools.misc import plistlib
from fontTools.misc.textTools import tostr
import sys
import shutil
import os
import fsspec
import pytest
import warnings
from pathlib import Path


TESTDATA_DIR = Path(__file__).parent / "testdata"
TEST_UFO3 = "TestFont1 (UFO3).ufo"
TEST_UFOZ = "TestFont1 (UFO3).ufoz"


@pytest.fixture(params=[TEST_UFO3, TEST_UFOZ])
def testufo(request, tmp_path_factory):
    path = request.param
    tmp_dir = tmp_path_factory.mktemp(path)

    test_data = TESTDATA_DIR / path
    test_data_target = tmp_dir / path
    if test_data.is_dir():
        shutil.copytree(test_data, test_data_target)
    else:
        shutil.copy(test_data, test_data_target)

    return test_data_target


@pytest.fixture
def testufoz(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp(TEST_UFOZ)
    test_data = TESTDATA_DIR / TEST_UFOZ
    test_data_target = tmp_dir / TEST_UFOZ
    shutil.copy(test_data, test_data_target)
    yield test_data_target


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
            return os.fspath(self._path)

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
    m = fsspec.filesystem("memory")
    m.put(TESTDATA_DIR / TEST_UFO3, "/", recursive=True)
    return m


class TestMemoryFS:
    def test_init_reader(self, memufo):
        with UFOReader(memufo) as reader:
            assert reader.formatVersion == 3
            assert reader.fileStructure == UFOFileStructure.PACKAGE

    def test_init_writer(self):
        m = fsspec.filesystem("memory")
        with UFOWriter(m) as writer:
            assert m.exists("metainfo.plist")
            assert writer._path is None
