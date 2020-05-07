import logging
import shutil

from fontTools.misc import plistlib
from fontTools.ufoLib import UFOReader, UFOWriter, UFOFormatVersion
from fontTools.ufoLib.errors import UFOLibError, UnsupportedUFOFormat
import pytest


@pytest.fixture
def ufo_path(tmp_path):
    ufodir = tmp_path / "TestFont.ufo"
    ufodir.mkdir()
    with (ufodir / "metainfo.plist").open("wb") as f:
        plistlib.dump({"creator": "pytest", "formatVersion": 3}, f)
    (ufodir / "glyphs").mkdir()
    with (ufodir / "layercontents.plist").open("wb") as f:
        plistlib.dump([("public.default", "glyphs")], f)
    return ufodir


def test_formatVersion_deprecated(ufo_path):
    reader = UFOReader(ufo_path)

    with pytest.warns(DeprecationWarning) as warnings:
        assert reader.formatVersion == 3

    assert len(warnings) == 1
    assert "is deprecated; use the 'formatVersionTuple'" in warnings[0].message.args[0]


def test_formatVersionTuple(ufo_path):
    reader = UFOReader(ufo_path)

    assert reader.formatVersionTuple == (3, 0)
    assert reader.formatVersionTuple.major == 3
    assert reader.formatVersionTuple.minor == 0
    assert str(reader.formatVersionTuple) == "3.0"


def test_readMetaInfo_errors(ufo_path):
    (ufo_path / "metainfo.plist").unlink()
    with pytest.raises(UFOLibError, match="'metainfo.plist' is missing"):
        UFOReader(ufo_path)

    (ufo_path / "metainfo.plist").write_bytes(plistlib.dumps({}))
    with pytest.raises(UFOLibError, match="Missing required formatVersion"):
        UFOReader(ufo_path)

    (ufo_path / "metainfo.plist").write_bytes(plistlib.dumps([]))
    with pytest.raises(UFOLibError, match="metainfo.plist is not properly formatted"):
        UFOReader(ufo_path)


def test_readMetaInfo_unsupported_format_version(ufo_path, caplog):
    metainfo = {"formatVersion": 10, "formatVersionMinor": 15}
    (ufo_path / "metainfo.plist").write_bytes(plistlib.dumps(metainfo))

    with pytest.raises(UnsupportedUFOFormat):
        UFOReader(ufo_path)  # validate=True by default

    with pytest.raises(UnsupportedUFOFormat):
        UFOReader(ufo_path, validate=True)

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="fontTools.ufoLib"):
        UFOReader(ufo_path, validate=False)

    assert len(caplog.records) == 1
    assert "Unsupported UFO format" in caplog.text
    assert "Assuming the latest supported version" in caplog.text


def test_UFOWriter_formatVersion(tmp_path):
    ufo_path = tmp_path / "TestFont.ufo"
    with UFOWriter(ufo_path, formatVersion=3) as writer:
        assert writer.formatVersionTuple == (3, 0)

    shutil.rmtree(str(ufo_path))
    with UFOWriter(ufo_path, formatVersion=(2, 0)) as writer:
        assert writer.formatVersionTuple == (2, 0)


def test_UFOWriter_formatVersion_default_latest(tmp_path):
    writer = UFOWriter(tmp_path / "TestFont.ufo")
    assert writer.formatVersionTuple == UFOFormatVersion.default()


def test_UFOWriter_unsupported_format_version(tmp_path):
    with pytest.raises(UnsupportedUFOFormat):
        UFOWriter(tmp_path, formatVersion=(123, 456))


def test_UFOWriter_previous_higher_format_version(ufo_path):
    with pytest.raises(
        UnsupportedUFOFormat, match="UFO located at this path is a higher version"
    ):
        UFOWriter(ufo_path, formatVersion=(2, 0))
