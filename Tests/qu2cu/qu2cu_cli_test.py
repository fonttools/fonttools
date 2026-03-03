import os
from types import SimpleNamespace

import pytest
import py

import fontTools.qu2cu.cli as qu2cu_cli
from fontTools.qu2cu.cli import _main as main
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

    def test_rejects_variable_fonts(self, monkeypatch):
        class FakeTTFont(dict):
            def __init__(self, path):
                super().__init__({"gvar": object(), "head": SimpleNamespace(unitsPerEm=1000)})

        monkeypatch.setattr(qu2cu_cli, "TTFont", FakeTTFont)

        with pytest.raises(ValueError, match="Cannot convert variable font"):
            qu2cu_cli._font_to_cubic("dummy.ttf", "dummy.cubic.ttf", dump_stats=False, max_err_em=0.001, all_cubic=False)

    def test_rejects_non_positive_conversion_error(self):
        with pytest.raises(SystemExit, match="2"):
            self.run_main("--conversion-error", "0", TEST_TTFS[0])
