from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.bezierTools import (
    calcQuadraticBounds, calcCubicBounds, splitLine, splitQuadratic,
    splitCubic, splitQuadraticAtT, splitCubicAtT, solveCubic)
import pytest


def test_calcQuadraticBounds():
    assert calcQuadraticBounds(
        (0, 0), (50, 100), (100, 0)) == (0, 0, 100, 50.0)
    assert calcQuadraticBounds(
        (0, 0), (100, 0), (100, 100)) == (0.0, 0.0, 100, 100)


def test_calcCubicBounds():
    assert calcCubicBounds(
        (0, 0), (25, 100), (75, 100), (100, 0)) == ((0, 0, 100, 75.0))
    assert calcCubicBounds(
        (0, 0), (50, 0), (100, 50), (100, 100)) == (0.0, 0.0, 100, 100)
    assert calcCubicBounds(
        (50, 0), (0, 100), (100, 100), (50, 0)
    ) == pytest.approx((35.566243, 0.000000, 64.433757, 75.000000))


def test_splitLine():
    assert splitLine(
        (0, 0), (100, 100), where=50, isHorizontal=True
    ) == [((0, 0), (50.0, 50.0)), ((50.0, 50.0), (100, 100))]
    assert splitLine(
        (0, 0), (100, 100), where=100, isHorizontal=True
    ) == [((0, 0), (100, 100))]
    assert splitLine(
        (0, 0), (100, 100), where=0, isHorizontal=True
    ) == [((0, 0), (0, 0)), ((0, 0), (100, 100))]
    assert splitLine(
        (0, 0), (100, 100), where=0, isHorizontal=False
    ) == [((0, 0), (0, 0)), ((0, 0), (100, 100))]
    assert splitLine(
        (100, 0), (0, 0), where=50, isHorizontal=False
    ) == [((100, 0), (50, 0)), ((50, 0), (0, 0))]
    assert splitLine(
        (0, 100), (0, 0), where=50, isHorizontal=True
    ) == [((0, 100), (0, 50)), ((0, 50), (0, 0))]
    assert splitLine(
        (0, 100), (100, 100), where=50, isHorizontal=True
    ) == [((0, 100), (100, 100))]


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
    ) == [((0, 0), (25, 50), (50, 50)),
          ((50, 50), (75, 50), (100, 0))]
    assert splitQuadratic(
        (0, 0), (50, 100), (100, 0), where=25, isHorizontal=False
    ) == [((0, 0), (12.5, 25), (25, 37.5)),
          ((25, 37.5), (62.5, 75), (100, 0))]
    assert_curves_approx_equal(
        splitQuadratic(
            (0, 0), (50, 100), (100, 0), where=25, isHorizontal=True),
        [((0, 0), (7.32233, 14.64466), (14.64466, 25)),
         ((14.64466, 25), (50, 75), (85.3553, 25)),
         ((85.3553, 25), (92.6777, 14.64466), (100, -7.10543e-15))])
    # XXX I'm not at all sure if the following behavior is desirable
    assert splitQuadratic(
        (0, 0), (50, 100), (100, 0), where=50, isHorizontal=True
    ) == [((0, 0), (25, 50), (50, 50)),
          ((50, 50), (50, 50), (50, 50)),
          ((50, 50), (75, 50), (100, 0))]


def test_splitCubic():
    assert splitCubic(
        (0, 0), (25, 100), (75, 100), (100, 0), where=150, isHorizontal=False
    ) == [((0, 0), (25, 100), (75, 100), (100, 0))]
    assert splitCubic(
        (0, 0), (25, 100), (75, 100), (100, 0), where=50, isHorizontal=False
    ) == [((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
          ((50, 75), (68.75, 75), (87.5, 50), (100, 0))]
    assert_curves_approx_equal(
        splitCubic(
            (0, 0), (25, 100), (75, 100), (100, 0), where=25,
            isHorizontal=True),
        [((0, 0), (2.293792, 9.17517), (4.798045, 17.5085), (7.47414, 25)),
         ((7.47414, 25), (31.2886, 91.6667), (68.7114, 91.6667),
          (92.5259, 25)),
         ((92.5259, 25), (95.202, 17.5085), (97.7062, 9.17517),
          (100, 1.77636e-15))])


def test_splitQuadraticAtT():
    assert splitQuadraticAtT(
        (0, 0), (50, 100), (100, 0), 0.5
    ) == [((0, 0), (25, 50), (50, 50)),
          ((50, 50), (75, 50), (100, 0))]
    assert splitQuadraticAtT(
        (0, 0), (50, 100), (100, 0), 0.5, 0.75
    ) == [((0, 0), (25, 50), (50, 50)),
          ((50, 50), (62.5, 50), (75, 37.5)),
          ((75, 37.5), (87.5, 25), (100, 0))]


def test_splitCubicAtT():
    assert splitCubicAtT(
        (0, 0), (25, 100), (75, 100), (100, 0), 0.5
    ) == [((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
          ((50, 75), (68.75, 75), (87.5, 50), (100, 0))]
    assert splitCubicAtT(
        (0, 0), (25, 100), (75, 100), (100, 0), 0.5, 0.75
    ) == [((0, 0), (12.5, 50), (31.25, 75), (50, 75)),
          ((50, 75), (59.375, 75), (68.75, 68.75), (77.34375, 56.25)),
          ((77.34375, 56.25), (85.9375, 43.75), (93.75, 25), (100, 0))]


def test_solveCubic():
    assert solveCubic(1, 1, -6, 0) == [-3.0, -0.0, 2.0]
    assert solveCubic(-10.0, -9.0, 48.0, -29.0) == [-2.9, 1.0, 1.0]
    assert solveCubic(-9.875, -9.0, 47.625, -28.75) == [-2.911392, 1.0, 1.0]
    assert solveCubic(1.0, -4.5, 6.75, -3.375) == [1.5, 1.5, 1.5]
    assert solveCubic(-12.0, 18.0, -9.0, 1.50023651123) == [0.5, 0.5, 0.5]
    assert solveCubic(9.0, 0.0, 0.0, -7.62939453125e-05) == [-0.0, -0.0, -0.0]
