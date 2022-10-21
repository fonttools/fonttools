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
                    (.5, (0, 1, 1)),
                ]
            ),
            # Case 2:
            pytest.param(
                (0, 1, 1), (-1, 0, .75),
                [
                    (.75, (0, 1, 1)),
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
                    (1, (0, 0.8, 1.99994)),
                ]
            ),

            # Case 4
            pytest.param(
                (0, .25, 1), (-1, 0, .4),
                [
                    (1, (0, 0.625, 1)),
                    (0.8, (0.625, 1, 1)),
                ]
            ),
            pytest.param(
                (.25, .3, 1.05), (0, .2, .4),
                [
                    (1, (.25, .5, 1)),
                    (2.6/3, (.5, 1, 1)),
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
                    (-.2, (0, 1, 1)),
                    (-.6, (-1, -1, 0)),
                ]
            ),

            # Case 3a/1neg
            pytest.param(
                (.0, .5, 2), (.2, .5, 1),
                [
                    (1, None),
                    (-1/3, (0, 1, 1)),
                    (-.6, (-1, -1, 0)),
                ]
            ),

            # Case 3
            pytest.param(
                (0, .5, 1), (.25, .25, .75),
                [
                    (.5, None),
                    (.5, (0, 0.5, 1.5)),
                    (-.5, (0.5, 1.5, 1.5)),
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
                    (-1, (0, .5, 1)),
                    (-1, (.5, 1, 1)),
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
            pytest.param(
                (.5, .5, .5), (.25, .35, .5),
                [
                    (1, (1, 1, 1)),
                ]
            ),
            pytest.param(
                (.5, .5, .55), (.25, .35, .5),
                [
                    (1, (1, 1, 1)),
                ]
            ),
            pytest.param(
                (.5, .5, 1), (.5, .5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                ]
            ),
            pytest.param(
                (.25, .5, 1), (.5, .5, 1),
                [
                    (1, None),
                    (-1, (0, 1, 1)),
                ]
            ),
            pytest.param(
                (0, .2, 1), (0, 0, .5),
                [
                    (1, (0, .4, 1.99994)),
                ]
            ),
            # Dirac delta at new default. Fancy!
            pytest.param(
                (.5, .5, .5), (0, .5, 1),
                [
                    (1, None),
                    (-1, (0, 0.0001220703, 1)),
                    (-1, (0.0001220703, 1, 1)),
                    (-1, (-1, -0.0001220703, 0)),
                    (-1, (-1, -1, -0.0001220703)),
                ]
            ),
        ],
    )
    def test_rebaseTent(self, tent, axisRange, expected):

        sol = solver.rebaseTent(tent, axisRange)

        a = pytest.approx
        expected = [
            (
             a(scalar),
             (a(v[0]),a(v[1]),a(v[2])) if v is not None else None
            )
            for scalar,v in expected
        ]

        assert sol == expected, (tent, axisRange)
