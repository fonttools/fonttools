import io
import copy
import pickle
import tempfile
from fontTools.ttLib import TTFont
from fontTools.ttLib.sfnt import calcChecksum, SFNTReader, WOFFFlavorData
from pathlib import Path
import pytest

TEST_DATA = Path(__file__).parent / "data"


@pytest.fixture
def ttfont_path():
    font = TTFont()
    font.importXML(TEST_DATA / "TestTTF-Regular.ttx")
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as fp:
        font_path = Path(fp.name)
        font.save(font_path)
    yield font_path
    font_path.unlink()


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


def test_ttLib_sfnt_write_privData(tmp_path, ttfont_path):
    output_path = tmp_path / "TestTTF-Regular.woff"
    font = TTFont(ttfont_path)

    privData = "Private Eyes".encode()

    data = WOFFFlavorData()
    head = font["head"]
    data.majorVersion, data.minorVersion = map(
        int, format(head.fontRevision, ".3f").split(".")
    )

    data.privData = privData
    font.flavor = "woff"
    font.flavorData = data
    font.save(output_path)

    assert output_path.exists()
    assert TTFont(output_path).flavorData.privData == privData
