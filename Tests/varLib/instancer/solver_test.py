from fontTools.varLib.instancer import solver
from fontTools.varLib.instancer import NormalizedAxisTripleAndDistances
import pytest


class RebaseTentTest(object):
    @pytest.mark.parametrize(
        "tent, axisRange, expected",
        [
            # Case 1: # Pin at default
            pytest.param((0, 1, 1), (0.0, 0.0, 0.0), []),
            # Case 1:
            pytest.param((0.3, 0.5, 0.8), (0.1, 0.2, 0.3), []),
            # Pin axis
            pytest.param(
                (0, 1, 1),
                (0.5, 0.5, 0.5),
                [
                    (0.5, None),
                ],
            ),
            # Case 2:
            pytest.param(
                (0, 1, 1),
                (-1, 0, 0.5),
                [
                    (0.5, (0, 1, 1)),
                ],
            ),
            # Case 2:
            pytest.param(
                (0, 1, 1),
                (-1, 0, 0.75),
                [
                    (0.75, (0, 1, 1)),
                ],
            ),
            #
            # Without gain:
            #
            # Case 3
            pytest.param(
                (0, 0.2, 1),
                (-1, 0, 0.8),
                [
                    (1, (0, 0.25, 1.25)),
                ],
            ),
            # Case 3 boundary
            pytest.param(
                (0, 0.4, 1),
                (-1, 0, 0.5),
                [
                    (1, (0, 0.8, 1.99994)),
                ],
            ),
            # Case 4
            pytest.param(
                (0, 0.25, 1),
                (-1, 0, 0.4),
                [
                    (1, (0, 0.625, 1)),
                    (0.8, (0.625, 1, 1)),
                ],
            ),
            pytest.param(
                (0.25, 0.3, 1.05),
                (0, 0.2, 0.4),
                [
                    (1, (0.25, 0.5, 1)),
                    (2.6 / 3, (0.5, 1, 1)),
                ],
            ),
            # Case 4 boundary
            pytest.param(
                (0.25, 0.5, 1),
                (0, 0.25, 0.5),
                [
                    (1, (0, 1, 1)),
                ],
            ),
            #
            # With gain:
            #
            # Case 3a/1neg
            pytest.param(
                (0.0, 0.5, 1),
                (0, 0.5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                    (-1, (-1, -1, 0)),
                ],
            ),
            pytest.param(
                (0.0, 0.5, 1),
                (0, 0.5, 0.75),
                [
                    (1, None),
                    (-0.5, (0, 1, 1)),
                    (-1, (-1, -1, 0)),
                ],
            ),
            pytest.param(
                (0.0, 0.5, 1),
                (0, 0.25, 0.8),
                [
                    (0.5, None),
                    (0.5, (0, 0.45454545, 0.9090909090)),
                    (-0.1, (0.9090909090, 1.0, 1.0)),
                    (-0.5, (-1, -1, 0)),
                ],
            ),
            # Case 3a/1neg
            pytest.param(
                (0.0, 0.5, 2),
                (0.2, 0.5, 0.8),
                [
                    (1, None),
                    (-0.2, (0, 1, 1)),
                    (-0.6, (-1, -1, 0)),
                ],
            ),
            # Case 3a/1neg
            pytest.param(
                (0.0, 0.5, 2),
                (0.2, 0.5, 1),
                [
                    (1, None),
                    (-1 / 3, (0, 1, 1)),
                    (-0.6, (-1, -1, 0)),
                ],
            ),
            # Case 3
            pytest.param(
                (0, 0.5, 1),
                (0.25, 0.25, 0.75),
                [
                    (0.5, None),
                    (0.5, (0, 0.5, 1.0)),
                ],
            ),
            # Case 1neg
            pytest.param(
                (0.0, 0.5, 1),
                (0, 0.25, 0.5),
                [
                    (0.5, None),
                    (0.5, (0, 1, 1)),
                    (-0.5, (-1, -1, 0)),
                ],
            ),
            # Case 2neg
            pytest.param(
                (0.05, 0.55, 1),
                (0, 0.25, 0.5),
                [
                    (0.4, None),
                    (0.5, (0, 1, 1)),
                    (-0.4, (-1, -0.8, 0)),
                    (-0.4, (-1, -1, -0.8)),
                ],
            ),
            # Case 2neg, other side
            pytest.param(
                (-1, -0.55, -0.05),
                (-0.5, -0.25, 0),
                [
                    (0.4, None),
                    (0.5, (-1, -1, 0)),
                    (-0.4, (0, 0.8, 1)),
                    (-0.4, (0.8, 1, 1)),
                ],
            ),
            #
            # Misc corner cases
            #
            pytest.param(
                (0.5, 0.5, 0.5),
                (0.5, 0.5, 0.5),
                [
                    (1, None),
                ],
            ),
            pytest.param(
                (0.3, 0.5, 0.7),
                (0.1, 0.5, 0.9),
                [
                    (1, None),
                    (-1, (0, 0.5, 1)),
                    (-1, (0.5, 1, 1)),
                    (-1, (-1, -0.5, 0)),
                    (-1, (-1, -1, -0.5)),
                ],
            ),
            pytest.param(
                (0.5, 0.5, 0.5),
                (0.25, 0.25, 0.5),
                [
                    (1, (1, 1, 1)),
                ],
            ),
            pytest.param(
                (0.5, 0.5, 0.5),
                (0.25, 0.35, 0.5),
                [
                    (1, (1, 1, 1)),
                ],
            ),
            pytest.param(
                (0.5, 0.5, 0.55),
                (0.25, 0.35, 0.5),
                [
                    (1, (1, 1, 1)),
                ],
            ),
            pytest.param(
                (0.5, 0.5, 1),
                (0.5, 0.5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                ],
            ),
            pytest.param(
                (0.25, 0.5, 1),
                (0.5, 0.5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                ],
            ),
            pytest.param(
                (0, 0.2, 1),
                (0, 0, 0.5),
                [
                    (1, (0, 0.4, 1.99994)),
                ],
            ),
            # https://github.com/fonttools/fonttools/issues/3139
            pytest.param(
                (0, 0.5, 1),
                (-1, 0.25, 1),
                [
                    (0.5, None),
                    (0.5, (0.0, 1 / 3, 2 / 3)),
                    (-0.5, (2 / 3, 1, 1)),
                    (-0.5, (-1, -0.2, 0)),
                    (-0.5, (-1, -1, -0.2)),
                ],
            ),
            # Dirac delta at new default. Fancy!
            pytest.param(
                (0.5, 0.5, 0.5),
                (0, 0.5, 1),
                [
                    (1, None),
                    (-1, (0, 0.0001220703, 1)),
                    (-1, (0.0001220703, 1, 1)),
                    (-1, (-1, -0.0001220703, 0)),
                    (-1, (-1, -1, -0.0001220703)),
                ],
            ),
            # https://github.com/fonttools/fonttools/issues/3177
            pytest.param(
                (0, 1, 1),
                (-1, -0.5, +1, 1, 1),
                [
                    (1.0, (1 / 3, 1.0, 1.0)),
                ],
            ),
            pytest.param(
                (0, 1, 1),
                (-1, -0.5, +1, 2, 1),
                [
                    (1.0, (0.5, 1.0, 1.0)),
                ],
            ),
            # https://github.com/fonttools/fonttools/issues/3291
            pytest.param(
                (0.6, 0.7, 0.8),
                (-1, 0.2, +1, 1, 1),
                [
                    (1.0, (0.5, 0.625, 0.75)),
                ],
            ),
        ],
    )
    def test_rebaseTent(self, tent, axisRange, expected):
        axisRange = NormalizedAxisTripleAndDistances(*axisRange)

        sol = solver.rebaseTent(tent, axisRange)

        a = pytest.approx
        expected = [
            (a(scalar), (a(v[0]), a(v[1]), a(v[2])) if v is not None else None)
            for scalar, v in expected
        ]

        assert sol == expected, (tent, axisRange)
