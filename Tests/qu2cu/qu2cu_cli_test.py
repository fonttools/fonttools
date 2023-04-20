import os

import pytest
import py

from fontTools.qu2cu.cli import main
from fontTools.ttLib import TTFont


DATADIR = os.path.join(os.path.dirname(__file__), "data")

TEST_TTFS = [
    py.path.local(DATADIR).join("NotoSansArabic-Regular.quadratic.subset.ttf"),
]


@pytest.fixture
def test_paths(tmpdir):
    result = []
    for path in TEST_TTFS:
        new_path = tmpdir / path.basename
        path.copy(new_path)
        result.append(new_path)
    return result


class MainTest(object):
    @staticmethod
    def run_main(*args):
        main([str(p) for p in args if p])

    def test_no_output(self, test_paths):
        ttf_path = test_paths[0]

        self.run_main(ttf_path)

        output_path = str(ttf_path).replace(".ttf", ".cubic.ttf")
        font = TTFont(output_path)
        assert font["head"].glyphDataFormat == 1
        assert os.stat(ttf_path).st_size > os.stat(output_path).st_size

    def test_output_file(self, test_paths):
        ttf_path = test_paths[0]
        output_path = str(ttf_path) + ".cubic"

        self.run_main(ttf_path, "-o", output_path)

        font = TTFont(output_path)
        assert font["head"].glyphDataFormat == 1

    def test_stats(self, test_paths):
        ttf_path = test_paths[0]
        self.run_main(ttf_path, "--verbose")

    def test_all_cubic(self, test_paths):
        ttf_path = test_paths[0]

        self.run_main(ttf_path, "-c")

        output_path = str(ttf_path).replace(".ttf", ".cubic.ttf")
        font = TTFont(output_path)
        assert font["head"].glyphDataFormat == 1
