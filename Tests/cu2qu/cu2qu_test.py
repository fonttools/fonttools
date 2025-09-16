# Copyright 2016 Google Inc. All Rights Reserved.
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

import collections
import math
import unittest
import os
import json

import pytest
from fontTools.cu2qu import curve_to_quadratic, curves_to_quadratic


DATADIR = os.path.join(os.path.dirname(__file__), "data")

MAX_ERR = 5


class CurveToQuadraticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Do the curve conversion ahead of time, and run tests on results."""
        with open(os.path.join(DATADIR, "curves.json"), "r") as fp:
            curves = json.load(fp)

        cls.single_splines = [curve_to_quadratic(c, MAX_ERR) for c in curves]
        cls.single_errors = [
            cls.curve_spline_dist(c, s) for c, s in zip(curves, cls.single_splines)
        ]

        curve_groups = [curves[i : i + 3] for i in range(0, 300, 3)]
        cls.compat_splines = [
            curves_to_quadratic(c, [MAX_ERR] * 3) for c in curve_groups
        ]
        cls.compat_errors = [
            [cls.curve_spline_dist(c, s) for c, s in zip(curve_group, splines)]
            for curve_group, splines in zip(curve_groups, cls.compat_splines)
        ]

        cls.results = []

    @classmethod
    def tearDownClass(cls):
        """Print stats from conversion, as determined during tests."""

        for tag, results in cls.results:
            print(
                "\n%s\n%s"
                % (
                    tag,
                    "\n".join(
                        "%s: %s (%d)" % (k, "#" * (v // 10 + 1), v)
                        for k, v in sorted(results.items())
                    ),
                )
            )

    def test_results_unchanged(self):
        """Tests that the results of conversion haven't changed since the time
        of this test's writing. Useful as a quick check whenever one modifies
        the conversion algorithm.
        """

        expected = {2: 6, 3: 26, 4: 82, 5: 232, 6: 360, 7: 266, 8: 28}

        results = collections.defaultdict(int)
        for spline in self.single_splines:
            n = len(spline) - 2
            results[n] += 1
        self.assertEqual(results, expected)
        self.results.append(("single spline lengths", results))

    def test_results_unchanged_multiple(self):
        """Test that conversion results are unchanged for multiple curves."""

        expected = {5: 11, 6: 35, 7: 49, 8: 5}

        results = collections.defaultdict(int)
        for splines in self.compat_splines:
            n = len(splines[0]) - 2
            for spline in splines[1:]:
                self.assertEqual(
                    len(spline) - 2, n, "Got incompatible conversion results"
                )
            results[n] += 1
        self.assertEqual(results, expected)
        self.results.append(("compatible spline lengths", results))

    def test_does_not_exceed_tolerance(self):
        """Test that conversion results do not exceed given error tolerance."""

        results = collections.defaultdict(int)
        for error in self.single_errors:
            results[round(error, 1)] += 1
            self.assertLessEqual(error, MAX_ERR)
        self.results.append(("single errors", results))

    def test_does_not_exceed_tolerance_multiple(self):
        """Test that error tolerance isn't exceeded for multiple curves."""

        results = collections.defaultdict(int)
        for errors in self.compat_errors:
            for error in errors:
                results[round(error, 1)] += 1
                self.assertLessEqual(error, MAX_ERR)
        self.results.append(("compatible errors", results))

    @classmethod
    def curve_spline_dist(cls, bezier, spline, total_steps=20):
        """Max distance between a bezier and quadratic spline at sampled points."""

        error = 0
        n = len(spline) - 2
        steps = total_steps // n
        for i in range(0, n - 1):
            p1 = spline[0] if i == 0 else p3
            p2 = spline[i + 1]
            if i < n - 1:
                p3 = cls.lerp(spline[i + 1], spline[i + 2], 0.5)
            else:
                p3 = spline[n + 2]
            segment = p1, p2, p3
            for j in range(steps):
                error = max(
                    error,
                    cls.dist(
                        cls.cubic_bezier_at(bezier, (j / steps + i) / n),
                        cls.quadratic_bezier_at(segment, j / steps),
                    ),
                )
        return error

    @classmethod
    def lerp(cls, p1, p2, t):
        (x1, y1), (x2, y2) = p1, p2
        return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t

    @classmethod
    def dist(cls, p1, p2):
        (x1, y1), (x2, y2) = p1, p2
        return math.hypot(x1 - x2, y1 - y2)

    @classmethod
    def quadratic_bezier_at(cls, b, t):
        (x1, y1), (x2, y2), (x3, y3) = b
        _t = 1 - t
        t2 = t * t
        _t2 = _t * _t
        _2_t_t = 2 * t * _t
        return (_t2 * x1 + _2_t_t * x2 + t2 * x3, _t2 * y1 + _2_t_t * y2 + t2 * y3)

    @classmethod
    def cubic_bezier_at(cls, b, t):
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = b
        _t = 1 - t
        t2 = t * t
        _t2 = _t * _t
        t3 = t * t2
        _t3 = _t * _t2
        _3_t2_t = 3 * t2 * _t
        _3_t_t2 = 3 * t * _t2
        return (
            _t3 * x1 + _3_t_t2 * x2 + _3_t2_t * x3 + t3 * x4,
            _t3 * y1 + _3_t_t2 * y2 + _3_t2_t * y3 + t3 * y4,
        )


class AllQuadraticFalseTest(unittest.TestCase):
    def test_cubic(self):
        cubic = [(0, 0), (0, 1), (2, 1), (2, 0)]
        result = curve_to_quadratic(cubic, 0.1, all_quadratic=False)
        assert result == cubic

    def test_quadratic(self):
        cubic = [(0, 0), (2, 2), (4, 2), (6, 0)]
        result = curve_to_quadratic(cubic, 0.1, all_quadratic=False)
        quadratic = [(0, 0), (3, 3), (6, 0)]
        assert result == quadratic


def test_cu2qu_degenerate_all_points_equal():
    # https://github.com/fonttools/fonttools/pull/3903
    cubic = [(5, 5), (5, 5), (5, 5), (5, 5)]
    result = curve_to_quadratic(cubic, 0.1, all_quadratic=True)
    assert result == [(5, 5), (5, 5), (5, 5)]


def test_cu2qu_degenerate_3_points_equal_single_quad_within_tolerance():
    cubic = [(5, 5), (5, 5), (5, 5), (5, 5.1)]
    result = curve_to_quadratic(cubic, 0.1, all_quadratic=True)
    # a single quadratic approximates this cubic for given tolerance
    assert result == [(5, 5), (5, 5), (5, 5.1)]


def test_cu2qu_degenerate_3_points_equal_exceeding_tolerance():
    cubic = [(5, 5), (5, 5), (5, 5), (5, 5.1)]
    result = curve_to_quadratic(cubic, 0.01, all_quadratic=True)
    # 2 off-curves are required to approximate the same cubic given the smaller tolerance
    assert result == [(5, 5), (5, 5), (5, 5.025), (5, 5.1)]


def test_cu2qu_degenerate_curve_with_collinear_points():
    # this particular curve (from 'brevecomb_gravecomb.case' glyph of BilboPro.glyphs) is
    # actually a straight line: the four control points are collinear, and the two
    # off-curves are overlapping and exactly midway between the two on-curves.
    # When computing the intersection of the cubic bezier's handles (in `calc_intersect`),
    # a ZeroDivisionError may or may not be raised depending on whether cu2qu is running
    # in pure-Python or compiled with Cython (due to insignificant floating-point
    # rounding errors in our vector dot() product), which in turn can produce a different
    # number of off-curves in the appoximated quadratic spline.
    # Below we assert that both implementations produce the same result.
    cubic = [(64.94, 550.998), (65.199, 550.032), (65.199, 550.032), (65.458, 549.066)]
    result = curve_to_quadratic(cubic, 1.0, all_quadratic=True)
    expected = [
        (64.94, 550.998),
        (65.13425, 550.2735),
        (65.26375, 549.7905),
        (65.458, 549.066),
    ]
    assert len(result) == len(expected)
    for i, (p1, p2) in enumerate(zip(result, expected)):
        assert p1 == pytest.approx(p2), f"point {i} does not match"


def test_cu2qu_complex_division_floating_point_precision():
    # This test ensures that cu2qu produces identical results whether compiled with
    # Cython or running in pure Python mode. The specific curves from Ojuju.glyphs
    # ("brackeleft" glyph) below exposed a bug where Cython's complex division by
    # a real number could differ by 1 ULP from Python's implementation due to
    # compiler optimizations (multiply-by-reciprocal in C vs two separate divisions
    # in Python).
    # See: https://github.com/fonttools/fonttools/issues/3928

    curves = [
        [(87, 738), (90, 438), (90, 437), (90, 277)],
        [(64, 738), (63, 586), (64, 442), (64, 277)],
    ]

    result = curves_to_quadratic(curves, max_errors=[1.0] * len(curves))

    # Before the fix, when compiled with Cython, the Y coordinate of point at index 5
    # of the second curve would be 326.5 instead of 326.49999999999994
    assert result[1][5][1] == 326.49999999999994


if __name__ == "__main__":
    unittest.main()
