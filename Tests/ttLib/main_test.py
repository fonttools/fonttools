import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from fontTools.ttLib import TTCollection, TTFont, __main__

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


@pytest.fixture
def ttcollection_path():
    font1 = TTFont()
    font1.importXML(TEST_DATA / "TestTTF-Regular.ttx")
    font2 = TTFont()
    font2.importXML(TEST_DATA / "TestTTF-Regular.ttx")
    coll = TTCollection()
    coll.fonts = [font1, font2]
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as fp:
        collection_path = Path(fp.name)
        coll.save(collection_path)
    yield collection_path
    collection_path.unlink()


@pytest.fixture(params=[None, "woff"])
def flavor(request):
    return request.param


def test_ttLib_main_as_subprocess(ttfont_path):
    subprocess.run(
        [sys.executable, "-m", "fontTools.ttLib", str(ttfont_path)], check=True
    )


def test_ttLib_open_ttfont(ttfont_path):
    __main__.main([str(ttfont_path)])


def test_ttLib_open_save_ttfont(tmp_path, ttfont_path, flavor):
    output_path = tmp_path / "TestTTF-Regular.ttf"
    args = ["-o", str(output_path), str(ttfont_path)]
    if flavor is not None:
        args.extend(["--flavor", flavor])

    __main__.main(args)

    assert output_path.exists()
    assert TTFont(output_path).getGlyphOrder() == TTFont(ttfont_path).getGlyphOrder()


def test_ttLib_open_ttcollection(ttcollection_path):
    __main__.main(["-y", "0", str(ttcollection_path)])


def test_ttLib_open_ttcollection_save_single_font(tmp_path, ttcollection_path, flavor):
    for i in range(2):
        output_path = tmp_path / f"TestTTF-Regular#{i}.ttf"
        args = ["-y", str(i), "-o", str(output_path), str(ttcollection_path)]
        if flavor is not None:
            args.extend(["--flavor", flavor])

        __main__.main(args)

        assert output_path.exists()
        assert (
            TTFont(output_path).getGlyphOrder()
            == TTCollection(ttcollection_path)[i].getGlyphOrder()
        )


def test_ttLib_open_ttcollection_save_ttcollection(tmp_path, ttcollection_path):
    output_path = tmp_path / "TestTTF.ttc"

    __main__.main(["-o", str(output_path), str(ttcollection_path)])

    assert output_path.exists()
    assert len(TTCollection(output_path)) == len(TTCollection(ttcollection_path))


def test_ttLib_open_multiple_fonts_save_ttcollection(tmp_path, ttfont_path):
    output_path = tmp_path / "TestTTF.ttc"

    __main__.main(["-o", str(output_path), str(ttfont_path), str(ttfont_path)])

    assert output_path.exists()

    coll = TTCollection(output_path)
    assert len(coll) == 2
    assert coll[0].getGlyphOrder() == coll[1].getGlyphOrder()
