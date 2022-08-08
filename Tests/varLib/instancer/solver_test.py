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
                    (.5, None),
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
            pytest.param(
                (.25, .3, 1.05), (0, .2, .4),
                [
                    (1, (0.24999999999999994, 0.4999999999999999, 1.0)),
                    (0.8666666666666667, (0.4999999999999999, 1.0, 1.0)),
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

            # Case 3a/1neg
            pytest.param(
                (.0, .5, 1), (0, .5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                    (-1, (-1, -1, 0)),
                ]
            ),

            # Case 3a/1neg
            pytest.param(
                (.0, .5, 2), (.2, .5, .8),
                [
                    (1, None),
                    (-0.20000000000000007, (0, 1, 1)),
                    (-.6, (-1, -1, 0)),
                ]
            ),

            # Case 3a/1neg
            pytest.param(
                (.0, .5, 2), (.2, .5, 1),
                [
                    (1, None),
                    (-0.33333333333333337, (0, 1, 1)),
                    (-.6, (-1, -1, 0)),
                ]
            ),

            # Case 1neg
            pytest.param(
                (.0, .5, 1), (0, .25, .5),
                [
                    (.5, None),
                    (.5, (0, 1, 1)),
                    (-.5, (-1, -1, 0)),
                ]
            ),

            # Case 2neg
            pytest.param(
                (.05, .55, 1), (0, .25, .5),
                [
                    (.4, None),
                    (.5, (0, 1, 1)),
                    (-.4, (-1, -.8, 0)),
                    (-.4, (-1, -1, -.8)),
                ]
            ),

            # Case 2neg, other side
            pytest.param(
                (-1, -.55, -.05), (-.5, -.25, 0),
                [
                    (.4, None),
                    (.5, (-1, -1, 0)),
                    (-.4, (0, .8, 1)),
                    (-.4, (.8, 1, 1)),
                ]
            ),

            #
            # Misc corner cases
            #

            pytest.param(
                (.5, .5, .5), (.5, .5, .5),
                [
                    (1, None),
                ]
            ),

            pytest.param(
                (.3, .5, .7), (.1, .5, .9),
                [
                    (1, None),
                    (-1, (0, 0.4999999999999999, 1)),
                    (-1, (0.4999999999999999, 1, 1)),
                    (-1, (-1, -.5, 0)),
                    (-1, (-1, -1, -.5)),
                ]
            ),

            pytest.param(
                (.5, .5, .5), (.25, .25, .5),
                [
                    (1, (1, 1, 1)),
                ]
            ),
        ],
    )
    def test_rebaseTent(self, tent, axisRange, expected):

        sol = solver.rebaseTent(tent, axisRange)

        assert sol == expected, (tent, axisRange)
