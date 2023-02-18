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

from fontTools.qu2cu import quadratic_to_curves, quadratics_to_curves


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
                False,
            ),
            (
                [
                    [(0, 0), (0, 1), (2, 1), (2, 2)],
                ],
                [
                    ((0, 0), (0, 4 / 3), (2, 2 / 3), (2, 2)),
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

        if len(quadratics) == 1:
            c = quadratic_to_curves(quadratics[0], tolerance, cubic_only)
            assert c == expected

        c = quadratics_to_curves(quadratics, tolerance, cubic_only)
        assert c == expected
