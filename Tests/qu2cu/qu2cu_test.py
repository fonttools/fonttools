# Copyright 2023 Behdad Esfahbod. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import pytest

from fontTools.qu2cu import quadratic_to_curves
from fontTools.qu2cu.qu2cu import main as qu2cu_main
from fontTools.qu2cu.benchmark import main as benchmark_main

import os
import json
from fontTools.cu2qu import curve_to_quadratic


class Qu2CuTest:
    @pytest.mark.parametrize(
        "quadratics, expected, tolerance, cubic_only",
        [
            (
                [
                    [(0, 0), (0, 1), (2, 1), (2, 0)],
                ],
                [
                    ((0, 0), (0, 4 / 3), (2, 4 / 3), (2, 0)),
                ],
                0.1,
                True,
            ),
            (
                [
                    [(0, 0), (0, 1), (2, 1), (2, 2)],
                ],
                [
                    ((0, 0), (0, 4 / 3), (2, 2 / 3), (2, 2)),
                ],
                0.2,
                True,
            ),
            (
                [
                    [(0, 0), (0, 1), (1, 1)],
                    [(1, 1), (3, 1), (3, 0)],
                ],
                [
                    ((0, 0), (0, 1), (1, 1)),
                    ((1, 1), (3, 1), (3, 0)),
                ],
                0.2,
                False,
            ),
            (
                [
                    [(0, 0), (0, 1), (1, 1)],
                    [(1, 1), (3, 1), (3, 0)],
                ],
                [
                    ((0, 0), (0, 2 / 3), (1 / 3, 1), (1, 1)),
                    ((1, 1), (7 / 3, 1), (3, 2 / 3), (3, 0)),
                ],
                0.2,
                True,
            ),
        ],
    )
    def test_simple(self, quadratics, expected, tolerance, cubic_only):
        expected = [
            tuple((pytest.approx(p[0]), pytest.approx(p[1])) for p in curve)
            for curve in expected
        ]

        c = quadratic_to_curves(quadratics, tolerance, cubic_only)
        assert c == expected

    def test_roundtrip(self):
        DATADIR = os.path.join(os.path.dirname(__file__), "..", "cu2qu", "data")
        with open(os.path.join(DATADIR, "curves.json"), "r") as fp:
            curves = json.load(fp)

        tolerance = 1

        splines = [curve_to_quadratic(c, tolerance) for c in curves]
        reconsts = [quadratic_to_curves([spline], tolerance) for spline in splines]

        for curve, reconst in zip(curves, reconsts):
            assert len(reconst) == 1
            curve = tuple((pytest.approx(p[0]), pytest.approx(p[1])) for p in curve)
            assert curve == reconst[0]

    def test_main(self):
        # Just for coverage
        qu2cu_main()
        benchmark_main()
