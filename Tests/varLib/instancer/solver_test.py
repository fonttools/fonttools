from fontTools.varLib.instancer import solver
import pytest

class RebaseTentTest(object):

    @pytest.mark.parametrize(
        "tent, axisRange, expected",
        [

            # Case 1: # Pin at default
            pytest.param(
                (0, 1, 1), (.0, .0, .0),
                [
                ]

            ),
            # Case 1:
            pytest.param(
                (0.3, .5, .8), (.1, .2, .3),
                [
                ]
            ),

            # Pin axis
            pytest.param(
                (0, 1, 1), (.5, .5, .5),
                [
                    (.5, (0, 0, 0)),
                ]
            ),

            # Case 2:
            pytest.param(
                (0, 1, 1), (-1, 0, .5),
                [
                    (.5, (0, 1.0, 1.0)),
                ]
            ),
            # Case 2:
            pytest.param(
                (0, 1, 1), (-1, 0, .75),
                [
                    (.75, (0, 1.0, 1.0)),
                ]
            ),

            #
            # Without gain:
            #

            # Case 3
            pytest.param(
                (0, .2, 1), (-1, 0, .8),
                [
                    (1, (0, 0.25, 1.25)),
                ]
            ),
            # Case 3 boundary
            pytest.param(
                (0, .4, 1), (-1, 0, .5),
                [
                    (1, (0.0, 0.8, 1.99993896484375)),
                ]
            ),

            # Case 4
            pytest.param(
                (0, .25, 1), (-1, 0, .4),
                [
                    (1, (0.0, 0.625, 1.0)),
                    (0.7999999999999999, (0.625, 1.0, 1.0)),
                ]
            ),
            # Case 4 boundary
            pytest.param(
                (.25, .5, 1), (0, .25, .5),
                [
                    (1, (0, 1, 1)),
                ]
            ),


            #
            # With gain:
            #

            # Case 3/1neg
            pytest.param(
                (.0, .5, 1), (0, .5, 1),
                [
                    (1, (-1, 0, 1)),
                    (-1, (0, 1, 1)),
                    (-1, (-1, -1, 0)),
                ]
            ),

            # Case 4/1neg
            pytest.param(
                (.0, .5, 2), (0, .5, .8),
                [
                    (1, (-1, 0, 1)),
                    (-1.0, (0.0, 1, 1)),
                    (-1, (-1, -1, 0)),
                ]
            ),

            # Case 1neg
            pytest.param(
                (.0, .5, 1), (0, .25, .5),
                [
                    (.5, (-1, 0, 1)),
                    (.5, (0, 1, 1)),
                    (-.5, (-1, -1, 0)),
                ]
            ),

            # Case 2neg
            pytest.param(
                (.05, .55, 1), (0, .25, .5),
                [
                    (.4, (-1.0, 0.0, 1.0)),
                    (.5, (0, 1, 1)),
                    (-.4, (-1, -.8, 0)),
                    (-.4, (-1, -1, -.8)),
                ]
            ),
        ],
    )
    def test_rebaseTent(self, tent, axisRange, expected):

        sol = solver.rebaseTent(tent, axisRange)

        assert sol == expected, (tent, axisRange)
