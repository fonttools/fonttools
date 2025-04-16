import os
from pathlib import Path
from fontTools.ttLib import TTCollection
import pytest

TTX_DATA_DIR = Path(__file__).parent.parent / "ttx" / "data"


@pytest.fixture(params=[None, True, False])
def lazy(request):
    return request.param


def test_lazy_open_path(lazy):
    ttc_path = TTX_DATA_DIR / "TestTTC.ttc"
    with TTCollection(ttc_path, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6


def test_lazy_open_file(lazy):
    with (TTX_DATA_DIR / "TestTTC.ttc").open("rb") as file:
        collection = TTCollection(file, lazy=lazy)
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
