import os

import pytest
import py

ufoLib2 = pytest.importorskip("ufoLib2")

from fontTools.cu2qu.ufo import CURVE_TYPE_LIB_KEY
from fontTools.cu2qu.cli import main


DATADIR = os.path.join(os.path.dirname(__file__), "data")

TEST_UFOS = [
    py.path.local(DATADIR).join("RobotoSubset-Regular.ufo"),
    py.path.local(DATADIR).join("RobotoSubset-Bold.ufo"),
]


@pytest.fixture
def test_paths(tmpdir):
    result = []
    for path in TEST_UFOS:
        new_path = tmpdir / path.basename
        path.copy(new_path)
        result.append(new_path)
    return result


class MainTest(object):
    @staticmethod
    def run_main(*args):
        main([str(p) for p in args if p])

    def test_single_input_no_output(self, test_paths):
        ufo_path = test_paths[0]

        self.run_main(ufo_path)

        font = ufoLib2.Font.open(ufo_path)
        assert font.lib[CURVE_TYPE_LIB_KEY] == "quadratic"

    def test_single_input_output_file(self, tmpdir):
        input_path = TEST_UFOS[0]
        output_path = tmpdir / input_path.basename
        self.run_main("-o", output_path, input_path)

        assert output_path.check(dir=1)

    def test_multiple_inputs_output_dir(self, tmpdir):
        output_dir = tmpdir / "output_dir"
        self.run_main("-d", output_dir, *TEST_UFOS)

        assert output_dir.check(dir=1)
        outputs = set(p.basename for p in output_dir.listdir())
        assert "RobotoSubset-Regular.ufo" in outputs
        assert "RobotoSubset-Bold.ufo" in outputs

    def test_interpolatable_inplace(self, test_paths):
        self.run_main("-i", *test_paths)
        self.run_main("-i", *test_paths)  # idempotent

    @pytest.mark.parametrize("mode", ["", "-i"], ids=["normal", "interpolatable"])
    def test_copytree(self, mode, tmpdir):
        output_dir = tmpdir / "output_dir"
        self.run_main(mode, "-d", output_dir, *TEST_UFOS)

        output_dir_2 = tmpdir / "output_dir_2"
        # no conversion when curves are already quadratic, just copy
        self.run_main(mode, "-d", output_dir_2, *output_dir.listdir())
        # running again overwrites existing with the copy
        self.run_main(mode, "-d", output_dir_2, *output_dir.listdir())

    def test_multiprocessing(self, tmpdir, test_paths):
        self.run_main(*(test_paths + ["-j"]))

    def test_keep_direction(self, test_paths):
        self.run_main("--keep-direction", *test_paths)

    def test_conversion_error(self, test_paths):
        self.run_main("--conversion-error", 0.002, *test_paths)

    def test_conversion_error_short(self, test_paths):
        self.run_main("-e", 0.003, test_paths[0])
