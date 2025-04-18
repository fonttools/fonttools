import fontTools.misc.bezierTools as bezierTools
from fontTools.misc.bezierTools import (
    calcQuadraticBounds,
    calcQuadraticArcLength,
    calcCubicBounds,
    calcCubicArcLength,
    curveLineIntersections,
    curveCurveIntersections,
    segmentPointAtT,
    splitLine,
    splitQuadratic,
    splitCubic,
    splitQuadraticAtT,
    splitCubicAtT,
    solveCubic,
)
import pytest


def test_calcQuadraticBounds():
    assert calcQuadraticBounds((0, 0), (50, 100), (100, 0)) == (0, 0, 100, 50.0)
    assert calcQuadraticBounds((0, 0), (100, 0), (100, 100)) == (0.0, 0.0, 100, 100)


def test_calcCubicBounds():
    assert calcCubicBounds((0, 0), (25, 100), (75, 100), (100, 0)) == (
        (0, 0, 100, 75.0)
    )
    assert calcCubicBounds((0, 0), (50, 0), (100, 50), (100, 100)) == (
        0.0,
        0.0,
        100,
        100,
    )
    assert calcCubicBounds((50, 0), (0, 100), (100, 100), (50, 0)) == pytest.approx(
        (35.566243, 0.000000, 64.433757, 75.000000)
    )


def test_splitLine():
    assert splitLine((0, 0), (100, 100), where=50, isHorizontal=True) == [
        ((0, 0), (50.0, 50.0)),
        ((50.0, 50.0), (100, 100)),
    ]
    assert splitLine((0, 0), (100, 100), where=100, isHorizontal=True) == [
        ((0, 0), (100, 100))
    ]
    assert splitLine((0, 0), (100, 100), where=0, isHorizontal=True) == [
        ((0, 0), (0, 0)),
        ((0, 0), (100, 100)),
    ]
    assert splitLine((0, 0), (100, 100), where=0, isHorizontal=False) == [
        ((0, 0), (0, 0)),
        ((0, 0), (100, 100)),
    ]
    assert splitLine((100, 0), (0, 0), where=50, isHorizontal=False) == [
        ((100, 0), (50, 0)),
        ((50, 0), (0, 0)),
    ]
    assert splitLine((0, 100), (0, 0), where=50, isHorizontal=True) == [
        ((0, 100), (0, 50)),
        ((0, 50), (0, 0)),
    ]
    assert splitLine((0, 100), (100, 100), where=50, isHorizontal=True) == [
        ((0, 100), (100, 100))
    ]


def assert_curves_approx_equal(actual_curves, expected_curves):
    assert len(actual_curves) == len(expected_curves)
    for acurve, ecurve in zip(actual_curves, expected_curves):
        assert len(acurve) == len(ecurve)
        for apt, ept in zip(acurve, ecurve):
            assert apt == pytest.approx(ept)


def test_splitQuadratic():
    assert splitQuadratic(
        (0, 0), (50, 100), (100, 0), where=150, isHorizontal=False
    ) == [((0, 0), (50, 100), (100, 0))]
    assert splitQuadratic(
        (0, 0), (50, 100), (100, 0), where=50, isHorizontal=False
    ) == [((0, 0), (25, 50), (50, 50)), ((50, 50), (75, 50), (100, 0))]
    assert splitQuadratic(
        (0, 0), (50, 100), (100, 0), where=25, isHorizontal=False
    ) == [((0, 0), (12.5, 25), (25, 37.5)), ((25, 37.5), (62.5, 75), (100, 0))]
    assert_curves_approx_equal(
        splitQuadratic((0, 0), (50, 100), (100, 0), where=25, isHorizontal=True),
        [
            ((0, 0), (7.32233, 14.64466), (14.64466, 25)),
            ((14.64466, 25), (50, 75), (85.3553, 25)),
            ((85.3553, 25), (92.6777, 14.64466), (100, -7.10543e-15)),
        ],
    )
    # XXX I'm not at all sure if the following behavior is desirable
    assert splitQuadratic((0, 0), (50, 100), (100, 0), where=50, isHorizontal=True) == [
        ((0, 0), (25, 50), (50, 50)),
        ((50, 50), (50, 50), (50, 50)),
        ((50, 50), (75, 50), (100, 0)),
    ]


def test_splitCubic():
    assert splitCubic(
        (0, 0), (25, 100), (75, 100), (100, 0), where=150, isHorizontal=False
    ) == [((0, 0), (25, 100), (75, 100), (100, 0))]
    assert splitCubic(
        (0, 0), (25, 100), (75, 100), (100, 0), where=50, isHorizontal=False
    ) == [
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
        ((50, 75), (68.75, 75), (87.5, 50), (100, 0)),
    ]
    assert_curves_approx_equal(
        splitCubic((0, 0), (25, 100), (75, 100), (100, 0), where=25, isHorizontal=True),
        [
            ((0, 0), (2.293792, 9.17517), (4.798045, 17.5085), (7.47414, 25)),
            ((7.47414, 25), (31.2886, 91.6667), (68.7114, 91.6667), (92.5259, 25)),
            ((92.5259, 25), (95.202, 17.5085), (97.7062, 9.17517), (100, 1.77636e-15)),
        ],
    )


def test_splitQuadraticAtT():
    assert splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5) == [
        ((0, 0), (25, 50), (50, 50)),
        ((50, 50), (75, 50), (100, 0)),
    ]
    assert splitQuadraticAtT((0, 0), (50, 100), (100, 0), 0.5, 0.75) == [
        ((0, 0), (25, 50), (50, 50)),
        ((50, 50), (62.5, 50), (75, 37.5)),
        ((75, 37.5), (87.5, 25), (100, 0)),
    ]


def test_splitCubicAtT():
    assert splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5) == [
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
        ((50, 75), (68.75, 75), (87.5, 50), (100, 0)),
    ]
    assert splitCubicAtT((0, 0), (25, 100), (75, 100), (100, 0), 0.5, 0.75) == [
        ((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
        ((50, 75), (59.375, 75), (68.75, 68.75), (77.34375, 56.25)),
        ((77.34375, 56.25), (85.9375, 43.75), (93.75, 25), (100, 0)),
    ]


def test_splitCubicAtT_robustness():
    segment = ((-103, -231), (-61, -240), (-31.009, -245), (6, -245))
    (_, tail) = splitCubicAtT(*segment, 0.386637)
    assert tail[-1] == segment[-1]


def test_solveCubic():
    assert solveCubic(1, 1, -6, 0) == [-3.0, -0.0, 2.0]
    assert solveCubic(-10.0, -9.0, 48.0, -29.0) == [-2.9, 1.0, 1.0]
    assert solveCubic(-9.875, -9.0, 47.625, -28.75) == [-2.911392, 1.0, 1.0]
    assert solveCubic(1.0, -4.5, 6.75, -3.375) == [1.5, 1.5, 1.5]
    assert solveCubic(-12.0, 18.0, -9.0, 1.50023651123) == [0.5, 0.5, 0.5]
    assert solveCubic(9.0, 0.0, 0.0, -7.62939453125e-05) == [-0.0, -0.0, -0.0]


_segmentPointAtT_testData = [
    ([(0, 10), (200, 100)], 0.0, (0, 10)),
    ([(0, 10), (200, 100)], 0.5, (100, 55)),
    ([(0, 10), (200, 100)], 1.0, (200, 100)),
    ([(0, 10), (100, 100), (200, 50)], 0.0, (0, 10)),
    ([(0, 10), (100, 100), (200, 50)], 0.5, (100, 65.0)),
    ([(0, 10), (100, 100), (200, 50)], 1.0, (200, 50.0)),
    ([(0, 10), (100, 100), (200, 100), (300, 0)], 0.0, (0, 10)),
    ([(0, 10), (100, 100), (200, 100), (300, 0)], 0.5, (150, 76.25)),
    ([(0, 10), (100, 100), (200, 100), (300, 0)], 1.0, (300, 0)),
]


@pytest.mark.parametrize("segment, t, expectedPoint", _segmentPointAtT_testData)
def test_segmentPointAtT(segment, t, expectedPoint):
    point = segmentPointAtT(segment, t)
    assert expectedPoint == point


def test_intersections_straight_line():
    curve = ((548, 183), (548, 289), (450, 366), (315, 366))
    line1 = ((330, 376), (330, 286))
    pt = curveLineIntersections(curve, line1)[0][0]
    assert pt[0] == 330
    line = (pt, (330, 286))
    pt2 = (330.0001018806911, 295.5635754579425)
    assert bezierTools._line_t_of_pt(*line, pt2) > 0
    s = (19, 0)
    e = (110, 0)
    pt = (109.05194805194802, 0.0)
    assert bezierTools._line_t_of_pt(s, e, pt) == pytest.approx(0.98958184)


def test_calcQuadraticArcLength():
    # https://github.com/fonttools/fonttools/issues/3287
    assert calcQuadraticArcLength(
        (210, 333), (289, 333), (326.5, 290.5)
    ) == pytest.approx(127.9225)


@pytest.mark.parametrize(
    "segment, expectedLength",
    [
        (
            # https://github.com/fonttools/fonttools/issues/3502
            ((377, 469), (377, 468), (377, 472), (377, 472)),  # off by one unit
            3.32098765445,
        ),
        (
            # https://github.com/fonttools/fonttools/issues/3502
            ((242, 402), (242, 403), (242, 399), (242, 399)),  # off by one unit
            3.32098765445,
        ),
        (
            # https://github.com/fonttools/fonttools/issues/3514
            (
                (626.9918761593156, 1000.0),
                (639.133178223544, 1000.0),
                (650.1152019577394, 1000.0),
                (626.9918761593156, 1000.0),
            ),  # infinite recursion with Cython
            27.06159516422008,
        ),
    ],
)
def test_calcCubicArcLength(segment, expectedLength):
    assert calcCubicArcLength(*segment) == pytest.approx(expectedLength)


def test_intersections_linelike():
    seg1 = [(0.0, 0.0), (0.0, 0.25), (0.0, 0.75), (0.0, 1.0)]
    seg2 = [(0.0, 0.5), (0.25, 0.5), (0.75, 0.5), (1.0, 0.5)]
    pt = curveCurveIntersections(seg1, seg2)[0][0]
    assert pt == (0.0, 0.5)
