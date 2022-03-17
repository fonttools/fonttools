import os
from fontTools.ttLib import TTCollection
import pytest

TTX_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "ttx", "data")


@pytest.mark.parametrize("lazy", [None, True, False])
def test_lazy_open(lazy):
    ttc = os.path.join(TTX_DATA_DIR, "TestTTC.ttc")
    with TTCollection(ttc, lazy=lazy) as collection:
        assert len(collection) == 2
        assert collection[0]["maxp"].numGlyphs == 6
        assert collection[1]["maxp"].numGlyphs == 6
