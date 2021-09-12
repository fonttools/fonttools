import io
import copy
import pickle
from fontTools.ttLib.sfnt import calcChecksum, SFNTReader
import pytest


def test_calcChecksum():
    assert calcChecksum(b"abcd") == 1633837924
    assert calcChecksum(b"abcdxyz") == 3655064932


EMPTY_SFNT = b"\x00\x01\x00\x00" + b"\x00" * 8


def pickle_unpickle(obj):
    return pickle.loads(pickle.dumps(obj))


class SFNTReaderTest:
    @pytest.mark.parametrize("deepcopy", [copy.deepcopy, pickle_unpickle])
    def test_pickle_protocol_FileIO(self, deepcopy, tmp_path):
        fontfile = tmp_path / "test.ttf"
        fontfile.write_bytes(EMPTY_SFNT)
        reader = SFNTReader(fontfile.open("rb"))

        reader2 = deepcopy(reader)

        assert reader2 is not reader
        assert reader2.file is not reader.file

        assert isinstance(reader2.file, io.BufferedReader)
        assert isinstance(reader2.file.raw, io.FileIO)
        assert reader2.file.name == reader.file.name
        assert reader2.file.tell() == reader.file.tell()

        for k, v in reader.__dict__.items():
            if k == "file":
                continue
            assert getattr(reader2, k) == v

    @pytest.mark.parametrize("deepcopy", [copy.deepcopy, pickle_unpickle])
    def test_pickle_protocol_BytesIO(self, deepcopy, tmp_path):
        buf = io.BytesIO(EMPTY_SFNT)
        reader = SFNTReader(buf)

        reader2 = deepcopy(reader)

        assert reader2 is not reader
        assert reader2.file is not reader.file

        assert isinstance(reader2.file, io.BytesIO)
        assert reader2.file.tell() == reader.file.tell()
        assert reader2.file.getvalue() == reader.file.getvalue()

        for k, v in reader.__dict__.items():
            if k == "file":
                continue
            assert getattr(reader2, k) == v
